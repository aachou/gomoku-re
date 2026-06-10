from typing import List, Optional, Tuple

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
BOARD_SIZE = 15
SYMBOLS = {0: '.', 1: '●', 2: '○'}


class Board:
    def __init__(self, size=BOARD_SIZE):
        self.size = size
        self.grid = [[0] * size for _ in range(size)]

    def in_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x, y):
        return self.grid[y][x]

    def set(self, x, y, value):
        self.grid[y][x] = value

    def is_empty(self, x, y):
        return self.get(x, y) == 0

    def legal_moves(self) -> List[Tuple[int, int]]:
        return [(x, y) for y in range(self.size) for x in range(self.size) if self.is_empty(x, y)]

    def render(self):
        header = '   ' + ' '.join(chr(ord('A') + i) for i in range(self.size))
        print(header)
        for y in range(self.size):
            row_num = str(y + 1).rjust(2)
            print(row_num + ' ' + ' '.join(SYMBOLS[self.grid[y][x]] for x in range(self.size)))
        print()

    def is_full(self):
        return all(cell != 0 for row in self.grid for cell in row)

    def scan_line(self, x, y, dx, dy, player):
        coords = [(x, y)]
        for direction in (-1, 1):
            step = direction
            cx, cy = x + dx * step, y + dy * step
            while self.in_bounds(cx, cy) and self.get(cx, cy) == player:
                coords.append((cx, cy))
                step += direction
                cx, cy = x + dx * step, y + dy * step
        coords.sort(key=lambda p: (p[0] * dx + p[1] * dy) if dx != 0 else p[1] if dy != 0 else 0)
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
        opponent = 3 - player
        return sum(1 for row in self.grid for cell in row if cell == opponent)

    def clone(self):
        clone = Board(self.size)
        clone.grid = [row.copy() for row in self.grid]
        return clone
