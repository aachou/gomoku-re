from typing import Dict, Optional

from .board import Board, BOARD_SIZE

STARTING_STONES = 30
PLAYER_NAMES = {1: '黑棋', 2: '白棋'}


class Game:
    def __init__(self, size=BOARD_SIZE, starting_stones=STARTING_STONES):
        self.board = Board(size)
        self.size = size
        self.supply = {1: starting_stones, 2: starting_stones}
        self.current = 1
        self.player_types: Dict[int, str] = {1: 'human', 2: 'human'}
        self.ai_levels: Dict[int, Optional[str]] = {1: None, 2: None}

    def has_lost(self, player):
        return self.supply[player] <= 0

    def is_game_over(self):
        return self.has_lost(self.current)

    def opponent(self):
        return 3 - self.current

    def _deduct_supply(self, player, amount=1):
        self.supply[player] -= amount
        if self.supply[player] < 0:
            self.supply[player] = 0

    def place_stone(self, x, y):
        if self.supply[self.current] <= 0:
            return False
        self.board.set(x, y, self.current)
        self._deduct_supply(self.current)
        return True

    def replacement_is_available(self):
        return self.board.count_opponent_stones(self.current) > 0 and self.supply[self.current] > 0

    def apply_replacement(self, x, y):
        self._deduct_supply(self.current)
        self.board.set(x, y, self.current)

    def process_stone_placement(self, x, y):
        line = self.board.find_connected_line(x, y, self.current)
        if not line:
            return ('no_line', None, False)
        self.board.remove_line(line)
        recovered = len(line)
        self.supply[self.current] += recovered
        can_replace = self.replacement_is_available()
        return ('recovered', recovered, can_replace)
