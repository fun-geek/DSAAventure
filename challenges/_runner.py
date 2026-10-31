"""Sandbox child process. Started as `python -I _runner.py`; NEVER imported by the game.

Protocol: one JSON request on stdin, one JSON response on stdout.
Layers of defence here: resource limits, restricted builtins, import allow-list,
per-case timer, swallowed stdout. The parent already ran an AST check.
"""
import builtins
import io
import json
import sys

ALLOWED_MODULES = {"collections", "heapq", "bisect", "math", "itertools", "functools",
                   "typing", "string"}
SAFE_BUILTINS = (
    "abs all any bool bin callable chr classmethod dict divmod enumerate filter float "
    "frozenset hash hex int isinstance issubclass iter len list map max min next object oct "
    "ord pow print property range repr reversed round set slice sorted staticmethod str sum "
    "super tuple zip ArithmeticError AssertionError AttributeError Exception IndexError "
    "KeyError LookupError NotImplementedError OverflowError RuntimeError StopIteration "
    "TypeError ValueError ZeroDivisionError").split()


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


class _Timeout(BaseException):
    pass


def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level or name.split(".")[0] not in ALLOWED_MODULES:
        raise ImportError(f"import of '{name}' is not allowed")
    return builtins.__import__(name, globals, locals, fromlist, level)


def apply_limits(cpu_seconds, memory_mb):
    try:
        import resource
    except ImportError:  # Windows: rely on the parent's wall-clock timeout
        return
    for res, val in ((getattr(resource, "RLIMIT_CPU", None), (cpu_seconds, cpu_seconds + 1)),
                     (getattr(resource, "RLIMIT_AS", None), (memory_mb << 20, memory_mb << 20)),
                     (getattr(resource, "RLIMIT_FSIZE", None), (0, 0))):
        if res is not None:
            try:
                resource.setrlimit(res, val)
            except (ValueError, OSError):
                pass


def plain(x):
    if x is None or isinstance(x, (bool, int, float, str)):
        return x
    if isinstance(x, (list, tuple)):
        return [plain(i) for i in x]
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (set, frozenset)):
        return sorted(plain(i) for i in x)
    return f"<{type(x).__name__} object>"


def build_nodes(values):
    nodes = [ListNode(v) for v in values]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    return nodes


def ll_to_list(node):
    out = []
    while node is not None:
        out.append(node.val)
        node = node.next
        if len(out) > 10000:
            raise ValueError("returned list is too long or contains a cycle")
    return out


def graph_from_adj(adj):
    nodes = [Node(i + 1) for i in range(len(adj))]
    for node, nbs in zip(nodes, adj):
        node.neighbors = [nodes[j - 1] for j in nbs]
    return nodes


def graph_to_adj(start, originals):
    if start is None:
        return []
    if not isinstance(start, Node):
        return "function must return a Node (or None)"
    seen, order, stack = {id(start)}, [start], [start]
    while stack:
        for nb in stack.pop().neighbors:
            if id(nb) not in seen:
                seen.add(id(nb))
                order.append(nb)
                stack.append(nb)
    if any(id(n) in originals for n in order):
        return "the copy shares nodes with the original graph"
    adj = [None] * len(order)
    for n in order:
        if not 1 <= n.val <= len(order) or adj[n.val - 1] is not None:
            return "copied node values are wrong"
        adj[n.val - 1] = [m.val for m in n.neighbors]
    return adj


def call_case(ns, spec, args):
    kind, opts = spec["kind"], spec.get("options", {})
    if kind == "design":
        obj = ns[spec["class_name"]](*args[1][0])
        out = [None]
        for op, a in zip(args[0][1:], args[1][1:]):
            out.append(plain(getattr(obj, op)(*a)))
        return out
    fn = ns[spec["function"]]
    if kind == "function":
        res = fn(*args)
        return plain(args[opts["inplace"]] if "inplace" in opts else res)
    if kind == "ll":
        conv = [build_nodes(a)[0] if t == "ll" and a else (None if t == "ll" else a)
                for a, t in zip(args, opts["arg_types"])]
        res = fn(*conv)
        return ll_to_list(res) if opts.get("result") == "ll" else plain(res)
    if kind == "ll_cycle":
        values, pos = args
        nodes = build_nodes(values)
        if pos >= 0:
            nodes[-1].next = nodes[pos]
        return plain(fn(nodes[0] if nodes else None))
    if kind == "ll_intersect":
        a_vals, b_vals, common = args
        shared = build_nodes(common)
        a_nodes, b_nodes = build_nodes(a_vals), build_nodes(b_vals)
        for nodes in (a_nodes, b_nodes):
            if nodes and shared:
                nodes[-1].next = shared[0]
        head_a = (a_nodes or shared or [None])[0]
        head_b = (b_nodes or shared or [None])[0]
        res = fn(head_a, head_b)
        expected = shared[0] if shared else None
        if res is expected:
            return res.val if res is not None else None
        return "returned a node that is not the shared one" if res is not None else "None"
    if kind == "graph_clone":
        nodes = graph_from_adj(args[0])
        res = fn(nodes[0] if nodes else None)
        return graph_to_adj(res, {id(n) for n in nodes})
    raise ValueError(f"unknown kind {kind}")


def describe_error(e):
    line = ""
    tb = e.__traceback__
    while tb is not None:
        if tb.tb_frame.f_code.co_filename == "<solution>":
            line = f" (line {tb.tb_lineno})"
        tb = tb.tb_next
    return f"{type(e).__name__}: {str(e)[:160]}{line}"


def execute(req):
    spec = req["spec"]
    cases = req["cases"]
    safe = {n: getattr(builtins, n) for n in SAFE_BUILTINS}
    safe["__build_class__"] = builtins.__build_class__
    safe["__import__"] = _safe_import
    ns = {"__builtins__": safe, "__name__": "solution", "ListNode": ListNode, "Node": Node}
    try:
        exec(compile(req["source"], "<solution>", "exec"), ns)
        needed = spec.get("class_name") if spec["kind"] == "design" else spec["function"]
        if needed not in ns:
            raise NameError(f"'{needed}' is not defined - keep the name from the starter code")
    except BaseException as e:  # user code failed while being defined
        msg = describe_error(e) if isinstance(e, Exception) else "Program stopped"
        return [{"status": "error", "error": msg}] * len(cases)

    try:
        import signal
        use_timer = hasattr(signal, "setitimer")
    except ImportError:
        use_timer = False
    if use_timer:
        def on_alarm(signum, frame):
            raise _Timeout()
        signal.signal(signal.SIGALRM, on_alarm)

    results, stop = [], False
    for args in cases:
        if stop:
            results.append({"status": "skipped"})
            continue
        try:
            if use_timer:
                signal.setitimer(signal.ITIMER_REAL, req["case_seconds"])
            got = call_case(ns, spec, args)
            results.append({"status": "ok", "got": got})
        except _Timeout:
            results.append({"status": "timeout"})
            stop = True
        except RecursionError:
            results.append({"status": "error", "error": "RecursionError: maximum recursion depth exceeded"})
        except Exception as e:
            results.append({"status": "error", "error": describe_error(e)})
        finally:
            if use_timer:
                signal.setitimer(signal.ITIMER_REAL, 0)
    return results


def main():
    req = json.loads(sys.stdin.read())
    apply_limits(req["cpu_seconds"], req["memory_mb"])
    sys.setrecursionlimit(3000)
    real_stdout, sys.stdout = sys.stdout, io.StringIO()  # swallow user prints
    try:
        results = execute(req)
    finally:
        sys.stdout = real_stdout
    sys.stdout.write(json.dumps({"results": results}))


if __name__ == "__main__":
    main()
