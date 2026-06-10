# AGENTS.md

## Project overview

Gomoku variant ("不一样的五子棋") — 5-in-a-row does not win, instead the 5 stones are recovered and one opponent stone is replaced. Running out of stones = loss.

## Commands

- `uv run python main.py` — launch GUI (tkinter required; auto-fallback to CLI if unavailable)
- `uv run python main.py cli` — force CLI mode
- `uv run pytest` — run all tests (unittest-based, 65 tests)
- `python -m pytest tests/test_file.py::TestClass::test_method` — run a single test
- `uv lock` — sync lockfile after dependency changes

## Architecture

- `main.py` — entry point, sole top-level module
- `gomoku/` — internal package
  - `board.py` — Board (15×15 grid: 0=empty, 1=black, 2=white), incremental evaluation cache, line scanning
  - `game.py` — Game, PlacementResult, config persistence (`gomoku_config.json`), undo history, JSON serialization
  - `ai.py` — 3 difficulty levels (`simple`/`medium`/`hard`); `_score_all_moves` early-returns on winning move; `select_ai_replacement(quick=True)` for simulation
  - `cli.py` — interactive CLI, save/load (`gomoku_save.json`), coordinate parse (A1 or `1 1`)
  - `ui.py` — tkinter GUI; Ctrl+S/L save/load, Esc/菜单确认弹窗, 对局统计, AI等级提示, 高亮缓存, _restart_game, _layout_changed两遍法, 默认1200x800+min900x640+_center_window, 主菜单bind_all全局滚轮, _start_canvas生命周期, _on_close自动存档, 主菜单继续上次游戏; `GameUI = None` if tkinter missing
- `tests/` — unittest, no pytest plugins needed

## Game quirks

- Board values are 0/1/2 (empty/black/white), accessed as `grid[y][x]`
- Coordinates: 0-indexed internally, `A1` or `1 1` (1-indexed) in user I/O
- `find_connected_line()` returns exactly 5 coords or None
- `_handle_line_loop` (cli.py) and `perform_placement`/`conclude_turn` (ui.py) are **separate implementations** of the same turn logic
- `Game.do_placement(x, y)` and `Game.do_replacement(x, y)` encapsulate action+log+process; used by GUI but CLI separates render between steps
- Board has `has_immediate_five(player)` lazy cache (`_five_threat_cache`), invalidated on every `set()`; used by AI
- Undo calls `_rebuild_cache()` to reconstruct Board's incremental cache and threat cache
- Supply starts at 30 per player; AI delay defaults to 300ms
- No external dependencies (pure stdlib)
- Config (`gomoku_config.json`) persists: `ai_level`, `board_size`, `starting_stones`, `ai_delay_ms`, `theme`
- UI themes: 3 presets (`默认`/`森林`/`暖阳`) in `THEMES` dict (`ui.py:16`); hotkey hints toggle with `?`

## Notable pitfalls

- `GameUI` is conditionally defined (only when tkinter is importable); `from .ui import GameUI` in `__init__.py` will fail at module level if tkinter absent — handled via `GameUI = None`
- `_rebuild_cache()` must be called after manually mutating `grid` or after undo
- `Board.clone()` is used in AI hard mode simulation; does a shallow copy of `_cell_potential` values (list copies are sufficient since they contain ints)
- `select_ai_replacement(..., quick=True)` is the lightweight version used inside simulation (no cloning); `quick=False` (default) is the full version used in actual play
- `_simulate_placement` now passes `level` to `select_ai_replacement` for consistent replacement logic in simulation
- `Game.serialize()` includes `timers` and `history` for full save/load fidelity
- Stats persisted in `gomoku_stats.json` (total_games, wins, draws, moves, recoveries, total_time); functions: `load_stats`, `save_stats`, `compute_game_stats` in `game.py`; UI via `_show_stats_dialog`/`_persist_game_stats` in `ui.py`
- CI: no CI workflow present currently
