"""Entry point: run `python main.py` from the project root."""
import sys

from game.game import Game


def main() -> int:
    game = Game()
    try:
        game.run()
    finally:
        game.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
