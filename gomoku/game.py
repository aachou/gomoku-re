import random
from typing import Dict, Optional

DIRECTIONS = [(1, 0), (0, 1), (1, 1), (1, -1)]
BOARD_SIZE = 15
STARTING_STONES = 30

SYMBOLS = {0: '.', 1: '●', 2: '○'}
PLAYER_NAMES = {1: '黑棋', 2: '白棋'}
AI_LEVELS = ['simple', 'medium', 'hard']


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

    def legal_moves(self):
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

    def find_connected_line(self, x, y, player):
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


class Game:
    def __init__(self, size=BOARD_SIZE, starting_stones=STARTING_STONES):
        self.board = Board(size)
        self.size = size
        self.supply = {1: starting_stones, 2: starting_stones}
        self.current = 1
        self.player_types: Dict[int, str] = {1: 'human', 2: 'human'}
        self.ai_levels: Dict[int, Optional[str]] = {1: None, 2: None}

    def setup(self):
        print('=== 不一样的五子棋 ===')
        print('规则: 先连成五颗棋子不立即获胜，而是回收这条连线，并用一颗棋子替换对方棋子。')
        print('先把棋子下完的一方判负。')
        print('支持人机对战，AI 具有简单、中等、困难三个难度。')
        print()

        mode = self.choose_option('请选择对战模式：1) 双人 2) 人机', ['1', '2'])
        if mode == '2':
            side = self.choose_option('请选择你执哪一方：1) 黑棋 2) 白棋', ['1', '2'])
            ai_player = 2 if side == '1' else 1
            self.player_types[int(side)] = 'human'
            self.player_types[ai_player] = 'ai'
            level = self.choose_option('请选择 AI 难度：1) 简单 2) 中等 3) 困难', ['1', '2', '3'])
            self.ai_levels[ai_player] = AI_LEVELS[int(level) - 1]
        else:
            self.player_types[1] = 'human'
            self.player_types[2] = 'human'

        try:
            raw = input(f'初始每方棋子数量（回车默认 {self.supply[1]}）: ').strip()
            if raw:
                val = int(raw)
                if val > 0:
                    self.supply = {1: val, 2: val}
        except Exception:
            pass

        try:
            raw_size = input(f'棋盘大小（回车默认 {self.board.size}）: ').strip()
            if raw_size:
                b = int(raw_size)
                if 5 <= b <= 99:
                    self.board = Board(b)
                    self.size = b
        except Exception:
            pass

        print(f'初始每方棋子数量：{self.supply[1]}')
        print('输入格式: A1 或 1 1')
        print()

    def choose_option(self, prompt, choices):
        while True:
            answer = input(prompt + ' > ').strip()
            if answer in choices:
                return answer
            print('无效输入，请重新输入。')

    def parse_coordinate(self, raw):
        raw = raw.strip().upper()
        if not raw:
            return None
        if raw[0].isalpha():
            col = ord(raw[0]) - ord('A')
            row_text = raw[1:]
            if not row_text.isdigit():
                return None
            row = int(row_text) - 1
            return (col, row) if self.board.in_bounds(col, row) else None
        parts = raw.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            x = int(parts[0]) - 1
            y = int(parts[1]) - 1
            return (x, y) if self.board.in_bounds(x, y) else None
        return None

    def input_move(self):
        while True:
            raw = input(f'{PLAYER_NAMES[self.current]} 请输入落子坐标: ').strip()
            coord = self.parse_coordinate(raw)
            if coord is None:
                print('坐标格式错误，请使用 A1 或 1 1')
                continue
            x, y = coord
            if not self.board.is_empty(x, y):
                print('该位置已有棋子，请选择空位。')
                continue
            return x, y

    def input_replacement(self):
        while True:
            raw = input(f'{PLAYER_NAMES[self.current]} 请输入想替换的对方棋子坐标: ').strip()
            coord = self.parse_coordinate(raw)
            if coord is None:
                print('坐标格式错误，请使用 A1 或 1 1')
                continue
            x, y = coord
            if self.board.get(x, y) != 3 - self.current:
                print('请选择对方的棋子位置。')
                continue
            return x, y

    def has_lost(self, player):
        return self.supply[player] <= 0

    def game_over(self):
        if self.has_lost(self.current):
            return True
        return False

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

    def line_after_placement(self, x, y):
        return self.board.find_connected_line(x, y, self.current)

    def recover_line(self, coords):
        self.board.remove_line(coords)
        recovered = len(coords)
        self.supply[self.current] += recovered
        return recovered

    def replacement_is_available(self):
        return self.board.count_opponent_stones(self.current) > 0 and self.supply[self.current] > 0

    def apply_replacement(self, x, y):
        self._deduct_supply(self.current)
        self.board.set(x, y, self.current)

    def _handle_line_loop(self, x, y):
        """Place stone at (x,y) then handle line/recovery/replacement loop.
        Returns True if the turn ended naturally, False if the player lost."""
        self.board.set(x, y, self.current)
        self._deduct_supply(self.current)
        while True:
            line = self.board.find_connected_line(x, y, self.current)
            if not line:
                break
            self.board.remove_line(line)
            self.supply[self.current] += len(line)
            if self.supply[self.current] <= 0 or self.board.count_opponent_stones(self.current) == 0:
                break
            if self.player_types[self.current] == 'human':
                rep = self.input_replacement()
            else:
                rep = self.select_ai_replacement(self.current)
            if rep is None:
                break
            rx, ry = rep
            self.apply_replacement(rx, ry)
            x, y = rx, ry
        return not self.has_lost(self.current)

    def play(self):
        self.setup()
        while True:
            if self.has_lost(self.current):
                print(f'{PLAYER_NAMES[self.current]} 棋子用完，{PLAYER_NAMES[self.opponent()]} 获胜！')
                break

            self.board.render()
            print(f'{PLAYER_NAMES[1]}：{self.supply[1]} 颗棋子    {PLAYER_NAMES[2]}：{self.supply[2]} 颗棋子')

            if self.player_types[self.current] == 'human':
                x, y = self.input_move()
            else:
                x, y = self.select_ai_move(self.current)
                print(f'AI({self.ai_levels[self.current]}) 选择 {chr(ord("A") + x)}{y + 1}')

            print(f'{PLAYER_NAMES[self.current]} 放置棋子: {chr(ord("A") + x)}{y + 1}')
            self._handle_line_loop(x, y)

            if self.has_lost(self.current):
                print(f'{PLAYER_NAMES[self.current]} 棋子用完，{PLAYER_NAMES[self.opponent()]} 获胜！')
                break

            self.current = self.opponent()

    def select_ai_move(self, player):
        level = self.ai_levels[player]
        if level == 'simple':
            return self.ai_random_move()
        if level == 'medium':
            return self.ai_greedy_move(player)
        return self.ai_hard_move(player)

    def ai_random_move(self):
        moves = self.board.legal_moves()
        return random.choice(moves)

    def ai_greedy_move(self, player):
        moves = self.board.legal_moves()
        best_score = -10**9
        best_moves = []
        for x, y in moves:
            score = self.evaluate_move(player, x, y)
            if score > best_score:
                best_score = score
                best_moves = [(x, y)]
            elif score == best_score:
                best_moves.append((x, y))
        return random.choice(best_moves)

    def ai_hard_move(self, player):
        moves = self.board.legal_moves()
        scored = []
        for x, y in moves:
            scored.append((self.evaluate_move(player, x, y), x, y))
        scored.sort(reverse=True, key=lambda item: item[0])
        candidates = scored[:min(10, len(scored))]
        best_move = None
        best_value = -10**9
        for score, x, y in candidates:
            value = score - self.estimate_opponent_response(player, x, y)
            if value > best_value:
                best_value = value
                best_move = (x, y)
        return best_move if best_move else random.choice(moves)

    def estimate_opponent_response(self, player, x, y):
        opponent = 3 - player
        board_clone = self.board.clone()
        board_clone.set(x, y, player)
        best = -10**9
        for ox, oy in board_clone.legal_moves():
            score = self.evaluate_move_on_board(opponent, ox, oy, board_clone)
            if score > best:
                best = score
        return best if best != -10**9 else 0

    def select_ai_replacement(self, player):
        opponent = 3 - player
        candidates = [(x, y) for y in range(self.size) for x in range(self.size) if self.board.get(x, y) == opponent]
        if not candidates:
            return None
        if self.ai_levels[player] == 'simple':
            return random.choice(candidates)
        best_score = -10**9
        best_moves = []
        for x, y in candidates:
            score = self.evaluate_move(player, x, y, replacement=True)
            if score > best_score:
                best_score = score
                best_moves = [(x, y)]
            elif score == best_score:
                best_moves.append((x, y))
        return random.choice(best_moves)

    def evaluate_move(self, player, x, y, replacement=False):
        board_clone = self.board.clone()
        if replacement:
            board_clone.set(x, y, player)
        else:
            if not board_clone.is_empty(x, y):
                return -10**9
            board_clone.set(x, y, player)
        return self.evaluate_board(player, board_clone) - self.evaluate_board(3 - player, board_clone)

    def evaluate_move_on_board(self, player, x, y, board):
        if not board.is_empty(x, y):
            return -10**9
        board_clone = board.clone()
        board_clone.set(x, y, player)
        return self.evaluate_board(player, board_clone)

    def evaluate_board(self, player, board):
        score = 0
        for y in range(self.size):
            for x in range(self.size):
                if board.get(x, y) == 0:
                    score += self.evaluate_potential(player, x, y, board)
        return score

    def evaluate_potential(self, player, x, y, board):
        total = 0
        for dx, dy in DIRECTIONS:
            total += self.evaluate_direction(player, x, y, dx, dy, board)
        return total

    def evaluate_direction(self, player, x, y, dx, dy, board):
        count = 0
        open_ends = 0
        for direction in (1, -1):
            step = 1
            while True:
                cx, cy = x + dx * step * direction, y + dy * step * direction
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
        return self.pattern_score(count, open_ends)

    def pattern_score(self, count, open_ends):
        if count >= 4 and open_ends >= 1:
            return 10000
        if count == 3 and open_ends == 2:
            return 800
        if count == 3 and open_ends == 1:
            return 200
        if count == 2 and open_ends == 2:
            return 50
        if count == 2 and open_ends == 1:
            return 10
        if count == 1 and open_ends == 2:
            return 5
        return 1 if count == 1 and open_ends == 1 else 0
