# AGENTS.md

## Commands

- `uv run python main.py` — launch GUI (tkinter required; auto-fallback to CLI)
- `uv run python main.py cli` — force CLI mode
- `uv run pytest` — run all 80 tests
- `python -m pytest tests/test_file.py::TestClass::test_method` — single test
- `uv lock` — sync lockfile after dependency changes

## Architecture

- `main.py` — entry point, sole top-level module; imports `Game` and `GameUI` from `gomoku`
- `gomoku/` — internal package
  - `board.py` — `Board` (N×N grid: 0=empty, 1=black, 2=white), incremental evaluation cache, line scanning
  - `game.py` — `Game`, `PlacementResult`, config/stats persistence, undo history, JSON serialization
  - `ai.py` — 3 difficulty levels; `select_ai_replacement(quick=True)` for simulation
  - `cli.py` — interactive CLI; coordinate parse (A1 or `1 1`)
  - `ui.py` — tkinter GUI; conditionally defined as `GameUI = None` when tkinter absent
- `tests/` — unittest-based, no plugins needed

## Key facts

- Board grid is `grid[y][x]`, values 0/1/2
- Coordinates: 0-indexed internally, 1-indexed in user I/O (`A1` or `1 1`)
- `find_connected_line()` returns exactly 5 coords or `None`
- CLI (`_handle_line_loop`) and GUI (`perform_placement`/`conclude_turn`) are **separate implementations** of the same turn logic
- `Game.do_placement(x, y)` and `Game.do_replacement(x, y)` encapsulate action + log + process
- Board has `has_immediate_five(player)` lazy cache (`_five_threat_cache`), invalidated on every `set()`
- `_rebuild_cache()` must be called after manually mutating `grid` or after undo
- `Game.save_snapshot()` now tracks `move_log_len` — undo pops all entries since snapshot
- `select_ai_move()` returns `Optional[Tuple[int, int]]` — returns `None` when no legal moves
- Supply starts at 30 per player; AI delay defaults to 300ms
- No external dependencies (pure stdlib)

## CLI quirks

- `save` in `_handle_command` returns `''` (not `None`) — otherwise input loops fall through to coordinate parsing and print "坐标格式错误"
- Special commands: `undo`, `save`, `load`, `quit`
- `quit` returns `'quit'`, `undo`/`load` return `'refresh'`, `save` returns `''`
- `input_replacement` returns `(-1, -1)` on undo/load (sentinel to abort replacement chain)

## Persisted files

- `gomoku_config.json` — `ai_level`, `board_size`, `starting_stones`, `ai_delay_ms`, `theme`
- `gomoku_save.json` — full game state (via `Game.serialize()`)
- `gomoku_stats.json` — `total_games`, `wins`, `draws`, `moves`, `recoveries`, `total_time`

## Notable pitfalls

- `GameUI` is conditionally defined; `from .ui import GameUI` at module level fails if tkinter absent — handled via `GameUI = None`
- `_rebuild_cache()` must be called after manually mutating `grid` or after undo
- `Board.clone()` does shallow copy of `_cell_potential` (list of ints — safe for this use)
- `select_ai_replacement(quick=True)` is the lightweight version inside simulation; `quick=False` (default) in actual play
- `_simulate_placement` passes `level` to `select_ai_replacement` for consistent replacement logic
- `Game.serialize()` includes `timers` and `history` for full save/load fidelity
- `withdraw()`/`deiconify()` in `GameUI.__init__` eliminates window flash on startup
