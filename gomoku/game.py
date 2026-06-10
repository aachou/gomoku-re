from typing import Dict, List, NamedTuple, Optional

from .board import Board, BOARD_SIZE


class PlacementResult(NamedTuple):
    result: str
    recovered: Optional[int]
    can_replace: bool

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
        self._history: List[dict] = []

    def save_snapshot(self):
        self._history.append({
            'grid': [row.copy() for row in self.board.grid],
            'supply': self.supply.copy(),
            'current': self.current,
        })

    def undo(self):
        if not self._history:
            return False
        snap = self._history.pop()
        self.board.grid = [row.copy() for row in snap['grid']]
        self.board._rebuild_cache()
        self.supply = snap['supply'].copy()
        self.current = snap['current']
        return True

    def serialize(self) -> dict:
        return {
            'size': self.size,
            'grid': self.board.grid,
            'supply': [self.supply[1], self.supply[2]],
            'current': self.current,
            'player_types': [self.player_types[1], self.player_types[2]],
            'ai_levels': [self.ai_levels[1], self.ai_levels[2]],
        }

    @classmethod
    def deserialize(cls, data: dict):
        game = cls(size=data['size'])
        for y in range(data['size']):
            for x in range(data['size']):
                game.board.grid[y][x] = data['grid'][y][x]
        game.board._rebuild_cache()
        game.supply = {1: data['supply'][0], 2: data['supply'][1]}
        game.current = data['current']
        game.player_types = {1: data['player_types'][0], 2: data['player_types'][1]}
        game.ai_levels = {1: data['ai_levels'][0], 2: data['ai_levels'][1]}
        return game

    def has_lost(self, player):
        return self.supply[player] <= 0

    def opponent(self):
        return 3 - self.current

    def _deduct_supply(self, player, amount=1):
        self.supply[player] = max(self.supply[player] - amount, 0)

    def place_stone(self, x, y):
        if self.supply[self.current] <= 0:
            return False
        self.board.set(x, y, self.current)
        self._deduct_supply(self.current)
        return True

    def replacement_is_available(self):
        return self.board.count_opponent_stones(self.current) > 0 and self.supply[self.current] > 0

    def apply_replacement(self, x, y):
        if self.board.get(x, y) != self.opponent():
            return False
        self._deduct_supply(self.current)
        self.board.set(x, y, self.current)
        return True

    def process_stone_placement(self, x, y):
        line = self.board.find_connected_line(x, y, self.current)
        if not line:
            return PlacementResult('no_line', None, False)
        self.board.remove_line(line)
        recovered = len(line)
        self.supply[self.current] += recovered
        can_replace = self.replacement_is_available()
        return PlacementResult('recovered', recovered, can_replace)
