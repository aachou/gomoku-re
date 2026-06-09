import sys

from game import Game
from ui import GameUI

if __name__ == '__main__':
    if GameUI is not None and (len(sys.argv) == 1 or sys.argv[1] != 'cli'):
        app = GameUI()
        app.run()
    else:
        game = Game()
        try:
            game.play()
        except KeyboardInterrupt:
            print('\n游戏已退出。')
        sys.exit(0)
