# AGENTS.md

## Project overview

Gomoku variant ("不一样的五子棋") — 5-in-a-row does not win, instead the 5 stones are recovered and one opponent stone is replaced. Running out of stones = loss.

## Commands

- `python main.py` — launch GUI (tkinter required; auto-fallback to CLI if unavailable)
- `python main.py cli` — force CLI mode
- `pytest` — run all tests (unittest-based, 46 tests)

## Architecture

- `main.py` — entry point, sole top-level module
- `gomoku/` — internal package
  - `board.py` — Board (15×15 grid: 0=empty, 1=black, 2=white), incremental evaluation cache, line scanning
  - `game.py` — Game, PlacementResult, config persistence (`gomoku_config.json`), undo history, JSON serialization
  - `ai.py` — 3 difficulty levels (`simple`/`medium`/`hard`), separate `select_ai_move` and `select_ai_replacement`
  - `cli.py` — interactive CLI, save/load (`gomoku_save.json`), coordinate parse (A1 or `1 1`)
  - `ui.py` — tkinter GUI; `GameUI = None` if tkinter missing
- `tests/` — unittest, no pytest plugins needed

## Game quirks

- Board values are 0/1/2 (empty/black/white), accessed as `grid[y][x]`
- Coordinates: 0-indexed internally, `A1` or `1 1` (1-indexed) in user I/O
- `find_connected_line()` returns exactly 5 coords or None
- `_handle_line_loop` (cli.py) and `perform_placement`/`conclude_turn` (ui.py) are **separate implementations** of the same turn logic
- Undo calls `_rebuild_cache()` to reconstruct Board's incremental cache
- Supply starts at 30 per player; AI delay defaults to 300ms
- No external dependencies (pure stdlib)

## Notable pitfalls

- `GameUI` is conditionally defined (only when tkinter is importable); `from .ui import GameUI` in `__init__.py` will fail at module level if tkinter absent — handled via `GameUI = None`
- `_rebuild_cache()` must be called after manually mutating `grid` or after undo
- `Board.clone()` is used in AI hard mode simulation; does a shallow copy of `_cell_potential` values (list copies are sufficient since they contain ints)
- `_quick_pick_replacement` in ai.py is used inside simulation only; the public replacement function is `select_ai_replacement`
- CI: no CI workflow present currently
