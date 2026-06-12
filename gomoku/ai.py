import random
from typing import List, Optional, Tuple

from .board import (
    Board, DIRECTIONS,
    _evaluate_potential, _would_form_five,
)

AI_LEVELS = ['simple', 'medium', 'hard']


def select_ai_move(board: Board, player: int, level: str) -> Optional[Tuple[int, int]]:
    if not board.legal_moves():
        return None
    if level == 'simple':
        return _simple_move(board, player)
    if level == 'medium':
        return _medium_move(board, player)
    return _hard_move(board, player, level)


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


def _get_candidate_moves(board: Board) -> List[Tuple[int, int]]:
    if not board._player_cells[1] and not board._player_cells[2]:
        return board.legal_moves()
    interesting = set()
    for cells in board._player_cells.values():
        for x, y in cells:
            for dx in range(-2, 3):
                nx = x + dx
                if nx < 0 or nx >= board.size:
                    continue
                for dy in range(-2, 3):
                    ny = y + dy
                    if ny < 0 or ny >= board.size:
                        continue
                    if board.grid[ny][nx] == 0:
                        interesting.add((nx, ny))
    if not interesting:
        return board.legal_moves()
    return list(interesting)


def _score_all_moves(board: Board, player: int) -> List[Tuple[float, int, int]]:
    opponent = 3 - player
    opp_has_five_now = board.has_immediate_five(opponent)
    scored = []
    for x, y in _get_candidate_moves(board):
        score = _light_score(board, player, x, y)
        if opp_has_five_now and _would_form_five(board, opponent, x, y):
            score += 50000
        elif not opp_has_five_now and _would_form_five(board, player, x, y):
            return [(100000, x, y)]
        scored.append((score, x, y))
    scored.sort(reverse=True, key=lambda p: p[0])
    return scored


def _medium_move(board: Board, player: int) -> Tuple[int, int]:
    scored = _score_all_moves(board, player)
    if not scored:
        return None
    best_score = scored[0][0]
    best = [(x, y) for s, x, y in scored if s == best_score]
    return random.choice(best)


def _evaluate_board(board: Board, player: int) -> float:
    opponent = 3 - player
    atk = board._board_potential[player]
    dfs = board._board_potential[opponent]
    score = atk * 1.1 - dfs * 1.2
    if board.has_immediate_five(player):
        score += 100000
    if board.has_immediate_five(opponent):
        score -= 100000
    return score


def _alpha_beta(board: Board, player: int, depth: int, alpha: float, beta: float,
                level: str, ai_player: int) -> float:
    if board.has_immediate_five(player):
        return (100000 if player == ai_player else -100000) + depth * 1000

    if depth == 0:
        return _evaluate_board(board, ai_player)

    scored = _score_all_moves(board, player)
    if not scored:
        return _evaluate_board(board, ai_player)

    next_player = 3 - player

    if player == ai_player:
        value = -10**9
        for _, x, y in scored[:10]:
            sim = _simulate_placement(board, player, x, y, level)
            v = _alpha_beta(sim, next_player, depth - 1, alpha, beta, level, ai_player)
            if v > value:
                value = v
            if value >= beta:
                return value
            if value > alpha:
                alpha = value
        return value
    else:
        value = 10**9
        for _, x, y in scored[:8]:
            sim = _simulate_placement(board, player, x, y, level)
            v = _alpha_beta(sim, next_player, depth - 1, alpha, beta, level, ai_player)
            if v < value:
                value = v
            if value <= alpha:
                return value
            if value < beta:
                beta = value
        return value


def _hard_move(board: Board, player: int, level: str = 'hard') -> Tuple[int, int]:
    scored = _score_all_moves(board, player)
    if not scored:
        return None
    candidates = scored[:min(10, len(scored))]
    best_move = (candidates[0][1], candidates[0][2])
    best_value = -10**9

    for _, x, y in candidates:
        sim = _simulate_placement(board, player, x, y, level)
        if sim.has_immediate_five(player):
            return (x, y)

        v = _alpha_beta(sim, 3 - player, 1, -10**9, 10**9, level, player)
        if v > best_value:
            best_value = v
            best_move = (x, y)

    return best_move


def _simulate_placement(board: Board, player: int, x: int, y: int, level: str) -> Board:
    clone = board.clone()
    clone.set(x, y, player)
    opponent = 3 - player

    cx, cy = x, y
    for _ in range(3):
        line = clone.find_connected_line(cx, cy, player)
        if not line:
            break
        clone.remove_line(line)
        rep = select_ai_replacement(clone, player, level, quick=True)
        if rep is None:
            break
        rx, ry = rep
        clone.set(rx, ry, player)
        cx, cy = rx, ry
    return clone


def select_ai_replacement(board: Board, player: int, level: str, quick: bool = False):
    opponent = 3 - player
    candidates = list(board._player_cells[opponent])
    if not candidates:
        return None
    if level == 'simple':
        return random.choice(candidates)

    if quick:
        best_score = -10**9
        best = None
        for x, y in candidates:
            our_val = _evaluate_potential(player, x, y, board)
            opp_val = _evaluate_potential(opponent, x, y, board)
            plus = 100000 if _would_form_five(board, player, x, y) else 0
            minus = 100000 if _would_form_five(board, opponent, x, y) else 0
            score = our_val * 1.5 + opp_val + plus - minus
            if score > best_score:
                best_score = score
                best = (x, y)
        return best

    best_score = -10**9
    best_moves = []

    opp_has_five = board.has_immediate_five(opponent)

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
            if not clone.has_immediate_five(opponent):
                opp_loss += 50000

        if clone is None:
            clone = board.clone()
            clone.set(x, y, player)

        board_score = clone._board_potential[player] - clone._board_potential[opponent]
        score = our_gain * 1.5 + opp_loss + board_score * 0.5

        if score > best_score:
            best_score = score
            best_moves = [(x, y)]
        elif score == best_score:
            best_moves.append((x, y))

    return random.choice(best_moves)
