from typing import Optional, Tuple

from .ai import select_ai_move, select_ai_replacement
from .game import Game, PLAYER_NAMES, STARTING_STONES
from .board import BOARD_SIZE


def setup(game: Game):
    print('=== 不一样的五子棋 ===')
    print('规则: 先连成五颗棋子不立即获胜，而是回收这条连线，并用一颗棋子替换对方棋子。')
    print('先把棋子下完的一方判负。')
    print('支持人机对战，AI 具有简单、中等、困难三个难度。')
    print()

    mode = choose_option('请选择对战模式：1) 双人 2) 人机', ['1', '2'])
    if mode == '2':
        side = choose_option('请选择你执哪一方：1) 黑棋 2) 白棋', ['1', '2'])
        ai_player = 2 if side == '1' else 1
        game.player_types[int(side)] = 'human'
        game.player_types[ai_player] = 'ai'
        level = choose_option('请选择 AI 难度：1) 简单 2) 中等 3) 困难', ['1', '2', '3'])
        game.ai_levels[ai_player] = ['simple', 'medium', 'hard'][int(level) - 1]
    else:
        game.player_types[1] = 'human'
        game.player_types[2] = 'human'

    try:
        raw = input(f'初始每方棋子数量（回车默认 {game.supply[1]}）: ').strip()
        if raw:
            val = int(raw)
            if val > 0:
                game.supply = {1: val, 2: val}
    except Exception:
        pass

    try:
        raw_size = input(f'棋盘大小（回车默认 {game.board.size}）: ').strip()
        if raw_size:
            b = int(raw_size)
            if 5 <= b <= 99:
                from .board import Board
                game.board = Board(b)
                game.size = b
    except Exception:
        pass

    print(f'初始每方棋子数量：{game.supply[1]}')
    print('输入格式: A1 或 1 1')
    print()


def choose_option(prompt: str, choices):
    while True:
        answer = input(prompt + ' > ').strip()
        if answer in choices:
            return answer
        print('无效输入，请重新输入。')


def parse_coordinate(raw: str, board) -> Optional[Tuple[int, int]]:
    raw = raw.strip().upper()
    if not raw:
        return None
    if raw[0].isalpha():
        col = ord(raw[0]) - ord('A')
        row_text = raw[1:]
        if not row_text.isdigit():
            return None
        row = int(row_text) - 1
        return (col, row) if board.in_bounds(col, row) else None
    parts = raw.split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        x = int(parts[0]) - 1
        y = int(parts[1]) - 1
        return (x, y) if board.in_bounds(x, y) else None
    return None


def input_move(game: Game) -> Tuple[int, int]:
    while True:
        raw = input(f'{PLAYER_NAMES[game.current]} 请输入落子坐标: ').strip()
        coord = parse_coordinate(raw, game.board)
        if coord is None:
            print('坐标格式错误，请使用 A1 或 1 1')
            continue
        x, y = coord
        if not game.board.is_empty(x, y):
            print('该位置已有棋子，请选择空位。')
            continue
        return x, y


def input_replacement(game: Game) -> Tuple[int, int]:
    while True:
        raw = input(f'{PLAYER_NAMES[game.current]} 请输入想替换的对方棋子坐标: ').strip()
        coord = parse_coordinate(raw, game.board)
        if coord is None:
            print('坐标格式错误，请使用 A1 或 1 1')
            continue
        x, y = coord
        if game.board.get(x, y) != 3 - game.current:
            print('请选择对方的棋子位置。')
            continue
        return x, y


def _handle_line_loop(game: Game, x: int, y: int) -> bool:
    game.board.set(x, y, game.current)
    game._deduct_supply(game.current)
    while True:
        result, _, can_replace = game.process_stone_placement(x, y)
        if result == 'no_line':
            break
        if not can_replace:
            break
        if game.player_types[game.current] == 'human':
            rep = input_replacement(game)
        else:
            rep = select_ai_replacement(game.board, game.current, game.ai_levels[game.current])
        if rep is None:
            break
        rx, ry = rep
        game.apply_replacement(rx, ry)
        x, y = rx, ry
    return not game.has_lost(game.current)


def play(game: Game):
    setup(game)
    while True:
        if game.has_lost(game.current):
            print(f'{PLAYER_NAMES[game.current]} 棋子用完，{PLAYER_NAMES[game.opponent()]} 获胜！')
            break

        game.board.render()
        print(f'{PLAYER_NAMES[1]}：{game.supply[1]} 颗棋子    {PLAYER_NAMES[2]}：{game.supply[2]} 颗棋子')

        if game.player_types[game.current] == 'human':
            x, y = input_move(game)
        else:
            x, y = select_ai_move(game.board, game.current, game.ai_levels[game.current])
            print(f'AI({game.ai_levels[game.current]}) 选择 {chr(ord("A") + x)}{y + 1}')

        print(f'{PLAYER_NAMES[game.current]} 放置棋子: {chr(ord("A") + x)}{y + 1}')
        _handle_line_loop(game, x, y)

        if game.has_lost(game.current):
            print(f'{PLAYER_NAMES[game.current]} 棋子用完，{PLAYER_NAMES[game.opponent()]} 获胜！')
            break

        game.current = game.opponent()
