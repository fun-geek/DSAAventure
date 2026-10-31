# DSA Jungle Solver

A 2D pixel-art jungle adventure that teaches Data Structures & Algorithms.
Python 3.10+ / Pygame / SQLite. All art and sound effects are generated in code, so there are no asset downloads.

## Install and run
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # pygame>=2.5
python main.py
```
Run the tests: `python -m unittest discover -s tests -t .`

## Controls
| Key | Action |
|---|---|
| WASD / arrows | move (hold Shift to run) |
| E / Enter / Space | talk, open chests, read signs, start totem puzzles |
| Q | quest log |
| Esc | pause / back |
| Challenge screen | F1-F3 switch mode, F5 run samples, F6 submit, Tab next blank |

## What is playable
- Main menu, saves (SQLite, one slot), world select, profile, settings (SFX volume, fullscreen).
- **Array Jungle** map: animated explorer, depth-sorted palms and jungle giants, thatched huts, river and rope bridge,
  chests, coins, gems, signs, a campfire, 3 NPCs with 5 chained quests.
- **Totem puzzles**: six carved totems in Array Jungle open real coding challenges.
- **Practice Puzzles** (button/`P` on World Select): all 33 problems across the six worlds.
- Three modes per problem: Beginner (multiple choice), Intermediate (fill the missing code),
  Advanced (write the function; Run = sample tests, Submit = hidden tests). Rewards (XP/coins) are paid once per mode
  and scale by difficulty and mode (see `settings.py`).

Not built yet: maps for worlds 2-6, boss battles, achievements/inventory, music (Phases 6-8).
`PRACTICE_ALL_WORLDS` in `settings.py` lets you practise every world's puzzles now.

## Question bank and data source
`challenges/questions.json` has 33 problems (6/5/5/5/6/6 across the worlds). Difficulty, topics, LeetCode link and the
"asked by N companies" count come from the CSVs in
[liquidslr/leetcode-company-wise-problems](https://github.com/liquidslr/leetcode-company-wise-problems).
The statements, examples, hints, test cases and solutions are original. Expected outputs are produced by running reference
solutions through the same sandbox that grades players. Rebuild the file with:
```bash
git clone --depth 1 https://github.com/liquidslr/leetcode-company-wise-problems
python tools/build_questions.py ./leetcode-company-wise-problems
```
BFS, DFS and 0/1 Knapsack are not in that repo, so they are original problems; "Shortest Path in a Grid" is a simplified
4-direction variant.

## Code execution safety
Player code never runs in the game process. `challenges/validator.py` rejects dangerous syntax (imports outside a small
allow-list, `open`, `eval`, `getattr`, dunder attributes...). `challenges/sandbox.py` then starts a fresh `python -I`
process with an empty working directory, minimal environment, CPU/memory limits (POSIX), restricted builtins, a per-test
timer and a wall-clock timeout. `SandboxRunner` is an interface, so a Docker or remote judge can replace
`SubprocessSandbox` later. This is layered defence for a single-player game, not a hardened jail: use a container
backend before exposing it to strangers. On Windows the per-test timer and memory limits are unavailable and only the
wall-clock timeout applies.

## Layout
```
main.py  settings.py  requirements.txt
game/        game loop, scenes, player, camera, collision, tiles, objects
worlds/      array_forest.py (Array Jungle map, objects, NPCs, quests)
challenges/  challenge_engine.py  validator.py  sandbox.py  _runner.py  questions.json
systems/     database.py (SQLite)  quest_manager.py  progression.py  audio.py
ui/          menus, HUD, dialogue, quest log, challenge screen, code editor, jungle background
tools/       build_questions.py
tests/       46 unit and headless end-to-end tests
```
