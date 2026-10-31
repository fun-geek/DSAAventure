"""World 1: Array Jungle (module name kept for the project layout). Deterministic procedurally generated layout."""
import math
import random

W, H = 64, 48
SPAWN = (10, 24)


OBJECTS = [
    {"id": "sign_welcome", "kind": "sign", "tx": 11, "ty": 22,
     "text": "Welcome to Array Jungle! An array stores items side by side in memory, "
             "so any item can be reached instantly by its index."},
    {"id": "sign_index", "kind": "sign", "tx": 46, "ty": 21,
     "text": "Indexes start at 0. The first item lives at arr[0] and the last at arr[n-1]. "
             "Going past the end is how the Index Guardian catches careless adventurers!"},
    {"id": "sign_bridge", "kind": "sign", "tx": 28, "ty": 22,
     "text": "Tip for Two Sum: instead of checking every pair, remember each number you "
             "have seen in a hash map. One pass is enough."},
    {"id": "npc_elder", "kind": "npc", "tx": 13, "ty": 22, "name": "Elder Arrin", "look": "elder",
     "idle": ["The Index Guardian stirs in the deep jungle. Sharpen your array skills!"]},
    {"id": "npc_pip", "kind": "npc", "tx": 25, "ty": 22, "name": "Pip the Merchant",
     "look": "merchant", "idle": ["Business is booming. Thanks again, friend!"]},
    {"id": "npc_rue", "kind": "npc", "tx": 43, "ty": 22, "name": "Rue the Ranger",
     "look": "ranger", "idle": ["Stay sharp out there. The jungle hides many secrets."]},
    {"id": "totem_1", "kind": "totem", "tx": 15, "ty": 22, "qid": "array_two_sum"},
    {"id": "totem_2", "kind": "totem", "tx": 21, "ty": 25, "qid": "array_stock"},
    {"id": "totem_3", "kind": "totem", "tx": 36, "ty": 22, "qid": "array_max_subarray"},
    {"id": "totem_4", "kind": "totem", "tx": 40, "ty": 25, "qid": "array_contains_duplicate"},
    {"id": "totem_5", "kind": "totem", "tx": 52, "ty": 22, "qid": "array_move_zeroes"},
    {"id": "totem_6", "kind": "totem", "tx": 57, "ty": 25, "qid": "array_product_except_self"},
    {"id": "fire_camp", "kind": "campfire", "tx": 12, "ty": 26},
    {"id": "chest_house", "kind": "chest", "tx": 22, "ty": 19},
    {"id": "chest_pond", "kind": "chest", "tx": 46, "ty": 31},
    {"id": "chest_trail", "kind": "chest", "tx": 11, "ty": 36},
    {"id": "coin_1", "kind": "coin", "tx": 16, "ty": 23},
    {"id": "coin_2", "kind": "coin", "tx": 20, "ty": 24},
    {"id": "coin_3", "kind": "coin", "tx": 24, "ty": 23},
    {"id": "coin_4", "kind": "coin", "tx": 37, "ty": 23},
    {"id": "coin_5", "kind": "coin", "tx": 41, "ty": 24},
    {"id": "coin_6", "kind": "coin", "tx": 50, "ty": 23},
    {"id": "coin_7", "kind": "coin", "tx": 56, "ty": 24},
    {"id": "coin_8", "kind": "coin", "tx": 47, "ty": 31},
    {"id": "gem_1", "kind": "gem", "tx": 9, "ty": 12},
    {"id": "gem_2", "kind": "gem", "tx": 9, "ty": 34},
    {"id": "gem_3", "kind": "gem", "tx": 45, "ty": 21},
]


QUESTS = [
    {"id": "q_signs", "giver": "npc_elder", "title": "Read the Signs",
     "objective": "Read signposts", "prefix": "sign_", "target": 3, "requires": None,
     "xp": 40, "coins": 20,
     "offer": ["Welcome, traveler! I am Elder Arrin, keeper of Array Jungle.",
               "Every tree here stands in a numbered row, just like the items in an array. "
               "Each one can be found by its index.",
               "Read the three signposts around the jungle, then come back and tell me what you learned."],
     "progress": ["Keep reading! Signposts stand by the campfire, the bridge and the eastern house."],
     "complete": ["Well done! Remember: indexes start at 0, and a hash map can turn a slow "
                  "pair search into a single pass.", "Take this reward, you earned it."]},
    {"id": "q_gems", "giver": "npc_elder", "title": "Gems of the Guardian",
     "objective": "Find gems", "prefix": "gem_", "target": 3, "requires": "q_signs",
     "xp": 80, "coins": 40,
     "offer": ["The Index Guardian is drawn to shiny gems. Three are hidden along the jungle trails.",
               "Bring them to me and I will help you prepare for his challenges."],
     "progress": ["Look along the long trails: north, south and near the eastern house."],
     "complete": ["You found them all! The Guardian's array challenges will test you soon."]},
    {"id": "q_solve", "giver": "npc_elder", "title": "Code Apprentice",
     "objective": "Solve totem puzzles", "prefix": "solve_", "target": 3, "requires": "q_gems",
     "xp": 120, "coins": 60,
     "offer": ["Ancient totems stand along the jungle roads. Each one guards a puzzle about arrays.",
               "Solve three of them in any mode and the jungle will recognise you as a true Code Apprentice."],
     "progress": ["Stand next to a totem and press E. Beginner mode is a good warm-up."],
     "complete": ["Three puzzles cracked! The Index Guardian will think twice before facing you."]},
    {"id": "q_coins", "giver": "npc_pip", "title": "Pip's Payment",
     "objective": "Collect coins", "prefix": "coin_", "target": 6, "requires": None,
     "xp": 30, "coins": 15,
     "offer": ["Psst! Pip the Merchant here. Coins keep my little shop afloat.",
               "Gather 6 coins from the jungle roads and I will pay you back with interest!"],
     "progress": ["Still short! Coins glitter along the roads and by the pond."],
     "complete": ["Six shiny coins! Here is your payment, as promised."]},
    {"id": "q_chests", "giver": "npc_rue", "title": "Treasure Hunter",
     "objective": "Open chests", "prefix": "chest_", "target": 3, "requires": None,
     "xp": 60, "coins": 30,
     "offer": ["I am Rue, the ranger. Three old chests are hidden in this jungle.",
               "Open all of them and I will make it worth your while."],
     "progress": ["Chests rest near the first house, by the pond and on the southern trail."],
     "complete": ["All three opened! You have a keen eye, adventurer."]},
]


def build() -> list[str]:
    rng = random.Random(42)
    g = [["."] * W for _ in range(H)]
    for y in range(H):  # scatter trees, flowers, rocks
        for x in range(W):
            r = rng.random()
            g[y][x] = ("T" if r < 0.17 else "f" if r < 0.27 else "*" if r < 0.32
                       else "O" if r < 0.34 else ".")

    def fill(x0, y0, x1, y1, ch):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                g[y][x] = ch

    houses = [(18, 16), (44, 14)]
    fill(6, 20, 14, 28, ".")                       # spawn clearing
    for hx, hy in houses:
        fill(hx - 2, hy - 2, hx + 5, hy + 8, ".")  # house clearings
    fill(46, 31, 54, 37, ".")                      # pond clearing

    river_x = [32 + round(2 * math.sin(y / 5)) for y in range(H)]
    for y in range(H):                             # river
        fill(river_x[y] - 1, y, river_x[y] + 1, y, "~")

    fill(6, 23, 58, 24, ",")                       # main east-west road (2 wide)
    for y in range(22, 28):                        # bridge across the river
        fill(river_x[y] - 1, y, river_x[y] + 1, y, "=")
    for hx, hy in houses:                          # houses + paths to their doors
        fill(hx, hy, hx + 3, hy, "R")
        fill(hx, hy + 1, hx + 3, hy + 1, "M")
        fill(hx, hy + 2, hx + 3, hy + 2, "M")
        g[hy + 2][hx + 1] = "D"
        fill(hx + 1, hy + 3, hx + 1, 22, ",")
    fill(47, 32, 53, 36, "~")                      # pond
    fill(8, 8, 9, 40, ",")                         # north-south trail near spawn
    fill(46, 25, 46, 30, ",")                      # trail down to the pond
    fill(8, 36, 10, 36, ",")                       # side trail to a chest
    for o in OBJECTS:                              # make sure objects sit on open ground
        if o["kind"] in ("chest", "sign", "campfire", "npc", "totem") and g[o["ty"]][o["tx"]] not in ",=":
            g[o["ty"]][o["tx"]] = "."
    for i in range(W):                             # jungle border, 2 tiles thick
        for k in (0, 1):
            g[k][i] = g[H - 1 - k][i] = "T"
    for j in range(H):
        for k in (0, 1):
            g[j][k] = g[j][W - 1 - k] = "T"
    return ["".join(row) for row in g]
