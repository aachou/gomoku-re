import sys

from gomoku import Game, GameUI
from gomoku.cli import play as cli_play

if __name__ == '__main__':
    if GameUI is not None and (len(sys.argv) == 1 or sys.argv[1] != 'cli'):
        app = GameUI()
        app.run()
    else:
        game = Game()
        try:
            cli_play(game)
        except KeyboardInterrupt:
            print('\n游戏已退出。')
