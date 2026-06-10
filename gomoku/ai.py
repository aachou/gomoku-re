import random
from typing import List, Tuple

from .board import Board, DIRECTIONS

AI_LEVELS = ['simple', 'medium', 'hard']


def select_ai_move(board: Board, player: int, level: str) -> Tuple[int, int]:
    if level == 'simple':
        return _random_move(board)
    if level == 'medium':
        return _greedy_move(board, player)
    return _hard_move(board, player)


def _random_move(board: Board) -> Tuple[int, int]:
    moves = board.legal_moves()
    return random.choice(moves)


def _greedy_move(board: Board, player: int) -> Tuple[int, int]:
    moves = board.legal_moves()
    best_score = -10**9
    best_moves: List[Tuple[int, int]] = []
    for x, y in moves:
        score = evaluate_move(board, player, x, y)
        if score > best_score:
            best_score = score
            best_moves = [(x, y)]
        elif score == best_score:
            best_moves.append((x, y))
    return random.choice(best_moves)


def _hard_move(board: Board, player: int) -> Tuple[int, int]:
    moves = board.legal_moves()
    scored = []
    for x, y in moves:
        scored.append((evaluate_move(board, player, x, y), x, y))
    scored.sort(reverse=True, key=lambda item: item[0])
    candidates = scored[:min(10, len(scored))]
    best_move = None
    best_value = -10**9
    for score, x, y in candidates:
        value = score - _estimate_opponent_response(board, player, x, y)
        if value > best_value:
            best_value = value
            best_move = (x, y)
    return best_move if best_move else random.choice(moves)


def _estimate_opponent_response(board: Board, player: int, x: int, y: int) -> int:
    opponent = 3 - player
    board_clone = board.clone()
    board_clone.set(x, y, player)
    best = -10**9
    for ox, oy in board_clone.legal_moves():
        score = evaluate_move_on_board(opponent, ox, oy, board_clone)
        if score > best:
            best = score
    return best if best != -10**9 else 0


def select_ai_replacement(board: Board, player: int, level: str):
    opponent = 3 - player
    candidates = [(x, y) for y in range(board.size) for x in range(board.size) if board.get(x, y) == opponent]
    if not candidates:
        return None
    if level == 'simple':
        return random.choice(candidates)
    best_score = -10**9
    best_moves = []
    for x, y in candidates:
        score = evaluate_move(board, player, x, y, replacement=True)
        if score > best_score:
            best_score = score
            best_moves = [(x, y)]
        elif score == best_score:
            best_moves.append((x, y))
    return random.choice(best_moves)


def evaluate_move(board: Board, player: int, x: int, y: int, replacement=False) -> int:
    board_clone = board.clone()
    if replacement:
        board_clone.set(x, y, player)
    else:
        if not board_clone.is_empty(x, y):
            return -10**9
        board_clone.set(x, y, player)
    return evaluate_board(board_clone, player) - evaluate_board(board_clone, 3 - player)


def evaluate_move_on_board(player: int, x: int, y: int, board: Board) -> int:
    if not board.is_empty(x, y):
        return -10**9
    board_clone = board.clone()
    board_clone.set(x, y, player)
    return evaluate_board(board_clone, player)


def evaluate_board(board: Board, player: int) -> int:
    score = 0
    checked = set()
    for y in range(board.size):
        for x in range(board.size):
            if board.get(x, y) != 0:
                for dy in range(-4, 5):
                    for dx in range(-4, 5):
                        nx, ny = x + dx, y + dy
                        if board.in_bounds(nx, ny) and board.is_empty(nx, ny) and (nx, ny) not in checked:
                            checked.add((nx, ny))
                            score += evaluate_potential(player, nx, ny, board)
    if not checked:
        cx, cy = board.size // 2, board.size // 2
        if board.is_empty(cx, cy):
            score += evaluate_potential(player, cx, cy, board)
    return score


def evaluate_potential(player: int, x: int, y: int, board: Board) -> int:
    total = 0
    for dx, dy in DIRECTIONS:
        total += evaluate_direction(player, x, y, dx, dy, board)
    return total


def evaluate_direction(player: int, x: int, y: int, dx: int, dy: int, board: Board) -> int:
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
    return pattern_score(count, open_ends)


def pattern_score(count: int, open_ends: int) -> int:
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
