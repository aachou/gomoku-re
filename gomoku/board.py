from typing import Dict, List, Optional, Set, Tuple

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
BOARD_SIZE = 15
SYMBOLS = {0: '.', 1: '●', 2: '○'}

_SCORE_TABLE = {
    (4, 2): 50000,
    (4, 1): 5000,
    (4, 0): 5000,
    (3, 2): 3000,
    (3, 1): 300,
    (3, 0): 50,
    (2, 2): 200,
    (2, 1): 30,
    (2, 0): 10,
    (1, 2): 10,
    (1, 1): 3,
    (1, 0): 1,
}


def _pattern_score(count: int, open_ends: int) -> int:
    return _SCORE_TABLE.get((min(count, 5), min(open_ends, 2)), 0)


def _consecutive_count(board: 'Board', x: int, y: int, dx: int, dy: int, player: int) -> int:
    cnt = 0
    for sign in (1, -1):
        step = 1
        while True:
            cx = x + dx * step * sign
            cy = y + dy * step * sign
            if not board.in_bounds(cx, cy) or board.get(cx, cy) != player:
                break
            cnt += 1
            step += 1
    return cnt


def _would_form_five(board: 'Board', player: int, x: int, y: int) -> bool:
    return any(_consecutive_count(board, x, y, dx, dy, player) >= 4 for dx, dy in DIRECTIONS)


def _has_immediate_five(board: 'Board', player: int) -> bool:
    checked = set()
    for px, py in board._player_cells[player]:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = px + dx, py + dy
                if board.in_bounds(nx, ny) and board.is_empty(nx, ny) and (nx, ny) not in checked:
                    if _would_form_five(board, player, nx, ny):
                        return True
                    checked.add((nx, ny))
    return False


def _evaluate_direction(player: int, x: int, y: int, dx: int, dy: int, board: 'Board') -> int:
    count = 0
    open_ends = 0
    for sign in (1, -1):
        step = 1
        while True:
            cx = x + dx * step * sign
            cy = y + dy * step * sign
            if not board.in_bounds(cx, cy):
                break
            cell = board.get(cx, cy)
            if cell == player:
                count += 1
            elif cell == 0:
                open_ends += 1
                break
            else:
                break
            step += 1
    return _pattern_score(count, open_ends)


def _evaluate_potential(player: int, x: int, y: int, board: 'Board') -> int:
    total = 0
    for dx, dy in DIRECTIONS:
        total += _evaluate_direction(player, x, y, dx, dy, board)
    return total


class Board:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.grid = [[0] * size for _ in range(size)]
        self._empty_cells: Set[Tuple[int, int]] = {(x, y) for y in range(size) for x in range(size)}
        self._stone_count: List[int] = [0, 0, 0]
        self._player_cells: Dict[int, Set[Tuple[int, int]]] = {1: set(), 2: set()}
        self._cell_potential: Dict[Tuple[int, int], List[int]] = {}
        self._board_potential: List[int] = [0, 0, 0]
        self._five_threat_cache: Dict[int, Optional[bool]] = {1: None, 2: None}
        self._init_potential_cache()

    def _rebuild_cache(self):
        self._empty_cells.clear()
        self._stone_count = [0, 0, 0]
        self._player_cells = {1: set(), 2: set()}
        for y in range(self.size):
            for x in range(self.size):
                v = self.grid[y][x]
                if v == 0:
                    self._empty_cells.add((x, y))
                else:
                    self._stone_count[v] += 1
                    self._player_cells[v].add((x, y))
        self._init_potential_cache()
        self._five_threat_cache = {1: None, 2: None}

    def has_immediate_five(self, player: int) -> bool:
        if self._five_threat_cache[player] is None:
            self._five_threat_cache[player] = _has_immediate_five(self, player)
        return self._five_threat_cache[player]

    def _init_potential_cache(self):
        self._cell_potential.clear()
        self._board_potential = [0, 0, 0]
        for x, y in self._empty_cells:
            s1 = _evaluate_potential(1, x, y, self)
            s2 = _evaluate_potential(2, x, y, self)
            self._cell_potential[(x, y)] = [s1, s2]
            self._board_potential[1] += s1
            self._board_potential[2] += s2

    def _recalc_cell_potential(self, x, y):
        old_s1, old_s2 = self._cell_potential.get((x, y), (0, 0))
        new_s1 = _evaluate_potential(1, x, y, self)
        new_s2 = _evaluate_potential(2, x, y, self)
        self._cell_potential[(x, y)] = [new_s1, new_s2]
        self._board_potential[1] += new_s1 - old_s1
        self._board_potential[2] += new_s2 - old_s2

    def _update_potential_around(self, x, y):
        for dx, dy in DIRECTIONS:
            for sign in (1, -1):
                step = 1
                while step <= 5:
                    cx = x + dx * step * sign
                    cy = y + dy * step * sign
                    if not self.in_bounds(cx, cy):
                        break
                    if self.grid[cy][cx] == 0:
                        self._recalc_cell_potential(cx, cy)
                    step += 1

    def in_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x, y):
        return self.grid[y][x]

    def set(self, x, y, value):
        old = self.grid[y][x]
        if old == value:
            return old
        self.grid[y][x] = value

        key = (x, y)
        if old == 0:
            s1, s2 = self._cell_potential.pop(key, (0, 0))
            self._board_potential[1] -= s1
            self._board_potential[2] -= s2
        if value == 0:
            s1 = _evaluate_potential(1, x, y, self)
            s2 = _evaluate_potential(2, x, y, self)
            self._cell_potential[key] = [s1, s2]
            self._board_potential[1] += s1
            self._board_potential[2] += s2

        if old != 0:
            self._stone_count[old] -= 1
            self._player_cells[old].discard((x, y))
            if value == 0:
                self._empty_cells.add((x, y))
        if value != 0:
            self._empty_cells.discard((x, y))
            self._stone_count[value] += 1
            self._player_cells[value].add((x, y))

        self._update_potential_around(x, y)
        self._five_threat_cache = {1: None, 2: None}
        return old

    def is_empty(self, x, y):
        return self.grid[y][x] == 0

    def legal_moves(self) -> List[Tuple[int, int]]:
        return list(self._empty_cells)

    def iter_legal_moves(self):
        return iter(self._empty_cells)

    def render(self):
        header = '   ' + ' '.join(chr(ord('A') + i) for i in range(self.size))
        print(header)
        for y in range(self.size):
            row_num = str(y + 1).rjust(2)
            print(row_num + ' ' + ' '.join(SYMBOLS[self.grid[y][x]] for x in range(self.size)))
        print()

    def is_full(self):
        return not self._empty_cells

    def scan_line(self, x, y, dx, dy, player):
        coords = [(x, y)]
        for sign in (-1, 1):
            step = 1
            cx, cy = x + dx * sign, y + dy * sign
            while self.in_bounds(cx, cy) and self.grid[cy][cx] == player:
                coords.append((cx, cy))
                step += 1
                cx, cy = x + dx * step * sign, y + dy * step * sign
        coords.sort(key=lambda p: (p[0] - x) * dx + (p[1] - y) * dy)
        return coords

    def find_connected_line(self, x, y, player) -> Optional[List[Tuple[int, int]]]:
        for dx, dy in DIRECTIONS:
            coords = self.scan_line(x, y, dx, dy, player)
            if len(coords) >= 5:
                index = coords.index((x, y))
                start = max(0, min(index, len(coords) - 5))
                return coords[start:start + 5]
        return None

    def remove_line(self, coords):
        for x, y in coords:
            self.set(x, y, 0)

    def count_opponent_stones(self, player):
        return len(self._player_cells[3 - player])

    def clone(self):
        clone = object.__new__(Board)
        clone.size = self.size
        clone.grid = [row.copy() for row in self.grid]
        clone._empty_cells = self._empty_cells.copy()
        clone._stone_count = self._stone_count.copy()
        clone._player_cells = {1: self._player_cells[1].copy(), 2: self._player_cells[2].copy()}
        clone._cell_potential = {k: v.copy() for k, v in self._cell_potential.items()}
        clone._board_potential = self._board_potential.copy()
        clone._five_threat_cache = {1: self._five_threat_cache[1], 2: self._five_threat_cache[2]}
        return clone
