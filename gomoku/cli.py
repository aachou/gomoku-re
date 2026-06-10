import json
import os
import time
from typing import Optional, Tuple

from .ai import select_ai_move, select_ai_replacement
from .game import Game, PLAYER_NAMES, STARTING_STONES
from .board import Board, BOARD_SIZE

SAVE_FILE = os.path.join(os.path.dirname(__file__), '..', 'gomoku_save.json')


def setup(game: Game):
    print('=== 不一样的五子棋 ===')
    print('规则: 先连成五颗棋子不立即获胜，而是回收这条连线，并用一颗棋子替换对方棋子。')
    print('先把棋子下完的一方判负。')
    print()

    mode = choose_option('请选择模式：1) 双人 2) 人机 3) AI vs AI', ['1', '2', '3'])
    if mode == '2':
        side = choose_option('请选择你执哪一方：1) 黑棋 2) 白棋', ['1', '2'])
        ai_player = 2 if side == '1' else 1
        game.player_types[int(side)] = 'human'
        game.player_types[ai_player] = 'ai'
        level = choose_option('请选择 AI 难度：1) 简单 2) 中等 3) 困难', ['1', '2', '3'])
        game.ai_levels[ai_player] = ['simple', 'medium', 'hard'][int(level) - 1]
    elif mode == '3':
        game.player_types = {1: 'ai', 2: 'ai'}
        for p in (1, 2):
            level = choose_option(f'请选择 {PLAYER_NAMES[p]} AI 难度：1) 简单 2) 中等 3) 困难', ['1', '2', '3'])
            game.ai_levels[p] = ['simple', 'medium', 'hard'][int(level) - 1]
    else:
        game.player_types = {1: 'human', 2: 'human'}

    try:
        raw = input(f'初始每方棋子数量（回车默认 {game.supply[1]}）: ').strip()
        if raw:
            val = int(raw)
            if val > 0:
                game.supply[1] = game.supply[2] = val
    except Exception:
        pass

    try:
        raw_size = input(f'棋盘大小（回车默认 {game.board.size}）: ').strip()
        if raw_size:
            b = int(raw_size)
            if 5 <= b <= 99:
                game.board = Board(b)
                game.size = b
    except Exception:
        pass

    print(f'初始每方棋子数量：{game.supply[1]}')
    print('输入格式: A1 或 1 1')
    print('特殊命令: undo / save / load / quit')
    print()


def _load_game(game: Game) -> bool:
    try:
        with open(SAVE_FILE, 'r') as f:
            data = json.load(f)
        loaded = Game.deserialize(data)
        game.board = loaded.board
        game.size = loaded.size
        game.supply = loaded.supply
        game.current = loaded.current
        game.player_types = loaded.player_types
        game.ai_levels = loaded.ai_levels
        print('存档已加载。')
        return True
    except FileNotFoundError:
        print('没有找到存档。')
        return False
    except Exception as e:
        print(f'加载存档失败: {e}')
        return False


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


def _handle_command(raw: str, game: Game) -> Optional[str]:
    cmd = raw.strip().lower()
    if cmd == 'undo':
        if game.undo():
            print('已悔棋。')
            return 'refresh'
        print('没有可悔的棋。')
        return None
    if cmd == 'save':
        try:
            with open(SAVE_FILE, 'w') as f:
                json.dump(game.serialize(), f)
            print('已保存。')
        except Exception as e:
            print(f'保存失败: {e}')
        return None
    if cmd == 'load':
        _load_game(game)
        return 'refresh'
    if cmd == 'quit':
        return 'quit'
    return None


def input_move(game: Game) -> Optional[Tuple[int, int]]:
    while True:
        raw = input(f'{PLAYER_NAMES[game.current]} 请输入落子坐标: ').strip()
        result = _handle_command(raw, game)
        if result == 'quit':
            return None
        if result == 'refresh':
            game.board.render()
            print(f'{PLAYER_NAMES[1]}：{game.supply[1]} 颗    {PLAYER_NAMES[2]}：{game.supply[2]} 颗')
            continue
        if result is not None:
            continue
        coord = parse_coordinate(raw, game.board)
        if coord is None:
            print('坐标格式错误，请使用 A1 或 1 1')
            continue
        x, y = coord
        if not game.board.is_empty(x, y):
            print('该位置已有棋子，请选择空位。')
            continue
        return x, y


def input_replacement(game: Game) -> Optional[Tuple[int, int]]:
    while True:
        raw = input(f'{PLAYER_NAMES[game.current]} 请输入想替换的对方棋子坐标: ').strip()
        result = _handle_command(raw, game)
        if result == 'quit':
            return None
        if result == 'refresh':
            game.board.render()
            continue
        if result is not None:
            continue
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
    if not game.place_stone(x, y):
        return False
    game.board.render()
    print(f'{PLAYER_NAMES[game.current]} 放置棋子: {chr(ord("A") + x)}{y + 1}')
    while True:
        result, recovered, can_replace = game.process_stone_placement(x, y)
        if result == 'no_line':
            break
        print(f'{PLAYER_NAMES[game.current]} 连成五子，回收 {recovered} 颗棋子！')
        game.board.render()
        if not can_replace:
            print(f'{PLAYER_NAMES[game.current]} 没有可替换的对方棋子，回合结束。')
            break
        if game.player_types[game.current] == 'human':
            rep = input_replacement(game)
        else:
            rep = select_ai_replacement(game.board, game.current, game.ai_levels[game.current])
        if rep is None:
            break
        rx, ry = rep
        if not game.apply_replacement(rx, ry):
            break
        print(f'{PLAYER_NAMES[game.current]} 替换了 {chr(ord("A") + rx)}{ry + 1}')
        game.board.render()
        x, y = rx, ry
    return not game.has_lost(game.current)


def play(game: Game):
    setup(game)

    try:
        raw = input('是否加载存档？(y/N) ').strip().lower()
        if raw == 'y':
            _load_game(game)
    except Exception:
        pass

    while True:
        if game.has_lost(game.current):
            print(f'{PLAYER_NAMES[game.current]} 棋子用完，{PLAYER_NAMES[game.opponent()]} 获胜！')
            break

        game.board.render()
        print(f'{PLAYER_NAMES[1]}：{game.supply[1]} 颗    {PLAYER_NAMES[2]}：{game.supply[2]} 颗')

        if game.is_draw():
            print('棋盘已满，平局！')
            break

        game.save_snapshot()

        if game.player_types[game.current] == 'human':
            move = input_move(game)
            if move is None:
                print('游戏已退出。')
                return
            x, y = move
        else:
            if game.player_types[1] == 'ai' and game.player_types[2] == 'ai':
                time.sleep(0.3)
            x, y = select_ai_move(game.board, game.current, game.ai_levels[game.current])
            print(f'AI({game.ai_levels[game.current]}) 选择 {chr(ord("A") + x)}{y + 1}')

        _handle_line_loop(game, x, y)

        if game.has_lost(game.current):
            print(f'{PLAYER_NAMES[game.current]} 棋子用完，{PLAYER_NAMES[game.opponent()]} 获胜！')
            break

        game.current = game.opponent()
