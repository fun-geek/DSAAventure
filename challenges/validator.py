"""Static safety checks on submitted code and output comparison."""
import ast

MAX_SOURCE_BYTES = 20_000
ALLOWED_IMPORTS = {"collections", "heapq", "bisect", "math", "itertools", "functools",
                   "typing", "string"}
BANNED_NAMES = {"eval", "exec", "compile", "open", "input", "__import__", "globals", "locals",
                "vars", "getattr", "setattr", "delattr", "breakpoint", "exit", "quit", "help",
                "memoryview", "type", "dir", "id"}
BANNED_ATTRS = {"tb_frame", "tb_next", "f_globals", "f_locals", "f_back", "f_builtins", "gi_frame",
                "gi_code", "cr_frame", "ag_frame", "func_globals", "mro", "format_map"}
ALLOWED_DUNDER_ATTRS = {"__init__"}


def static_check(source: str) -> list[str]:
    """Return a list of human-readable problems (empty list = code may run).

    This is the first layer of defence; the sandbox process adds restricted
    builtins, resource limits and a timeout (see challenges/sandbox.py).
    """
    if len(source.encode("utf-8")) > MAX_SOURCE_BYTES:
        return ["Code is too long (limit 20 KB)."]
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"Syntax error on line {e.lineno}: {e.msg}"]
    problems: list[str] = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", "?")
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS:
                    problems.append(f"Line {line}: import '{a.name}' is not allowed.")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level or root not in ALLOWED_IMPORTS or any(a.name == "*" for a in node.names):
                problems.append(f"Line {line}: this import is not allowed.")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            problems.append(f"Line {line}: '{node.id}' is not allowed.")
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if (attr.startswith("__") and attr not in ALLOWED_DUNDER_ATTRS) or attr in BANNED_ATTRS:
                problems.append(f"Line {line}: attribute '{attr}' is not allowed.")
    return problems[:5]


def _norm(x):
    if isinstance(x, (list, tuple)):
        return [_norm(i) for i in x]
    if isinstance(x, dict):
        return {str(k): _norm(v) for k, v in x.items()}
    return x


def _is_peak(nums, i) -> bool:
    left = nums[i - 1] if i > 0 else float("-inf")
    right = nums[i + 1] if i + 1 < len(nums) else float("-inf")
    return nums[i] > left and nums[i] > right


def compare(question: dict, args: list, expected, got) -> bool:
    """Decide whether `got` is a correct answer for this case."""
    if question.get("compare") == "peak":
        return (isinstance(got, int) and not isinstance(got, bool)
                and 0 <= got < len(args[0]) and _is_peak(args[0], got))
    if question["kind"] == "design":  # None in expected means "return value ignored"
        return (isinstance(got, list) and len(got) == len(expected)
                and all(e is None or _norm(e) == _norm(g) for e, g in zip(expected, got)))
    if isinstance(expected, bool):
        return isinstance(got, bool) and expected == got
    return _norm(expected) == _norm(got)
