import json
import sys
import traceback

from gomoku import Game, GameUI
from gomoku.cli import play as cli_play
from gomoku.game import SAVE_FILE


def _crash_save(game):
    try:
        with open(SAVE_FILE, 'w') as f:
            json.dump(game.serialize(), f)
    except Exception:
        pass


if __name__ == '__main__':
    if GameUI is not None and (len(sys.argv) == 1 or sys.argv[1] != 'cli'):
        app = GameUI()
        try:
            app.run()
        except Exception:
            if app._in_game:
                app._save_game()
            traceback.print_exc()
    else:
        game = Game()
        try:
            cli_play(game)
        except KeyboardInterrupt:
            print('\n游戏已退出。')
        except Exception:
            _crash_save(game)
            raise
