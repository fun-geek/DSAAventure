"""Global, configurable constants for DSA Jungle Solver."""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
SAVE_DIR = BASE_DIR / "saves"
DB_PATH = SAVE_DIR / "dsa_forest.db"

TITLE = "DSA Jungle Solver"
VERSION = "0.5.0 (Phase 5)"
SCREEN_W, SCREEN_H = 960, 640
FPS = 60

# Pixel-art backgrounds are drawn on a small surface and scaled up.
PIXEL_W, PIXEL_H = 240, 160

COLORS = {
    "text": (244, 236, 205),        # parchment
    "text_dim": (176, 168, 128),
    "text_disabled": (120, 112, 90),
    "title": (255, 208, 84),        # jungle gold
    "shadow": (10, 22, 14),
    "border": (22, 14, 8),          # dark bark
    "btn": (112, 74, 40),           # carved wood
    "btn_focus": (255, 200, 70),
    "btn_text_focus": (48, 28, 10),
    "btn_disabled": (62, 54, 44),
    "panel": (24, 36, 26),          # deep moss
    "panel_edge": (128, 88, 48),    # wooden frame
    "moss": (74, 150, 70),
    "locked": (76, 70, 60),
    "xp_bar": (166, 224, 72),
    "xp_back": (28, 44, 30),
    "warn": (255, 126, 92),
}

# ---- Rewards (configurable; used from Phase 5/6 onward) -------------------
REWARDS = {
    "easy": {"xp": 50, "coins": 10},
    "medium": {"xp": 100, "coins": 25},
    "hard": {"xp": 200, "coins": 60},
    "boss": {"xp": 500, "coins": 150},
}
XP_PER_LEVEL = 200  # level = xp // XP_PER_LEVEL + 1

# ---- Curriculum ----------------------------------------------------------
WORLDS = [
    {"id": 1, "name": "Array Jungle", "boss": "Index Guardian", "problems": 6,
     "color": (76, 175, 80)},
    {"id": 2, "name": "Searching Caverns", "boss": "Binary Beast", "problems": 5,
     "color": (121, 134, 203)},
    {"id": 3, "name": "Linked Vine Village", "boss": "Pointer Phantom",
     "problems": 5, "color": (255, 183, 77)},
    {"id": 4, "name": "Stack & Queue Summit", "boss": "Bracket Monster",
     "problems": 5, "color": (144, 164, 174)},
    {"id": 5, "name": "Graph Temple Ruins", "boss": "Cycle Dragon", "problems": 6,
     "color": (239, 83, 80)},
    {"id": 6, "name": "DP Kingdom", "boss": "Recursion Overlord",
     "problems": 6, "color": (186, 104, 200)},
]

# ---- Gameplay (Phase 2) ---------------------------------------------------
TILE = 32
PLAYER_SPEED = 150      # pixels / second
PLAYER_RUN_MULT = 1.6   # hold Shift

# ---- Collectibles (Phase 3, configurable) ---------------------------------
PICKUP_REWARDS = {"coin": {"coins": 1, "xp": 0}, "gem": {"coins": 5, "xp": 10}}
CHEST_REWARD = {"coins": 25, "xp": 30}
INTERACT_RANGE = 56  # pixels

# ---- Challenges (Phase 5, configurable) -----------------------------------
CHALLENGE_MODE_MULT = {"beginner": 0.5, "intermediate": 0.75, "advanced": 1.0}
SANDBOX_CASE_SECONDS = 2.0      # per test case
SANDBOX_MEMORY_MB = 1024
PRACTICE_ALL_WORLDS = True      # set False once bosses gate progression (Phase 7)
