import json
import os
from typing import Any, Dict, List, NamedTuple, Optional

from .board import Board, BOARD_SIZE


class PlacementResult(NamedTuple):
    result: str
    recovered: Optional[int]
    can_replace: bool

STARTING_STONES = 30
PLAYER_NAMES = {1: '黑棋', 2: '白棋'}
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'gomoku_config.json')
DEFAULT_CONFIG = {
    'ai_level': 'medium',
    'board_size': 15,
    'starting_stones': 30,
    'ai_delay_ms': 300,
}


def save_config(**kwargs):
    config = DEFAULT_CONFIG.copy()
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                config.update(json.load(f))
    except Exception:
        pass
    config.update(kwargs)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception:
        pass


def load_config() -> dict:
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                data = json.load(f)
            result = DEFAULT_CONFIG.copy()
            result.update(data)
            return result
    except Exception:
        pass
    return dict(DEFAULT_CONFIG)


class Game:
    def __init__(self, size=BOARD_SIZE, starting_stones=STARTING_STONES):
        self.board = Board(size)
        self.size = size
        self.supply = {1: starting_stones, 2: starting_stones}
        self.current = 1
        self.player_types: Dict[int, str] = {1: 'human', 2: 'human'}
        self.ai_levels: Dict[int, Optional[str]] = {1: None, 2: None}
        self._history: List[dict] = []
        self.move_log: List[dict] = []
        self.timers: Dict[int, float] = {1: 0.0, 2: 0.0}
        self._turn_start: float = 0.0

    def start_turn_timer(self):
        import time
        self._turn_start = time.time()

    def stop_turn_timer(self):
        import time
        self.timers[self.current] += time.time() - self._turn_start

    def log_move(self, action: str, x: int, y: int, recovered: int = 0):
        self.move_log.append({
            'player': self.current,
            'action': action,
            'x': x,
            'y': y,
            'recovered': recovered,
        })

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
        if self.move_log:
            self.move_log.pop()
        return True

    def serialize(self) -> dict:
        return {
            'size': self.size,
            'grid': self.board.grid,
            'supply': [self.supply[1], self.supply[2]],
            'current': self.current,
            'player_types': [self.player_types[1], self.player_types[2]],
            'ai_levels': [self.ai_levels[1], self.ai_levels[2]],
            'move_log': self.move_log,
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
        game.move_log = data.get('move_log', [])
        return game

    def has_lost(self, player):
        return self.supply[player] <= 0

    def is_draw(self):
        return self.board.is_full() and not self.has_lost(1) and not self.has_lost(2)

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
