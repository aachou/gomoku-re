from typing import List, Optional, Set, Tuple

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
BOARD_SIZE = 15
SYMBOLS = {0: '.', 1: '●', 2: '○'}


class Board:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.grid = [[0] * size for _ in range(size)]
        self._empty_cells: Set[Tuple[int, int]] = {(x, y) for y in range(size) for x in range(size)}
        self._stone_count: List[int] = [0, 0, 0]

    def _rebuild_cache(self):
        self._empty_cells.clear()
        self._stone_count = [0, 0, 0]
        for y in range(self.size):
            for x in range(self.size):
                v = self.grid[y][x]
                if v == 0:
                    self._empty_cells.add((x, y))
                else:
                    self._stone_count[v] += 1

    def in_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x, y):
        return self.grid[y][x]

    def set(self, x, y, value):
        old = self.grid[y][x]
        if old == value:
            return old
        self.grid[y][x] = value
        if old != 0:
            self._empty_cells.add((x, y))
            self._stone_count[old] -= 1
        if value != 0:
            self._empty_cells.discard((x, y))
            self._stone_count[value] += 1
        return old

    def is_empty(self, x, y):
        return self.grid[y][x] == 0

    def legal_moves(self) -> List[Tuple[int, int]]:
        return list(self._empty_cells)

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
        coords.sort(key=lambda p: p[0] * dx + p[1] * dy)
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
        return self._stone_count[3 - player]

    def clone(self):
        clone = Board(self.size)
        clone.grid = [row.copy() for row in self.grid]
        clone._rebuild_cache()
        return clone
