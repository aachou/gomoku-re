import random
from typing import List, Optional, Tuple

from .board import Board, DIRECTIONS

AI_LEVELS = ['simple', 'medium', 'hard']

_SCORE_TABLE = {
    (5, 0): 200000, (5, 1): 200000, (5, 2): 200000,
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


def select_ai_move(board: Board, player: int, level: str) -> Tuple[int, int]:
    if level == 'simple':
        return _simple_move(board, player)
    if level == 'medium':
        return _medium_move(board, player)
    return _hard_move(board, player)


def _simple_move(board: Board, player: int) -> Tuple[int, int]:
    moves = board.legal_moves()
    cx, cy = board.size // 2, board.size // 2
    scored = []
    for x, y in moves:
        near = any(
            board.in_bounds(x + dx, y + dy) and not board.is_empty(x + dx, y + dy)
            for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx != 0 or dy != 0
        )
        center = -(abs(x - cx) + abs(y - cy)) // 2
        bonus = center + (10 if near else 0) + random.randint(0, 10)
        scored.append((bonus, x, y))
    scored.sort(reverse=True, key=lambda p: p[0])
    return (scored[0][1], scored[0][2])


def _light_score(board: Board, player: int, x: int, y: int) -> int:
    opponent = 3 - player
    atk = _evaluate_potential(player, x, y, board)
    dfs = _evaluate_potential(opponent, x, y, board)
    score = atk * 1.2 + dfs
    if _would_form_five(board, player, x, y):
        score += 50000
    return score


def _medium_move(board: Board, player: int) -> Tuple[int, int]:
    opponent = 3 - player
    moves = board.legal_moves()
    opp_has_five_now = _has_immediate_five(board, opponent)

    best_score = -10**9
    best_moves: List[Tuple[int, int]] = []
    for x, y in moves:
        score = _light_score(board, player, x, y)
        if opp_has_five_now and _would_form_five(board, opponent, x, y):
            score += 50000
        if score > best_score:
            best_score = score
            best_moves = [(x, y)]
        elif score == best_score:
            best_moves.append((x, y))
    return random.choice(best_moves)


def _hard_move(board: Board, player: int) -> Tuple[int, int]:
    opponent = 3 - player
    moves = board.legal_moves()
    opp_has_five_now = _has_immediate_five(board, opponent)

    scored = []
    for x, y in moves:
        score = _light_score(board, player, x, y)
        if opp_has_five_now and _would_form_five(board, opponent, x, y):
            score += 50000
        scored.append((score, x, y))
    scored.sort(reverse=True, key=lambda p: p[0])

    candidates = scored[:min(30, len(scored))]
    best_move = (candidates[0][1], candidates[0][2])
    best_value = -10**9

    for _, x, y in candidates:
        sim = _simulate_placement(board, player, x, y)
        atk = _evaluate_board(sim, player)
        dfs = _evaluate_board(sim, opponent)

        value = atk * 1.1 - dfs * 1.2
        if _has_immediate_five(sim, opponent):
            value -= 50000
        if _has_immediate_five(sim, player):
            value += 100000

        if value > best_value:
            best_value = value
            best_move = (x, y)

    return best_move


def _simulate_placement(board: Board, player: int, x: int, y: int) -> Board:
    clone = board.clone()
    clone.set(x, y, player)
    opponent = 3 - player

    cx, cy = x, y
    for _ in range(3):
        line = clone.find_connected_line(cx, cy, player)
        if not line:
            break
        clone.remove_line(line)
        rep = _quick_pick_replacement(clone, player, opponent)
        if rep is None:
            break
        rx, ry = rep
        clone.set(rx, ry, player)
        cx, cy = rx, ry
    return clone


def _quick_pick_replacement(board: Board, player: int, opponent: int) -> Optional[Tuple[int, int]]:
    best_score = -10**9
    best = None
    for y in range(board.size):
        for x in range(board.size):
            if board.get(x, y) != opponent:
                continue
            our_val = _evaluate_potential(player, x, y, board)
            opp_val = _evaluate_potential(opponent, x, y, board)
            plus = 100000 if _would_form_five(board, player, x, y) else 0
            minus = 100000 if _would_form_five(board, opponent, x, y) else 0
            score = our_val * 1.5 + opp_val + plus - minus
            if score > best_score:
                best_score = score
                best = (x, y)
    return best


def _consecutive_count(board: Board, x: int, y: int, dx: int, dy: int, player: int) -> int:
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


def _would_form_five(board: Board, player: int, x: int, y: int) -> bool:
    return any(_consecutive_count(board, x, y, dx, dy, player) >= 4 for dx, dy in DIRECTIONS)


def _has_immediate_five(board: Board, player: int) -> bool:
    return any(_would_form_five(board, player, x, y) for x, y in board._empty_cells)


def select_ai_replacement(board: Board, player: int, level: str):
    opponent = 3 - player
    candidates = [(x, y) for y in range(board.size) for x in range(board.size)
                  if board.get(x, y) == opponent]
    if not candidates:
        return None
    if level == 'simple':
        return random.choice(candidates)

    best_score = -10**9
    best_moves = []

    opp_has_five = _has_immediate_five(board, opponent)

    for x, y in candidates:
        our_gain = _evaluate_potential(player, x, y, board)
        opp_loss = _evaluate_potential(opponent, x, y, board)

        our_forms_five = _would_form_five(board, player, x, y)
        if our_forms_five:
            our_gain += 50000

        clone = None
        if opp_has_five:
            clone = board.clone()
            clone.set(x, y, player)
            if not _has_immediate_five(clone, opponent):
                opp_loss += 50000

        if clone is None:
            clone = board.clone()
            clone.set(x, y, player)

        board_score = _evaluate_board(clone, player) - _evaluate_board(clone, opponent)
        score = our_gain * 1.5 + opp_loss + board_score * 0.5

        if score > best_score:
            best_score = score
            best_moves = [(x, y)]
        elif score == best_score:
            best_moves.append((x, y))

    return random.choice(best_moves)


def _evaluate_board(board: Board, player: int) -> int:
    score = 0
    for x, y in board._empty_cells:
        score += _evaluate_potential(player, x, y, board)
    return score


def _evaluate_potential(player: int, x: int, y: int, board: Board) -> int:
    total = 0
    for dx, dy in DIRECTIONS:
        total += _evaluate_direction(player, x, y, dx, dy, board)
    return total


def _evaluate_direction(player: int, x: int, y: int, dx: int, dy: int, board: Board) -> int:
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


def _pattern_score(count: int, open_ends: int) -> int:
    c = min(count, 5)
    o = min(open_ends, 2)
    return _SCORE_TABLE.get((c, o), 0)
