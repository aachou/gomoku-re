import json
import os
import time
from typing import Any, Dict, List, NamedTuple, Optional

from .board import Board, BOARD_SIZE


class PlacementResult(NamedTuple):
    result: str
    recovered: Optional[int]
    can_replace: bool

STARTING_STONES = 30
PLAYER_NAMES = {1: '黑棋', 2: '白棋'}
SAVE_FILE = os.path.join(os.path.dirname(__file__), '..', 'gomoku_save.json')
CONFIG_FILE = os.path.join(os.path.dirname(__file__), '..', 'gomoku_config.json')
DEFAULT_CONFIG = {
    'ai_level': 'medium',
    'board_size': 15,
    'starting_stones': 30,
    'ai_delay_ms': 300,
}
STATS_FILE = os.path.join(os.path.dirname(__file__), '..', 'gomoku_stats.json')
DEFAULT_STATS = {
    'total_games': 0,
    'wins': {1: 0, 2: 0},
    'draws': 0,
    'moves': {1: 0, 2: 0},
    'recoveries': {1: 0, 2: 0},
    'total_time': {1: 0.0, 2: 0.0},
}


def save_stats(stats: dict):
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f)
    except Exception:
        pass


def load_stats() -> dict:
    try:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE) as f:
                data = json.load(f)
            result = DEFAULT_STATS.copy()
            result.update(data)
            for key in ('wins', 'moves', 'recoveries', 'total_time'):
                result[key] = {int(k): v for k, v in result[key].items()}
            return result
    except Exception:
        pass
    return dict(DEFAULT_STATS)


def compute_game_stats(game: 'Game', winner: Optional[int]) -> dict:
    b_moves = sum(1 for m in game.move_log if m['player'] == 1)
    w_moves = sum(1 for m in game.move_log if m['player'] == 2)
    b_rec = sum(m.get('recovered', 0) for m in game.move_log if m['player'] == 1)
    w_rec = sum(m.get('recovered', 0) for m in game.move_log if m['player'] == 2)
    return {
        'wins': {1: 1 if winner == 1 else 0, 2: 1 if winner == 2 else 0},
        'draws': 1 if winner is None else 0,
        'moves': {1: b_moves, 2: w_moves},
        'recoveries': {1: b_rec, 2: w_rec},
        'total_time': {1: game.timers[1], 2: game.timers[2]},
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
        self._replay_snapshots: List[dict] = []

    def save_replay_snapshot(self):
        self._replay_snapshots.append({
            'grid': [row.copy() for row in self.board.grid],
            'supply': self.supply.copy(),
            'current': self.current,
            'move_log': [dict(m) for m in self.move_log],
            'timers': self.timers.copy(),
        })

    def restore_replay_snapshot(self, snapshot: dict):
        self.board.grid = [row.copy() for row in snapshot['grid']]
        self.board._rebuild_cache()
        self.supply = snapshot['supply'].copy()
        self.current = snapshot['current']
        self.move_log = [dict(m) for m in snapshot['move_log']]
        if 'timers' in snapshot:
            self.timers = snapshot['timers'].copy()

    def start_turn_timer(self):
        self._turn_start = time.time()

    def stop_turn_timer(self):
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
            'move_log_len': len(self.move_log),
        })

    def undo(self):
        if not self._history:
            return False
        snap = self._history.pop()
        self.board.grid = [row.copy() for row in snap['grid']]
        self.board._rebuild_cache()
        self.supply = snap['supply'].copy()
        self.current = snap['current']
        while len(self.move_log) > snap['move_log_len']:
            self.move_log.pop()
        return True

    def serialize(self) -> dict:
        return {
            'size': self.size,
            'grid': [row.copy() for row in self.board.grid],
            'supply': [self.supply[1], self.supply[2]],
            'current': self.current,
            'player_types': [self.player_types[1], self.player_types[2]],
            'ai_levels': [self.ai_levels[1], self.ai_levels[2]],
            'move_log': self.move_log,
            'timers': [self.timers[1], self.timers[2]],
            'history': self._history,
            'replay_snapshots': self._replay_snapshots,
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
        if 'timers' in data:
            game.timers = {1: data['timers'][0], 2: data['timers'][1]}
        if 'history' in data:
            game._history = data['history']
        if 'replay_snapshots' in data:
            game._replay_snapshots = data['replay_snapshots']
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

    def do_placement(self, x, y):
        if self.supply[self.current] <= 0:
            return None
        if not self.place_stone(x, y):
            return None
        result, recovered, can_replace = self.process_stone_placement(x, y)
        self.log_move('place', x, y, recovered or 0)
        return PlacementResult(result, recovered, can_replace)

    def do_replacement(self, x, y):
        if self.board.get(x, y) != self.opponent():
            return None
        if not self.apply_replacement(x, y):
            return None
        result, recovered, can_replace = self.process_stone_placement(x, y)
        self.log_move('replace', x, y, recovered or 0)
        return PlacementResult(result, recovered, can_replace)

    def process_stone_placement(self, x, y):
        line = self.board.find_connected_line(x, y, self.current)
        if not line:
            return PlacementResult('no_line', None, False)
        self.board.remove_line(line)
        recovered = len(line)
        self.supply[self.current] += recovered
        can_replace = self.replacement_is_available()
        return PlacementResult('recovered', recovered, can_replace)
