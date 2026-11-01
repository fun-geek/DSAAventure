# 🌳 DSA Jungle Solver

### Explore the Jungle. Solve DSA. Conquer Challenges.

**DSA Jungle Solver** is a 2D pixel-art adventure game developed using Python and Pygame that transforms Data Structures and Algorithms practice into an interactive gaming experience.

Explore a mysterious jungle, interact with NPCs, complete quests, discover coding challenges, earn XP and coins, and sharpen your problem-solving skills through an adventure.

**What if learning DSA felt like playing an adventure game?**

That's the idea behind DSA Jungle Solver.

---

## 🎮 About the Project

Traditional coding platforms focus on solving programming problems. DSA Jungle Solver introduces a different approach by combining game mechanics with algorithmic learning.

Players explore an interactive jungle environment, discover ancient coding totems, interact with characters, and solve DSA challenges to progress.

The game currently features a playable Array Jungle, six DSA practice categories, 33 programming problems, and three challenge difficulty modes.

## ✨ Features

### 🌲 Interactive 2D Adventure
- Pixel-art jungle environment.
- Animated player character.
- WASD and arrow-key movement.
- Running mechanics.
- Camera and depth-sorted environment objects.
- River, rope bridge, huts, trees and jungle decorations.
- Interactive treasure chests, coins and gems.

### 🧙 NPCs and Quest System
- Three interactive NPCs.
- Five chained quests.
- Interactive dialogues.
- Quest log.
- Six ancient coding totems that unlock programming challenges.

### 🧠 DSA Challenge Engine

Practice 33 important Data Structures and Algorithms problems across six categories.

| DSA Category | Problems |
|---|---:|
| Arrays | 6 |
| Searching | 5 |
| Linked Lists | 5 |
| Stack & Queue | 5 |
| Graphs | 6 |
| Dynamic Programming | 6 |
| **Total** | **33** |

### Three Challenge Modes

| Mode | Description |
|---|---|
| Beginner | Solve multiple-choice questions. |
| Intermediate | Complete missing lines of code. |
| Advanced | Write complete functions and pass hidden test cases. |

Additional features:
- Problem descriptions and examples.
- Hints and test cases.
- Run sample tests.
- Submit solutions against hidden tests.
- Difficulty-based XP and coin rewards.

### 🏆 Player Progression
- XP and coins.
- Difficulty-based rewards.
- Rewards paid once per challenge mode.
- SQLite-based player progress.
- Single-slot save system.
- Player profile.
- World selection.

### ⚙️ Game Settings
- Sound effects volume control.
- Fullscreen mode.
- Pause menu.

---

## 🌍 DSA Worlds

The question bank covers six major DSA categories.

| World | Topics | Example Problems |
|---|---|---|
| 🌱 Array Jungle | Arrays | Two Sum, Maximum Subarray |
| 🔍 Searching Cave | Binary Search | Binary Search, Search in Rotated Sorted Array |
| 🔗 Linked List Village | Linked Lists | Reverse Linked List, Linked List Cycle |
| 🏔️ Stack Mountain | Stack & Queue | Valid Parentheses, Min Stack |
| 🕸️ Graph Dungeon | Graph Algorithms | BFS, DFS, Number of Islands |
| 🐉 DP Kingdom | Dynamic Programming | Climbing Stairs, House Robber, Coin Change |

**Current status:** Array Jungle has a playable game environment. All six categories are accessible through Practice Puzzles.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core programming language |
| Pygame | 2D game development |
| SQLite | Persistent player data |
| JSON | DSA question storage |
| unittest | Automated testing |
| Git & GitHub | Version control |

**A special implementation detail:** All game art and sound effects are generated in code, so external asset downloads are not required.

---

## 📁 Project Structure

```text
DSA-Jungle-Solver/
│
├── assets/
│
├── challenges/
│   ├── challenge_engine.py
│   ├── validator.py
│   ├── sandbox.py
│   ├── _runner.py
│   └── questions.json
│
├── game/
│
├── saves/
│
├── systems/
│   ├── database.py
│   ├── quest_manager.py
│   ├── progression.py
│   └── audio.py
│
├── tests/
│
├── tools/
│   └── build_questions.py
│
├── ui/
│
├── worlds/
│   └── array_forest.py
│
├── main.py
├── settings.py
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/DSA-Jungle-Solver.git
```

### 2. Navigate to the project directory

```bash
cd DSA-Jungle-Solver
```

### 3. Create a virtual environment

**Windows:**

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the game

```bash
python main.py
```

---

## 🎮 Game Controls

| Key | Action |
|---|---|
| WASD / Arrow Keys | Move player |
| Shift | Run |
| E / Enter / Space | Interact with NPCs, chests, signs and totems |
| Q | Open quest log |
| P | Open Practice Puzzles on World Select |
| Esc | Pause / Back |
| F1 – F3 | Switch challenge mode |
| F5 | Run sample tests |
| F6 | Submit solution |
| Tab | Move to next code blank |

---

## 🔐 Code Execution and Security

One of the important engineering components of DSA Jungle Solver is its isolated code execution architecture.

Player-submitted code does not execute directly inside the main game process.

The current implementation includes:

- Syntax validation and dangerous-operation rejection.
- Restricted imports and builtins.
- Separate Python subprocess execution.
- Isolated execution using Python's `-I` mode.
- Empty working directory.
- CPU and memory limits on supported POSIX systems.
- Per-test timer and wall-clock timeout.
- A `SandboxRunner` interface that allows future execution backend replacement.

**Security note:** The current subprocess sandbox is intended for a single-player desktop game. It is not a hardened security boundary for untrusted public users. A container-based or remote execution backend should be used before exposing code execution to strangers.

On Windows, per-test CPU timers and memory limits are unavailable; only the wall-clock timeout applies.

---

## 📚 DSA Question Bank

The project contains 33 problems stored in:

```text
challenges/questions.json
```

Problem difficulty, topics, LeetCode links and company-frequency information are sourced from:


Problem statements, examples, hints, test cases and solutions are original.

To rebuild the question bank:

```bash
git clone --depth 1 https://github.com/liquidslr/leetcode-company-wise-problems

python tools/build_questions.py ./leetcode-company-wise-problems
```

BFS, DFS and 0/1 Knapsack are original problems. Shortest Path in a Grid is a simplified four-direction variant.

---

## 🧪 Testing

DSA Jungle Solver currently includes **46 unit and headless end-to-end tests**.

Run the complete test suite:

```bash
python -m unittest discover -s tests -t .
```

---

## 🗺️ Development Roadmap

### Completed

- [x] Pygame game environment.
- [x] Main menu and game scenes.
- [x] Player movement and animations.
- [x] Array Jungle environment.
- [x] Camera and collision systems.
- [x] NPC interactions and chained quests.
- [x] Six interactive coding totems.
- [x] 33 DSA practice problems.
- [x] Three challenge difficulty modes.
- [x] Sample and hidden test validation.
- [x] SQLite save system.
- [x] XP and coin progression.
- [x] Automated testing.

### Upcoming

- [ ] Playable maps for the remaining five DSA worlds.
- [ ] Boss battle system.
- [ ] Inventory system.
- [ ] Achievement and badge system.
- [ ] Background music.
- [ ] More animations and environmental interactions.
- [ ] Additional quests and challenges.

---

## 🤝 Contributing

Contributions, ideas, suggestions and bug reports are welcome!

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Test your implementation.
5. Submit a Pull Request.

---

## 🎯 Project Vision

The vision behind DSA Jungle Solver is to make learning Data Structures and Algorithms more engaging, interactive and enjoyable.

Learning algorithms doesn't always have to feel like an examination.

Sometimes, it can be an adventure.

Explore new environments, discover hidden challenges, solve problems and conquer the jungle.

---

## 👨‍💻 Developer

Built with ❤️ using Python and Pygame.

**DSA Jungle Solver**

*Explore the Jungle. Solve DSA. Conquer Challenges.*
Here is new way to learn DSA

⭐ If you like this project, consider giving the repository a star!
