"""Builds challenges/questions.json.

Metadata (difficulty, topics, link, how many companies ask it) comes from the CSV files of
https://github.com/liquidslr/leetcode-company-wise-problems. Statements, examples, hints and
solutions are original. Expected outputs are produced by running the reference solutions
through the same sandbox that grades players.

Usage:  python tools/build_questions.py [path-to-cloned-repo]
"""
import csv
import json
import random
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from challenges.sandbox import SubprocessSandbox  # noqa: E402
from challenges.validator import static_check  # noqa: E402

REPO_URL = "https://github.com/liquidslr/leetcode-company-wise-problems"


# ----------------------------------------------------------------------------- repo metadata
def load_repo_meta(repo: Path) -> dict:
    meta: dict = {}
    companies: dict = defaultdict(set)
    for folder in repo.iterdir():
        csv_path = folder / "5. All.csv"
        if not csv_path.exists():
            continue
        with open(csv_path, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                title = row["Title"].strip()
                companies[title].add(folder.name)
                m = meta.setdefault(title, {"difficulty": row["Difficulty"].lower(),
                                            "link": row["Link"], "max_frequency": 0.0,
                                            "topics": [t.strip() for t in row["Topics"].split(",") if t.strip()]})
                m["max_frequency"] = max(m["max_frequency"], float(row["Frequency"] or 0))
    for title, m in meta.items():
        m["companies"] = len(companies[title])
    return meta


# ----------------------------------------------------------------------------- generators
def sorted_unique(r, lo=1, hi=10, vlo=-20, vhi=40):
    return sorted(r.sample(range(vlo, vhi), r.randint(lo, hi)))


def g_two_sum(r):
    while True:
        n = r.randint(2, 10)
        nums = r.sample(range(-15, 16), n)
        i, j = sorted(r.sample(range(n), 2))
        t = nums[i] + nums[j]
        if sum(1 for a in range(n) for b in range(a + 1, n) if nums[a] + nums[b] == t) == 1:
            return [nums, t]


def g_rotated(r):
    nums = sorted_unique(r)
    k = r.randrange(len(nums))
    nums = nums[k:] + nums[:k]
    return [nums, r.choice(nums) if r.random() < .6 else r.randint(-25, 45)]


def g_first_last(r):
    nums = sorted(r.choices(range(8), k=r.randint(1, 12)))
    return [nums, r.randint(0, 8)]


def g_matrix(r):
    rows, cols = r.randint(1, 4), r.randint(1, 4)
    vals = sorted(r.sample(range(-30, 60), rows * cols))
    m = [vals[i * cols:(i + 1) * cols] for i in range(rows)]
    return [m, r.choice(vals) if r.random() < .5 else r.randint(-35, 65)]


def g_peak(r):
    n = r.randint(1, 10)
    nums = [r.randint(-9, 9)]
    while len(nums) < n:
        v = r.randint(-9, 9)
        if v != nums[-1]:
            nums.append(v)
    return [nums]


def g_ll(r, lo=0, hi=7):
    return [[r.randint(-9, 9) for _ in range(r.randint(lo, hi))]]


def g_merge(r):
    return [sorted(r.randint(-9, 9) for _ in range(r.randint(0, 6))) for _ in range(2)]


def g_remove(r):
    vals = [r.randint(-9, 9) for _ in range(r.randint(1, 8))]
    return [vals, r.randint(1, len(vals))]


def g_cycle(r):
    vals = [r.randint(-9, 9) for _ in range(r.randint(1, 7))]
    return [vals, r.randint(-1, len(vals) - 1)]


def g_intersect(r):
    mk = lambda hi: [r.randint(1, 9) for _ in range(r.randint(0, hi))]
    return [mk(4), mk(4), mk(4)]


def balanced(r, depth=0):
    if depth > 2 or r.random() < .3:
        return ""
    o, c = r.choice(["()", "[]", "{}"])
    return o + balanced(r, depth + 1) + c + balanced(r, depth + 1)


def g_valid(r):
    if r.random() < .5:
        return [balanced(r)]
    return ["".join(r.choice("()[]{}") for _ in range(r.randint(1, 8)))]


def g_min_stack(r):
    ops, args, size = ["MinStack"], [[]], 0
    for _ in range(r.randint(4, 12)):
        choices = ["push"] + (["pop", "top", "getMin"] if size else [])
        op = r.choice(choices)
        ops.append(op)
        if op == "push":
            args.append([r.randint(-5, 5)])
            size += 1
        else:
            args.append([])
            size -= op == "pop"
    return [ops, args]


def g_queue(r):
    ops, args, size = ["MyQueue"], [[]], 0
    for _ in range(r.randint(4, 12)):
        op = r.choice(["push", "empty"] + (["pop", "peek"] if size else []))
        ops.append(op)
        args.append([r.randint(1, 9)] if op == "push" else [])
        size += (op == "push") - (op == "pop")
    return [ops, args]


def g_next_greater(r):
    nums2 = r.sample(range(0, 20), r.randint(1, 8))
    return [r.sample(nums2, r.randint(1, len(nums2))), nums2]


def g_temps(r):
    return [[r.randint(30, 100) for _ in range(r.randint(1, 10))]]


def g_graph(r):
    n = r.randint(1, 8)
    adj = [[] for _ in range(n)]
    for a in range(n):
        for b in range(a + 1, n):
            if r.random() < .3:
                adj[a].append(b)
                adj[b].append(a)
    for nb in adj:
        r.shuffle(nb)
    return [adj, r.randrange(n)]


def g_grid(r, p=.45):
    rows, cols = r.randint(1, 6), r.randint(1, 6)
    return [[[1 if r.random() < p else 0 for _ in range(cols)] for _ in range(rows)]]


def g_clone(r):
    n = r.randint(1, 6)
    adj = [set() for _ in range(n)]
    for i in range(1, n):
        j = r.randrange(i)
        adj[i].add(j + 1)
        adj[j].add(i + 1)
    for _ in range(r.randint(0, 3)):
        a, b = r.randrange(n), r.randrange(n)
        if a != b:
            adj[a].add(b + 1)
            adj[b].add(a + 1)
    return [[sorted(s) for s in adj]]


def g_course(r):
    n = r.randint(1, 6)
    edges = [[r.randrange(n), r.randrange(n)] for _ in range(r.randint(0, 7))]
    return [n, [e for e in edges if e[0] != e[1]]]


def g_coin(r):
    return [r.sample(range(1, 12), r.randint(1, 4)), r.randint(0, 30)]


def g_knap(r):
    n = r.randint(1, 6)
    return [[r.randint(1, 8) for _ in range(n)], [r.randint(1, 20) for _ in range(n)], r.randint(0, 15)]


def g_lcs(r):
    return ["".join(r.choices("abcd", k=r.randint(1, 8))) for _ in range(2)]


# ----------------------------------------------------------------------------- problems
PROBLEMS = []


def add(**kw):
    PROBLEMS.append(kw)


LL = {"arg_types": ["ll"], "result": "ll"}

# ---- World 1: Array Jungle ---------------------------------------------------------------
add(id="array_two_sum", world=1, repo="Two Sum", title="Two Sum", fn="twoSum", sig="def twoSum(nums, target):",
    desc="Given a list of integers `nums` and an integer `target`, find the two different positions whose values add up to `target`. Exactly one such pair exists. Return the two indices in increasing order.",
    cons=["2 <= len(nums) <= 10^4", "Exactly one pair of positions sums to target"],
    complexity="O(n) time, O(n) space", examples=[[[2, 7, 11, 15], 9], [[3, 2, 4], 6]],
    notes=["nums[0] + nums[1] = 2 + 7 = 9"],
    hints=["Brute force checks every pair: O(n^2). Can you remember what you have already seen?", "For each x you need the value target - x. A dictionary can tell you instantly if it was seen.", "Store value -> index as you go, and check the dictionary before inserting."],
    mc=("Which approach solves Two Sum in a single pass?", ["Store each number's index in a hash map and look up target - x", "Sort the list and use two pointers on the sorted copy", "Try every pair with two nested loops", "Binary search for target / 2"], 0, "A dictionary remembers values seen so far, so each lookup of target - x is O(1) and the whole scan is O(n)."),
    sol="""def twoSum(nums, target):
    seen = {}
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
""", blanks=["target - x in seen", "seen[x] = i"], edge=[[[1, 2], 3], [[-3, 4, 3, 90], 0]], gen=g_two_sum)

add(id="array_stock", world=1, repo="Best Time to Buy and Sell Stock", title="Best Time to Buy and Sell Stock", fn="maxProfit", sig="def maxProfit(prices):",
    desc="`prices[i]` is a stock's price on day i. Choose one day to buy and a later day to sell to earn the largest profit. Return that profit, or 0 if every possible trade would lose money.",
    cons=["1 <= len(prices) <= 10^5", "0 <= prices[i] <= 10^4"], complexity="O(n) time, O(1) space",
    examples=[[[7, 1, 5, 3, 6, 4]], [[7, 6, 4, 3, 1]]], notes=["Buy at 1, sell at 6: profit 5", "Prices only fall, so do not trade"],
    hints=["Selling on day i is best when you bought at the cheapest earlier price.", "Track the lowest price seen so far while scanning once."],
    mc=("How do you find the best profit in one pass?", ["Track the lowest price so far and the best (price - lowest)", "Sort the prices and subtract first from last", "Subtract the global minimum from the global maximum", "Compare every pair of days"], 0, "At each day the best sale uses the cheapest earlier price; keeping a running minimum gives O(n)."),
    sol="""def maxProfit(prices):
    best = 0
    lowest = float("inf")
    for p in prices:
        lowest = min(lowest, p)
        best = max(best, p - lowest)
    return best
""", blanks=["lowest = min(lowest, p)", "best = max(best, p - lowest)"], edge=[[[5]], [[1, 2]], [[2, 1, 2, 0, 1]]],
    gen=lambda r: [[r.randint(0, 30) for _ in range(r.randint(1, 12))]])

add(id="array_max_subarray", world=1, repo="Maximum Subarray", title="Maximum Subarray", fn="maxSubArray", sig="def maxSubArray(nums):",
    desc="Find the contiguous, non-empty part of `nums` with the largest sum and return that sum.",
    cons=["1 <= len(nums) <= 10^5", "-10^4 <= nums[i] <= 10^4"], complexity="O(n) time, O(1) space",
    examples=[[[-2, 1, -3, 4, -1, 2, 1, -5, 4]], [[1]]], notes=["The part [4, -1, 2, 1] sums to 6"],
    hints=["A running sum that goes negative only drags later elements down.", "At each element either extend the current sum or start fresh from this element."],
    mc=("At every element, Kadane's algorithm chooses to:", ["Extend the running sum or start fresh here, whichever is larger", "Always restart the sum at zero", "Add only the positive numbers", "Sort the numbers first"], 0, "cur = max(x, cur + x) keeps the best sum of a subarray ending here; the answer is the best cur seen."),
    sol="""def maxSubArray(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best
""", blanks=["cur = max(x, cur + x)", "best = max(best, cur)"], edge=[[[-1]], [[-3, -1, -2]], [[5, -9, 6]]],
    gen=lambda r: [[r.randint(-10, 10) for _ in range(r.randint(1, 12))]])

add(id="array_contains_duplicate", world=1, repo="Contains Duplicate", title="Contains Duplicate", fn="containsDuplicate", sig="def containsDuplicate(nums):",
    desc="Return True if any value appears at least twice in `nums`, otherwise return False.",
    cons=["1 <= len(nums) <= 10^5"], complexity="O(n) time, O(n) space", examples=[[[1, 2, 3, 1]], [[1, 2, 3, 4]]], notes=["1 appears twice"],
    hints=["Comparing every pair is O(n^2).", "A set answers 'have I seen this?' in O(1)."],
    mc=("What is a fast way to detect any duplicate?", ["Insert values into a set and stop when one is already there", "Compare every pair", "Count the zeros", "Reverse the list"], 0, "Set membership is O(1) on average, so one pass is O(n)."),
    sol="""def containsDuplicate(nums):
    seen = set()
    for x in nums:
        if x in seen:
            return True
        seen.add(x)
    return False
""", blanks=["if x in seen:", "seen.add(x)"], edge=[[[1]], [[2, 2]]], gen=lambda r: [[r.randint(0, 12) for _ in range(r.randint(1, 10))]])

add(id="array_move_zeroes", world=1, repo="Move Zeroes", title="Move Zeroes", fn="moveZeroes", sig="def moveZeroes(nums):", options={"inplace": 0},
    desc="Rearrange `nums` in place so every zero moves to the end while the non-zero numbers keep their original order. Modify the list itself; do not build a second list.",
    cons=["1 <= len(nums) <= 10^4"], complexity="O(n) time, O(1) space", examples=[[[0, 1, 0, 3, 12]], [[0]]], notes=["Non-zeros keep their order: 1, 3, 12"],
    hints=["Keep a 'write' position for the next non-zero value.", "After copying all non-zeros forward, fill the rest with zeros."],
    mc=("Which in-place approach works?", ["Keep a write pointer, copy non-zeros forward, then fill the tail with zeros", "Build a new list and return it", "Sort the list descending", "Remove zeros from the front with repeated pop(0)"], 0, "The write pointer packs non-zeros to the front in order, in a single pass."),
    sol="""def moveZeroes(nums):
    write = 0
    for x in nums:
        if x != 0:
            nums[write] = x
            write += 1
    for i in range(write, len(nums)):
        nums[i] = 0
""", blanks=["nums[write] = x", "for i in range(write, len(nums)):"], edge=[[[1]], [[0, 0, 0]], [[4, 5]]],
    gen=lambda r: [[r.choice([0, 0, 1, 2, 3, 5]) for _ in range(r.randint(1, 10))]])

add(id="array_product_except_self", world=1, repo="Product of Array Except Self", title="Product of Array Except Self", fn="productExceptSelf", sig="def productExceptSelf(nums):",
    desc="Return a list `out` where `out[i]` is the product of every element of `nums` except `nums[i]`. Do not use division, and aim for O(n) time.",
    cons=["2 <= len(nums) <= 10^5", "The answer fits in a 32-bit integer"], complexity="O(n) time, O(1) extra space",
    examples=[[[1, 2, 3, 4]], [[-1, 1, 0, -3, 3]]], notes=["out[0] = 2*3*4 = 24"],
    hints=["Division fails when the list contains zero.", "out[i] = (product to the left of i) * (product to the right of i).", "Fill the left products first, then multiply in the right products from the end."],
    mc=("Without division, out[i] equals:", ["Product of everything to its left times product of everything to its right", "Total product minus nums[i]", "Sum of left and right", "Total product divided by nums[i]"], 0, "Two passes - prefix products then suffix products - give every i in O(n)."),
    sol="""def productExceptSelf(nums):
    n = len(nums)
    out = [1] * n
    left = 1
    for i in range(n):
        out[i] = left
        left *= nums[i]
    right = 1
    for i in range(n - 1, -1, -1):
        out[i] *= right
        right *= nums[i]
    return out
""", blanks=["left *= nums[i]", "out[i] *= right"], edge=[[[1, 1]], [[0, 0, 2]]],
    gen=lambda r: [[r.randint(-4, 4) for _ in range(r.randint(2, 8))]])

# ---- World 2: Searching Cave -------------------------------------------------------------
add(id="search_binary_search", world=2, repo="Binary Search", title="Binary Search", fn="search", sig="def search(nums, target):",
    desc="`nums` is sorted in ascending order and contains distinct values. Return the index of `target`, or -1 if it is not present. Aim for O(log n).",
    cons=["1 <= len(nums) <= 10^4", "All values are distinct and sorted"], complexity="O(log n) time, O(1) space",
    examples=[[[-1, 0, 3, 5, 9, 12], 9], [[-1, 0, 3, 5, 9, 12], 2]], notes=["9 is at index 4", "2 is not in the list"],
    hints=["Look at the middle element and throw away the half that cannot contain the target.", "Keep two bounds, lo and hi, and loop while lo <= hi."],
    mc=("Each step of binary search:", ["Checks the middle and discards half the range", "Checks the first element", "Scans left to right", "Doubles the search range"], 0, "Halving the range each step gives O(log n)."),
    sol="""def search(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
""", blanks=["mid = (lo + hi) // 2", "lo = mid + 1"], edge=[[[5], 5], [[5], 4]],
    gen=lambda r: (lambda a: [a, r.choice(a) if r.random() < .6 else r.randint(-25, 45)])(sorted_unique(r)))

add(id="search_rotated", world=2, repo="Search in Rotated Sorted Array", title="Search in Rotated Sorted Array", fn="searchRotated", sig="def searchRotated(nums, target):",
    desc="A sorted list of distinct numbers was rotated at an unknown pivot (for example [0,1,2,4,5,6,7] became [4,5,6,7,0,1,2]). Return the index of `target`, or -1 if it is absent. Aim for O(log n).",
    cons=["1 <= len(nums) <= 5000", "Values are distinct"], complexity="O(log n) time, O(1) space",
    examples=[[[4, 5, 6, 7, 0, 1, 2], 0], [[4, 5, 6, 7, 0, 1, 2], 3]], notes=["0 sits at index 4"],
    hints=["After computing mid, at least one half is still sorted.", "Check whether the target lies inside the sorted half; if so go there, otherwise go to the other half."],
    mc=("In a rotated sorted array, after computing mid:", ["One half is always sorted; check if the target falls inside it", "Rotate the array back first", "The left half is always sorted", "O(log n) is impossible"], 0, "Knowing which half is sorted lets you discard the other half safely."),
    sol="""def searchRotated(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1
""", blanks=["if nums[lo] <= nums[mid]:", "if nums[mid] < target <= nums[hi]:"], edge=[[[1], 1], [[3, 1], 1], [[1, 3], 3]], gen=g_rotated)

add(id="search_first_last", world=2, repo="Find First and Last Position of Element in Sorted Array", title="First and Last Position", fn="searchRange", sig="def searchRange(nums, target):",
    desc="`nums` is sorted in ascending order and may contain duplicates. Return [first, last], the first and last index of `target`, or [-1, -1] if it does not occur. Aim for O(log n).",
    cons=["0 <= len(nums) <= 10^5"], complexity="O(log n) time, O(1) space",
    examples=[[[5, 7, 7, 8, 8, 10], 8], [[5, 7, 7, 8, 8, 10], 6]], notes=["8 occupies indexes 3 to 4"],
    hints=["A 'lower bound' search finds the first index whose value is >= t.", "The last index of target is lower_bound(target + 1) - 1."],
    mc=("To find the last position of target with binary search you can:", ["Find the lower bound of target + 1 and subtract one", "Scan right from the first position (always O(log n))", "Search with a linear loop from the right", "Run the same search twice and compare"], 0, "Two lower-bound searches give both ends in O(log n)."),
    sol="""def searchRange(nums, target):
    def lower(t):
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] < t:
                lo = mid + 1
            else:
                hi = mid
        return lo
    first = lower(target)
    if first == len(nums) or nums[first] != target:
        return [-1, -1]
    return [first, lower(target + 1) - 1]
""", blanks=["if nums[mid] < t:", "lower(target + 1) - 1"], edge=[[[], 0], [[2, 2], 2], [[1], 1]], gen=g_first_last)

add(id="search_matrix", world=2, repo="Search a 2D Matrix", title="Search a 2D Matrix", fn="searchMatrix", sig="def searchMatrix(matrix, target):",
    desc="Each row of `matrix` is sorted left to right, and every row starts with a number larger than the last number of the previous row. Return True if `target` appears in the matrix, otherwise False.",
    cons=["1 <= rows, cols <= 100"], complexity="O(log(rows * cols)) time, O(1) space",
    examples=[[[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3], [[[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13]], notes=["3 is in the first row"],
    hints=["Read the matrix row by row: the values form one long sorted list.", "Index mid maps to row mid // cols and column mid % cols."],
    mc=("Why can binary search treat the matrix as one list?", ["Reading row by row gives one fully sorted sequence", "Columns are unordered so you must scan", "The matrix is always square", "It cannot be done in O(log n)"], 0, "Sorted rows plus ordered row boundaries mean the flattened order is sorted."),
    sol="""def searchMatrix(matrix, target):
    rows, cols = len(matrix), len(matrix[0])
    lo, hi = 0, rows * cols - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        value = matrix[mid // cols][mid % cols]
        if value == target:
            return True
        if value < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False
""", blanks=["matrix[mid // cols][mid % cols]", "lo = mid + 1"], edge=[[[[1]], 1], [[[1]], 2]], gen=g_matrix)

add(id="search_peak", world=2, repo="Find Peak Element", title="Find Peak Element", fn="findPeakElement", sig="def findPeakElement(nums):", compare="peak",
    desc="A peak is an element strictly greater than its neighbours (treat the space outside the list as negative infinity). Neighbouring values are never equal. Return the index of any peak. Aim for O(log n).",
    cons=["1 <= len(nums) <= 1000", "nums[i] != nums[i + 1]"], complexity="O(log n) time, O(1) space",
    examples=[[[1, 2, 3, 1]], [[1, 2, 1, 3, 5, 6, 4]]], notes=["Index 2 (value 3) is a peak - any valid peak is accepted", "Indexes 1 and 5 are both valid"],
    hints=["Compare nums[mid] with nums[mid + 1].", "If the sequence is still rising, a peak must exist to the right."],
    mc=("If nums[mid] < nums[mid + 1] in the peak search, then:", ["A peak must exist to the right of mid", "A peak must exist to the left of mid", "There is no peak", "mid is a peak"], 0, "Rising means the climb has to end somewhere on the right - possibly at the last element."),
    sol="""def findPeakElement(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < nums[mid + 1]:
            lo = mid + 1
        else:
            hi = mid
    return lo
""", blanks=["if nums[mid] < nums[mid + 1]:", "lo = mid + 1"], edge=[[[1]], [[2, 1]], [[1, 2]]], gen=g_peak)

# ---- World 3: Linked List Village --------------------------------------------------------
add(id="ll_reverse", world=3, repo="Reverse Linked List", title="Reverse Linked List", fn="reverseList", sig="def reverseList(head):", kind="ll", options=LL, arg_names=["head"],
    desc="Reverse a singly linked list and return the new head. Each node has `.val` and `.next` (the `ListNode` class is provided).",
    cons=["0 <= number of nodes <= 5000"], complexity="O(n) time, O(1) space", examples=[[[1, 2, 3, 4, 5]], [[1, 2]]], notes=["Show nodes as a list of values"],
    hints=["Walk the list once, flipping each node's next pointer.", "Save `head.next` before you overwrite it."],
    mc=("Reversing a list in place needs which pointers?", ["previous, current and a saved next", "Only head", "Two heads and a stack of values", "A full copy of every node"], 0, "Saving next first lets you flip the link without losing the rest of the list."),
    sol="""def reverseList(head):
    prev = None
    while head:
        nxt = head.next
        head.next = prev
        prev = head
        head = nxt
    return prev
""", blanks=["nxt = head.next", "head.next = prev"], edge=[[[]], [[7]]], gen=g_ll)

add(id="ll_cycle", world=3, repo="Linked List Cycle", title="Linked List Cycle", fn="hasCycle", sig="def hasCycle(head):", kind="ll_cycle", arg_names=["values", "pos"],
    desc="Return True if following `.next` pointers from `head` eventually loops back to an earlier node. Tests describe the list as `values` plus `pos`, the index the tail connects back to (-1 means no cycle); your function only receives `head`.",
    cons=["1 <= number of nodes <= 10^4"], complexity="O(n) time, O(1) space", examples=[[[3, 2, 0, -4], 1], [[1, 2], -1]], notes=["The tail links back to the node at index 1"],
    hints=["A set of visited nodes works, but uses O(n) memory.", "Move one pointer 1 step and another 2 steps; they meet inside a cycle."],
    mc=("Floyd's cycle detection uses:", ["A slow pointer (1 step) and a fast pointer (2 steps) that meet if there is a cycle", "Two pointers moving at the same speed", "A sorted copy of the list", "A counter of nodes"], 0, "The fast pointer laps the slow one inside a cycle, so they must meet."),
    sol="""def hasCycle(head):
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
        if slow is fast:
            return True
    return False
""", blanks=["fast = fast.next.next", "if slow is fast:"], edge=[[[1], -1], [[1], 0]], gen=g_cycle)

add(id="ll_merge_sorted", world=3, repo="Merge Two Sorted Lists", title="Merge Two Sorted Lists", fn="mergeTwoLists", sig="def mergeTwoLists(l1, l2):", kind="ll",
    options={"arg_types": ["ll", "ll"], "result": "ll"}, arg_names=["l1", "l2"],
    desc="Merge two sorted linked lists into one sorted list by splicing their nodes together. Return the head of the merged list.",
    cons=["0 <= nodes in each list <= 50"], complexity="O(n + m) time, O(1) space", examples=[[[1, 2, 4], [1, 3, 4]], [[], [0]]], notes=["Nodes from both lists interleave"],
    hints=["A dummy head node removes special cases.", "Repeatedly attach the smaller front node, then attach whatever is left."],
    mc=("At each step of merging, you:", ["Attach the smaller head node and advance that list", "Sort all values with sorted()", "Append list2 after list1", "Reverse both lists"], 0, "Comparing the two fronts keeps the output sorted in one pass."),
    sol="""def mergeTwoLists(l1, l2):
    dummy = tail = ListNode()
    while l1 and l2:
        if l1.val <= l2.val:
            tail.next = l1
            l1 = l1.next
        else:
            tail.next = l2
            l2 = l2.next
        tail = tail.next
    tail.next = l1 or l2
    return dummy.next
""", blanks=["if l1.val <= l2.val:", "tail.next = l1 or l2"], edge=[[[], []], [[5], []]], gen=g_merge)

add(id="ll_remove_nth", world=3, repo="Remove Nth Node From End of List", title="Remove Nth Node From End", fn="removeNthFromEnd", sig="def removeNthFromEnd(head, n):", kind="ll",
    options={"arg_types": ["ll", "val"], "result": "ll"}, arg_names=["head", "n"],
    desc="Remove the n-th node counted from the END of the list and return the head. Try to do it in a single pass.",
    cons=["1 <= number of nodes <= 30", "1 <= n <= number of nodes"], complexity="O(n) time, O(1) space", examples=[[[1, 2, 3, 4, 5], 2], [[1], 1]], notes=["Node 4 is second from the end"],
    hints=["Let a 'lead' pointer get n steps ahead.", "Move both pointers until the lead reaches the last node; the follower is just before the target."],
    mc=("The one-pass trick for 'n-th from the end':", ["Advance a lead pointer n steps, then move both until the lead reaches the end", "Measure the length in a separate pass only", "Reverse the list twice", "Use recursion only"], 0, "The gap between two pointers equals n, so the follower lands right before the node to delete."),
    sol="""def removeNthFromEnd(head, n):
    dummy = ListNode(0, head)
    lead = lag = dummy
    for _ in range(n):
        lead = lead.next
    while lead.next:
        lead = lead.next
        lag = lag.next
    lag.next = lag.next.next
    return dummy.next
""", blanks=["while lead.next:", "lag.next = lag.next.next"], edge=[[[1, 2], 2], [[1, 2], 1]], gen=g_remove)

add(id="ll_intersection", world=3, repo="Intersection of Two Linked Lists", title="Intersection of Two Linked Lists", fn="getIntersectionNode", sig="def getIntersectionNode(headA, headB):", kind="ll_intersect", arg_names=["listA", "listB", "shared"],
    desc="Two linked lists may end in the very same nodes (the same objects, not just equal values). Return the first shared node, or None if they never meet. Tests give each list's own nodes plus the shared tail.",
    cons=["Lists are short (0-8 nodes)", "Do not change the lists"], complexity="O(n + m) time, O(1) space", examples=[[[4, 1], [5, 6, 1], [8, 4, 5]], [[2, 6, 4], [1, 5], []]], notes=["Both lists end with the same nodes 8 -> 4 -> 5", "No shared tail"],
    hints=["The lists have different lengths before the shared part.", "Walk pointer a through A then B, and pointer b through B then A - they travel equal distances."],
    mc=("Why does the 'switch lists at the end' trick work?", ["Both pointers travel lenA + lenB nodes, so they meet at the shared node (or both reach None)", "The values are equal", "The lists are sorted", "One list is secretly reversed"], 0, "Equal total distance cancels out the difference in the unshared lengths."),
    sol="""def getIntersectionNode(headA, headB):
    a, b = headA, headB
    while a is not b:
        a = a.next if a else headB
        b = b.next if b else headA
    return a
""", blanks=["while a is not b:", "a = a.next if a else headB"], edge=[[[], [], []], [[1], [1], []], [[], [], [3]]], gen=g_intersect)

# ---- World 4: Stack & Queue Mountain -----------------------------------------------------
add(id="stack_valid_parentheses", world=4, repo="Valid Parentheses", title="Valid Parentheses", fn="isValid", sig="def isValid(s):",
    desc="`s` contains only the characters ()[]{}. Return True if every opening bracket is closed by the same type of bracket in the correct order.",
    cons=["0 <= len(s) <= 10^4"], complexity="O(n) time, O(n) space", examples=[["()[]{}"], ["(]"]], notes=["Every bracket closes properly", "']' does not match '('"],
    hints=["The most recent unmatched opener must be closed first.", "Push openers; for a closer, pop and compare."],
    mc=("Which structure checks bracket order?", ["A stack of opening brackets", "A queue", "A set", "A counter per bracket type only"], 0, "Last opened, first closed - exactly a stack."),
    sol="""def isValid(s):
    pairs = {")": "(", "]": "[", "}": "{"}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack
""", blanks=["if not stack or stack.pop() != pairs[ch]:", "return not stack"], edge=[[""], ["("], [")"], ["([)]"]], gen=g_valid)

add(id="stack_min_stack", world=4, repo="Min Stack", title="Min Stack", fn="MinStack", sig="class MinStack:", kind="design", class_name="MinStack", arg_names=["operations", "arguments"],
    starter="""class MinStack:
    def __init__(self):
        pass

    def push(self, val):
        pass

    def pop(self):
        pass

    def top(self):
        pass

    def getMin(self):
        pass
""",
    desc="Design a stack that supports push, pop, top and getMin (the smallest element currently stored), all in O(1) time. The tests call your methods in order; the list shows what each call returns (null means it returns nothing useful).",
    cons=["pop, top and getMin are only called on a non-empty stack"], complexity="O(1) per operation",
    examples=[[["MinStack", "push", "push", "push", "getMin", "pop", "top", "getMin"], [[], [-2], [0], [-3], [], [], [], []]], [["MinStack", "push", "push", "getMin", "push", "getMin"], [[], [4], [2], [], [2], []]]], notes=["After popping -3 the minimum is -2 again"],
    hints=["Scanning the stack for the minimum is O(n).", "Remember the minimum at every depth, e.g. with a second stack that moves together with the first."],
    mc=("How can getMin be O(1)?", ["Keep a second stack that stores the minimum at each depth", "Re-sort the stack on every push", "Keep one variable that is never updated", "Scan the stack when asked"], 0, "Each push records the min so far; pop removes both entries so the previous min returns."),
    sol="""class MinStack:
    def __init__(self):
        self.stack = []
        self.mins = []

    def push(self, val):
        self.stack.append(val)
        self.mins.append(val if not self.mins else min(val, self.mins[-1]))

    def pop(self):
        self.stack.pop()
        self.mins.pop()

    def top(self):
        return self.stack[-1]

    def getMin(self):
        return self.mins[-1]
""", blanks=["val if not self.mins else min(val, self.mins[-1])", "return self.mins[-1]"], edge=[], gen=g_min_stack)

add(id="stack_next_greater", world=4, repo="Next Greater Element I", title="Next Greater Element", fn="nextGreaterElement", sig="def nextGreaterElement(nums1, nums2):",
    desc="`nums1` is a subset of `nums2` and all values are distinct. For each x in `nums1`, find x inside `nums2` and return the first larger value to its right, or -1 if there is none.",
    cons=["1 <= len(nums1) <= len(nums2) <= 1000"], complexity="O(n + m) time, O(m) space", examples=[[[4, 1, 2], [1, 3, 4, 2]], [[2, 4], [1, 2, 3, 4]]], notes=["4 has nothing greater to its right"],
    hints=["Scanning right for every element is O(n^2).", "Keep a stack of values still waiting for a bigger one; pop them when a larger value arrives."],
    mc=("This problem is solved with:", ["A monotonic stack of values waiting for a greater element", "A max-heap of everything", "Sorting nums2", "Binary search in nums1"], 0, "A new larger value resolves every smaller waiting value on the stack."),
    sol="""def nextGreaterElement(nums1, nums2):
    nxt = {}
    stack = []
    for x in nums2:
        while stack and stack[-1] < x:
            nxt[stack.pop()] = x
        stack.append(x)
    return [nxt.get(x, -1) for x in nums1]
""", blanks=["while stack and stack[-1] < x:", "nxt[stack.pop()] = x"], edge=[[[1], [1]]], gen=g_next_greater)

add(id="stack_daily_temperatures", world=4, repo="Daily Temperatures", title="Daily Temperatures", fn="dailyTemperatures", sig="def dailyTemperatures(temperatures):",
    desc="`temperatures[i]` is day i's temperature. For each day return how many days you must wait for a warmer one, or 0 if none will come.",
    cons=["1 <= len(temperatures) <= 10^5"], complexity="O(n) time, O(n) space", examples=[[[73, 74, 75, 71, 69, 72, 76, 73]], [[30, 40, 50, 60]]], notes=["Day 0 waits 1 day for 74"],
    hints=["Store indexes of days still waiting for a warmer day.", "When today is warmer than the day on top of the stack, pop it and record the gap."],
    mc=("In the stack solution you push:", ["Indexes of days still waiting for a warmer day", "Temperatures sorted", "Only the hottest day", "The number of days waited"], 0, "Indexes let you compute the distance when a warmer day finally arrives."),
    sol="""def dailyTemperatures(temperatures):
    out = [0] * len(temperatures)
    stack = []
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            out[j] = i - j
        stack.append(i)
    return out
""", blanks=["while stack and temperatures[stack[-1]] < t:", "out[j] = i - j"], edge=[[[50]], [[60, 50, 40]]], gen=g_temps)

add(id="stack_queue_using_stacks", world=4, repo="Implement Queue using Stacks", title="Implement Queue Using Stacks", fn="MyQueue", sig="class MyQueue:", kind="design", class_name="MyQueue", arg_names=["operations", "arguments"],
    starter="""class MyQueue:
    def __init__(self):
        pass

    def push(self, x):
        pass

    def pop(self):
        pass

    def peek(self):
        pass

    def empty(self):
        pass
""",
    desc="Build a first-in-first-out queue using only two stacks (Python lists used with append and pop at the end). Support push(x), pop() which removes and returns the front, peek() which returns the front, and empty().",
    cons=["pop and peek are only called on a non-empty queue"], complexity="Amortised O(1) per operation",
    examples=[[["MyQueue", "push", "push", "peek", "pop", "empty"], [[], [1], [2], [], [], []]], [["MyQueue", "empty", "push", "pop", "empty"], [[], [], [5], [], []]]], notes=["The first pushed value comes out first"],
    hints=["One stack receives new items; moving them to a second stack reverses their order.", "Only refill the second stack when it is empty."],
    mc=("Moving items from the inbox stack to the outbox stack:", ["Reverses their order, producing FIFO behaviour", "Keeps LIFO order", "Sorts them", "Duplicates them"], 0, "Reversal turns the newest-on-top order into oldest-on-top."),
    sol="""class MyQueue:
    def __init__(self):
        self.inbox = []
        self.outbox = []

    def push(self, x):
        self.inbox.append(x)

    def _shift(self):
        if not self.outbox:
            while self.inbox:
                self.outbox.append(self.inbox.pop())

    def pop(self):
        self._shift()
        return self.outbox.pop()

    def peek(self):
        self._shift()
        return self.outbox[-1]

    def empty(self):
        return not self.inbox and not self.outbox
""", blanks=["self.outbox.append(self.inbox.pop())", "return not self.inbox and not self.outbox"], edge=[], gen=g_queue)

# ---- World 5: Graph Dungeon --------------------------------------------------------------
add(id="graph_bfs", world=5, repo=None, title="BFS Traversal", fn="bfsTraversal", sig="def bfsTraversal(graph, start):", difficulty="easy", topics=["Graph", "Breadth-First Search"],
    desc="`graph[i]` lists the neighbours of node i (nodes are numbered 0 to n-1). Return the nodes in the order a breadth-first search visits them from `start`, taking neighbours in the listed order and never visiting a node twice.",
    cons=["1 <= n <= 1000"], complexity="O(V + E) time, O(V) space", examples=[[[[1, 2], [3], [3], []], 0], [[[1], [0, 2], [1], []], 1]], notes=["Level by level: 0, then 1 and 2, then 3"],
    hints=["Use a queue and a visited set.", "Mark a node visited when you enqueue it so it is never queued twice."],
    mc=("Breadth-first search is driven by:", ["A queue", "A stack", "Recursion only", "A heap"], 0, "FIFO order processes nodes level by level."),
    sol="""from collections import deque


def bfsTraversal(graph, start):
    order = []
    seen = {start}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        order.append(node)
        for nb in graph[node]:
            if nb not in seen:
                seen.add(nb)
                queue.append(nb)
    return order
""", blanks=["node = queue.popleft()", "if nb not in seen:"], edge=[[[[]], 0]], gen=g_graph)

add(id="graph_dfs", world=5, repo=None, title="DFS Traversal", fn="dfsTraversal", sig="def dfsTraversal(graph, start):", difficulty="easy", topics=["Graph", "Depth-First Search"],
    desc="Same graph format as BFS. Return the order in which a recursive depth-first search visits the nodes from `start`, exploring neighbours in the listed order (go as deep as possible before backtracking).",
    cons=["1 <= n <= 1000"], complexity="O(V + E) time, O(V) space", examples=[[[[1, 2], [3], [3], []], 0], [[[2, 1], [0], [0]], 0]], notes=["Goes 0 -> 1 -> 3 before trying 2"],
    hints=["Recursion naturally goes deep first.", "If you use your own stack, push neighbours in reverse so the first neighbour is explored first."],
    mc=("Depth-first search naturally uses:", ["Recursion (the call stack)", "A queue", "A heap", "A sorted list"], 0, "The call stack remembers where to backtrack to."),
    sol="""def dfsTraversal(graph, start):
    order = []
    seen = set()

    def visit(node):
        seen.add(node)
        order.append(node)
        for nb in graph[node]:
            if nb not in seen:
                visit(nb)

    visit(start)
    return order
""", blanks=["seen.add(node)", "visit(nb)"], edge=[[[[]], 0]], gen=g_graph)

add(id="graph_islands", world=5, repo="Number of Islands", title="Number of Islands", fn="numIslands", sig="def numIslands(grid):",
    desc="`grid` is a 2D list of 0 (water) and 1 (land). Count the islands: groups of land cells connected up, down, left or right.",
    cons=["1 <= rows, cols <= 300"], complexity="O(rows * cols) time and space", examples=[[[[1, 1, 0, 0], [1, 0, 0, 1], [0, 0, 1, 1]]], [[[1, 0, 1], [0, 1, 0], [1, 0, 1]]]], notes=["Two islands"],
    hints=["Scan every cell; when you meet unvisited land, you found a new island.", "Flood-fill (DFS or BFS) to mark all connected land as visited."],
    mc=("When you find unvisited land you should:", ["Count one island and flood-fill all connected land", "Count every land cell", "Return immediately", "Sort the grid"], 0, "Flood-fill ensures each island is counted exactly once."),
    sol="""def numIslands(grid):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1 and (r, c) not in seen:
                count += 1
                stack = [(r, c)]
                seen.add((r, c))
                while stack:
                    x, y = stack.pop()
                    for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if 0 <= nx < rows and 0 <= ny < cols and grid[nx][ny] == 1 and (nx, ny) not in seen:
                            seen.add((nx, ny))
                            stack.append((nx, ny))
    return count
""", blanks=["count += 1", "0 <= nx < rows and 0 <= ny < cols"], edge=[[[[0]]], [[[1]]]], gen=g_grid)

add(id="graph_clone", world=5, repo="Clone Graph", title="Clone Graph", fn="cloneGraph", sig="def cloneGraph(node):", kind="graph_clone", arg_names=["adjacencyList"],
    desc="Given a node of a connected undirected graph (each `Node` has `.val` and `.neighbors`; the class is provided), return a deep copy of the whole graph. Tests describe the graph as an adjacency list where entry i lists the neighbours of node i + 1. Returning any original node fails.",
    cons=["0 <= number of nodes <= 100", "Node values are 1..n"], complexity="O(V + E) time and space", examples=[[[[2, 4], [1, 3], [2, 4], [1, 3]]], [[[]]]], notes=["A square of four nodes"],
    hints=["Graphs can contain cycles, so remember which nodes you already copied.", "A dictionary from original node to its copy does both jobs."],
    mc=("To clone a graph with cycles you need:", ["A map from original node to its copy", "Nothing special", "A sorted list of values", "To reuse the original nodes"], 0, "The map prevents infinite loops and lets neighbours point to the same copy."),
    sol="""def cloneGraph(node):
    if node is None:
        return None
    copies = {node: Node(node.val)}
    stack = [node]
    while stack:
        cur = stack.pop()
        for nb in cur.neighbors:
            if nb not in copies:
                copies[nb] = Node(nb.val)
                stack.append(nb)
            copies[cur].neighbors.append(copies[nb])
    return copies[node]
""", blanks=["copies[nb] = Node(nb.val)", "copies[cur].neighbors.append(copies[nb])"], edge=[[[]]], gen=g_clone)

add(id="graph_course_schedule", world=5, repo="Course Schedule", title="Course Schedule", fn="canFinish", sig="def canFinish(numCourses, prerequisites):",
    desc="There are `numCourses` courses numbered 0 to n-1. Each pair [a, b] in `prerequisites` means you must take course b before course a. Return True if it is possible to finish every course.",
    cons=["1 <= numCourses <= 2000"], complexity="O(V + E) time and space", examples=[[2, [[1, 0]]], [2, [[1, 0], [0, 1]]]], notes=["Two courses depend on each other: impossible"],
    hints=["This is asking whether the dependency graph has a cycle.", "Repeatedly take courses with no remaining prerequisites (topological sort)."],
    mc=("Course Schedule asks whether the prerequisite graph:", ["Has no cycle", "Has exactly one cycle", "Is a tree", "Has equal in- and out-degree"], 0, "A valid order exists exactly when the directed graph is acyclic."),
    sol="""def canFinish(numCourses, prerequisites):
    graph = [[] for _ in range(numCourses)]
    indeg = [0] * numCourses
    for a, b in prerequisites:
        graph[b].append(a)
        indeg[a] += 1
    ready = [i for i in range(numCourses) if indeg[i] == 0]
    taken = 0
    while ready:
        c = ready.pop()
        taken += 1
        for nxt in graph[c]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                ready.append(nxt)
    return taken == numCourses
""", blanks=["indeg[nxt] -= 1", "return taken == numCourses"], edge=[[1, []], [3, [[1, 0], [2, 1]]]], gen=g_course)

add(id="graph_shortest_path", world=5, repo="Shortest Path in Binary Matrix", title="Shortest Path in a Grid", fn="shortestPath", sig="def shortestPath(grid):",
    desc="`grid` has 0 for open cells and 1 for walls. Starting at the top-left cell and moving up, down, left or right through open cells, return the fewest steps needed to reach the bottom-right cell, or -1 if that is impossible. A 1x1 open grid needs 0 steps; if the start or end is a wall the answer is -1.",
    cons=["1 <= rows, cols <= 100"], complexity="O(rows * cols) time and space", examples=[[[[0, 0, 0], [1, 1, 0], [0, 0, 0]]], [[[0, 1], [1, 0]]]], notes=["Right, right, down, down = 4 steps"],
    hints=["Every step costs the same, so breadth-first search finds the shortest path.", "Store the distance with each queued cell."],
    mc=("The shortest path in an unweighted grid is found with:", ["BFS from the start cell", "DFS", "Sorting the rows", "Binary search"], 0, "BFS reaches cells in order of distance."),
    sol="""from collections import deque


def shortestPath(grid):
    rows, cols = len(grid), len(grid[0])
    if grid[0][0] == 1 or grid[rows - 1][cols - 1] == 1:
        return -1
    queue = deque([(0, 0, 0)])
    seen = {(0, 0)}
    while queue:
        r, c, d = queue.popleft()
        if (r, c) == (rows - 1, cols - 1):
            return d
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0 and (nr, nc) not in seen:
                seen.add((nr, nc))
                queue.append((nr, nc, d + 1))
    return -1
""", blanks=["return d", "queue.append((nr, nc, d + 1))"], edge=[[[[0]]], [[[1]]], [[[0, 0], [0, 0]]]], gen=lambda r: g_grid(r, .25))

# ---- World 6: Dynamic Programming Kingdom ------------------------------------------------
add(id="dp_climbing_stairs", world=6, repo="Climbing Stairs", title="Climbing Stairs", fn="climbStairs", sig="def climbStairs(n):",
    desc="You climb a staircase of n steps, taking 1 or 2 steps at a time. Return how many distinct ways there are to reach the top.",
    cons=["1 <= n <= 45"], complexity="O(n) time, O(1) space", examples=[[2], [[3]][0]], notes=["1+1 or 2", "1+1+1, 1+2 or 2+1"],
    hints=["To stand on step n you came from step n-1 or n-2.", "ways(n) = ways(n-1) + ways(n-2) - you only need the last two values."],
    mc=("The number of ways to reach step n equals:", ["ways(n-1) + ways(n-2)", "ways(n-1) * 2", "n * n", "ways(n-1) - 1"], 0, "The last move was either 1 step or 2 steps: a Fibonacci recurrence."),
    sol="""def climbStairs(n):
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return b
""", blanks=["a, b = 1, 1", "a, b = b, a + b"], edge=[[1], [30], [45]], gen=lambda r: [r.randint(1, 40)])

add(id="dp_house_robber", world=6, repo="House Robber", title="House Robber", fn="rob", sig="def rob(nums):",
    desc="`nums[i]` is the money in house i along a street. You cannot rob two adjacent houses. Return the largest total you can collect.",
    cons=["0 <= len(nums) <= 100"], complexity="O(n) time, O(1) space", examples=[[[1, 2, 3, 1]], [[2, 7, 9, 3, 1]]], notes=["Rob houses 0 and 2: 1 + 3 = 4"],
    hints=["At each house you either rob it (plus best from two houses back) or skip it.", "Keep two running values: best if you take this house, best if you skip it."],
    mc=("At each house the best total is:", ["The better of robbing it (plus the best two houses back) or skipping it", "Always rob it", "The sum of all houses", "Only alternate houses"], 0, "A one-step recurrence over the previous two states."),
    sol="""def rob(nums):
    take, skip = 0, 0
    for x in nums:
        take, skip = skip + x, max(take, skip)
    return max(take, skip)
""", blanks=["take, skip = skip + x, max(take, skip)", "return max(take, skip)"], edge=[[[]], [[5]], [[2, 1, 1, 2]]], gen=lambda r: [[r.randint(0, 20) for _ in range(r.randint(0, 10))]])

add(id="dp_coin_change", world=6, repo="Coin Change", title="Coin Change", fn="coinChange", sig="def coinChange(coins, amount):",
    desc="Given coin denominations (unlimited supply of each) and a target `amount`, return the fewest coins that add up to the amount, or -1 if it cannot be made. An amount of 0 needs 0 coins.",
    cons=["1 <= len(coins) <= 12", "0 <= amount <= 10^4"], complexity="O(amount * len(coins)) time, O(amount) space", examples=[[[1, 2, 5], 11], [[2], 3]], notes=["11 = 5 + 5 + 1", "Only even totals are possible"],
    hints=["Greedy fails for sets like [1, 3, 4] and amount 6.", "dp[a] = 1 + min(dp[a - coin]) over coins that fit."],
    mc=("Why does 'always take the largest coin' fail?", ["Some coin sets need smaller coins first (e.g. [1,3,4] for 6), so use DP", "It is always correct", "Unlimited coins break it", "Coin order does not matter"], 0, "Greedy picks 4+1+1 (3 coins) instead of 3+3 (2 coins)."),
    sol="""def coinChange(coins, amount):
    INF = amount + 1
    dp = [0] + [INF] * amount
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a:
                dp[a] = min(dp[a], dp[a - c] + 1)
    return dp[amount] if dp[amount] < INF else -1
""", blanks=["dp[a] = min(dp[a], dp[a - c] + 1)", "return dp[amount] if dp[amount] < INF else -1"], edge=[[[1], 0], [[5, 3], 7], [[1, 3, 4], 6]], gen=g_coin)

add(id="dp_lis", world=6, repo="Longest Increasing Subsequence", title="Longest Increasing Subsequence", fn="lengthOfLIS", sig="def lengthOfLIS(nums):",
    desc="Return the length of the longest strictly increasing subsequence of `nums`. Elements keep their original order but do not need to be adjacent.",
    cons=["1 <= len(nums) <= 2500"], complexity="O(n^2) time (O(n log n) possible)", examples=[[[10, 9, 2, 5, 3, 7, 101, 18]], [[7, 7, 7, 7]]], notes=["One answer is 2, 3, 7, 101"],
    hints=["Let dp[i] be the best length ending exactly at index i.", "dp[i] = 1 + max(dp[j]) for earlier j with nums[j] < nums[i]."],
    mc=("In the O(n^2) solution, dp[i] means:", ["Length of the longest increasing subsequence ending at index i", "Longest one anywhere", "Count of elements", "Sum of the subsequence"], 0, "The answer is the maximum dp value over all i."),
    sol="""def lengthOfLIS(nums):
    dp = [1] * len(nums)
    for i in range(len(nums)):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp)
""", blanks=["if nums[j] < nums[i]:", "dp[i] = max(dp[i], dp[j] + 1)"], edge=[[[5]], [[1, 2, 3, 4]], [[4, 3, 2, 1]]], gen=lambda r: [[r.randint(-5, 15) for _ in range(r.randint(1, 12))]])

add(id="dp_lcs", world=6, repo="Longest Common Subsequence", title="Longest Common Subsequence", fn="longestCommonSubsequence", sig="def longestCommonSubsequence(text1, text2):",
    desc="Return the length of the longest subsequence that appears in both strings in the same order (the characters do not need to be next to each other). Return 0 if there is none.",
    cons=["1 <= len(text1), len(text2) <= 1000"], complexity="O(m * n) time and space", examples=[["abcde", "ace"], ["abc", "def"]], notes=["The common subsequence is 'ace'"],
    hints=["Let dp[i][j] be the answer for the first i and first j characters.", "Equal last characters extend the diagonal; otherwise take the better of dropping one character from either string."],
    mc=("If text1[i-1] == text2[j-1], then dp[i][j] equals:", ["dp[i-1][j-1] + 1", "max(dp[i-1][j], dp[i][j-1])", "0", "dp[i][j-1]"], 0, "A matching pair extends the best answer of both shorter prefixes."),
    sol="""def longestCommonSubsequence(text1, text2):
    m, n = len(text1), len(text2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if text1[i - 1] == text2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[m][n]
""", blanks=["dp[i][j] = dp[i - 1][j - 1] + 1", "dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])"], edge=[["a", "a"], ["a", "b"]], gen=g_lcs)

add(id="dp_knapsack", world=6, repo=None, title="0/1 Knapsack", fn="knapsack", sig="def knapsack(weights, values, capacity):", difficulty="medium", topics=["Dynamic Programming"],
    desc="Each item has a weight and a value and can be taken at most once. Return the largest total value whose total weight does not exceed `capacity`.",
    cons=["1 <= items <= 100", "0 <= capacity <= 1000"], complexity="O(items * capacity) time, O(capacity) space", examples=[[[1, 3, 4, 5], [1, 4, 5, 7], 7], [[2, 3], [10, 20], 1]], notes=["Take the items of weight 3 and 4 for value 9", "Nothing fits"],
    hints=["dp[c] is the best value achievable with capacity c.", "For each item, update capacities from high to low so the item is used only once."],
    mc=("Why loop capacity downward for 0/1 knapsack with one array?", ["Each item may be used once; going upward would reuse it", "It is faster", "The array is reversed", "Values are negative"], 0, "Downward order keeps dp[cap - w] from the previous item row."),
    sol="""def knapsack(weights, values, capacity):
    dp = [0] * (capacity + 1)
    for w, v in zip(weights, values):
        for cap in range(capacity, w - 1, -1):
            dp[cap] = max(dp[cap], dp[cap - w] + v)
    return dp[capacity]
""", blanks=["for cap in range(capacity, w - 1, -1):", "dp[cap] = max(dp[cap], dp[cap - w] + v)"], edge=[[[1], [5], 0], [[3], [9], 3]], gen=g_knap)


# ----------------------------------------------------------------------------- build
STARTERS = {"ll": "# ListNode(val, next) is provided.\n", "ll_cycle": "# ListNode(val, next) is provided.\n",
            "ll_intersect": "# ListNode(val, next) is provided.\n", "graph_clone": "# Node(val, neighbors) is provided.\n"}


def fmt_example(names, args):
    return ", ".join(f"{n} = {a!r}" for n, a in zip(names, args))


def build(repo: Path) -> dict:
    meta = load_repo_meta(repo)
    sandbox = SubprocessSandbox(case_seconds=5)
    questions = []
    for order_by_world, p in enumerate(PROBLEMS):
        kind = p.get("kind", "function")
        spec = {"kind": kind, "function": p["fn"], "options": p.get("options", {}), "class_name": p.get("class_name")}
        names = p.get("arg_names") or [a.strip() for a in p["sig"].split("(", 1)[1].rstrip("):").split(",") if a.strip()]
        rng = random.Random(p["id"])
        candidates = list(p["examples"]) + list(p["edge"]) + [p["gen"](rng) for _ in range(40)]
        unique, seen = [], set()
        for c in candidates:
            key = json.dumps(c)
            if key not in seen:
                seen.add(key)
                unique.append(c)
        unique = unique[:len(p["examples"]) + len(p["edge"]) + 8]
        assert not static_check(p["sol"]), p["id"]
        outcomes = sandbox.run(p["sol"], spec, unique)
        for c, o in zip(unique, outcomes):
            assert o["status"] == "ok", (p["id"], c, o)
        tests = [{"args": c, "expected": o["got"]} for c, o in zip(unique, outcomes)]
        n_samples = len(p["examples"])

        sol = p["sol"].rstrip() + "\n"
        template = sol
        for i, snippet in enumerate(p["blanks"], 1):
            assert template.count(snippet) == 1, (p["id"], snippet)
            template = template.replace(snippet, f"@@{i}@@")
        m = meta.get(p["repo"]) if p.get("repo") else None
        if p.get("repo"):
            assert m, f"{p['repo']} missing from repo data"
        prompt, options, answer, why = p["mc"]
        order = list(range(len(options)))
        random.Random(p["id"] + "mc").shuffle(order)
        examples = []
        for i, c in enumerate(p["examples"]):
            out = tests[i]["expected"]
            if p.get("compare") == "peak":
                out = out
            examples.append({"input": fmt_example(names, c), "output": repr(out),
                             "note": p.get("notes", [""] * 9)[i] if i < len(p.get("notes", [])) else ""})
        starter = p.get("starter") or (STARTERS.get(kind, "") + p["sig"] + "\n    # Write your solution here\n    pass\n")
        questions.append({
            "id": p["id"], "world": p["world"], "order": sum(1 for q in questions if q["world"] == p["world"]) + 1,
            "title": p["title"], "difficulty": (m or {}).get("difficulty") or p["difficulty"],
            "topics": (m or {}).get("topics") or p["topics"], "complexity": p["complexity"],
            "description": p["desc"], "constraints": p["cons"], "examples": examples,
            "function": p["fn"], "signature": p["sig"], "kind": kind, "options": p.get("options", {}),
            "class_name": p.get("class_name"), "compare": p.get("compare", "exact"), "arg_names": names,
            "starter": starter, "samples": tests[:n_samples], "hidden": tests[n_samples:], "hints": p["hints"],
            "beginner": {"prompt": prompt, "options": [options[i] for i in order], "answer": order.index(answer), "explanation": why},
            "intermediate": {"template": template, "blanks": [{"answer": b} for b in p["blanks"]]},
            "source": {"repo": "liquidslr/leetcode-company-wise-problems" if m else None, "title": p.get("repo"),
                       "link": (m or {}).get("link"), "companies": (m or {}).get("companies", 0),
                       "max_frequency": (m or {}).get("max_frequency", 0)},
        })
    return {"generated_from": REPO_URL, "questions": questions}


def main():
    if len(sys.argv) > 1:
        repo = Path(sys.argv[1])
    else:
        repo = Path(tempfile.mkdtemp()) / "repo"
        subprocess.run(["git", "clone", "--depth", "1", REPO_URL, str(repo)], check=True)
    data = build(repo)
    out = ROOT / "challenges" / "questions.json"
    out.write_text(json.dumps(data, indent=1), encoding="utf-8")
    print(f"wrote {len(data['questions'])} questions to {out}")


if __name__ == "__main__":
    main()
