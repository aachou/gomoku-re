# AGENTS.md

## Commands

- `uv run python main.py` — launch GUI (tkinter required; falls back to CLI)
- `uv run python main.py cli` — force CLI mode
- `uv run python -m pytest tests/` — run all tests
- `python -m pytest tests/test_file.py::TestClass::test_method` — single test
- `uv lock` — sync lockfile after dependency changes

## Architecture

- `main.py` — sole entry point; conditionally launches `GameUI` (GUI) or `cli_play` (CLI)
- `gomoku/` — internal package
  - `board.py` — `Board` (N×N grid: 0=empty, 1=black, 2=white), incremental cache (`_cell_potential`, `_board_potential`, `_five_threat_cache`), line scanning
  - `game.py` — `Game`, `PlacementResult`, config/stats persistence, undo history (`_history` stack + `move_log_len`), JSON serialization, `do_placement`/`do_replacement` as canonical action+log+process wrappers
  - `ai.py` — 3 difficulty levels; `select_ai_replacement(quick=True)` for simulation; `_simulate_placement` passes `level` for consistent sub-simulation
  - `cli.py` — interactive CLI; coordinate parse (A1 or `1 1`); `_handle_line_loop` is one implementation of turn logic
  - `ui.py` — tkinter GUI (`GameUI`); `perform_placement`/`conclude_turn` is the other implementation of turn logic; conditionally defined — `GameUI = None` when tkinter absent
- `tests/` — unittest-based, no plugins needed, pure stdlib
- `__init__.py` re-exports `Game`, `GameUI`, `Board`, etc.

## Key facts

- Board grid is `grid[y][x]`, values 0/1/2. Coordinates: 0-indexed internally, 1-indexed in user I/O (`A1` or `1 1`).
- `find_connected_line()` returns exactly 5 coords or `None`. `scan_line()` returns all contiguous coords in one direction.
- `Board.set(x, y, value)` updates all caches and returns the old value. `_rebuild_cache()` must be called after manually mutating `grid` or after undo.
- `Board.clone()` does shallow copy of `_cell_potential` (list of ints — safe).
- `has_immediate_five(player)` uses lazy `_five_threat_cache`, invalidated on every `set()`.
- Supply starts at 30 per player (configurable). AI delay defaults to 300ms.
- `select_ai_move()` returns `Optional[Tuple[int, int]]` — `None` when no legal moves.
- Themes: 默认, 森林, 暖阳 (3 themes).
- No external dependencies (pure stdlib). Requires Python ≥3.8.

## CLI quirks

- `_handle_command` returns: `'quit'` for quit, `'refresh'` for undo/load, `''` (not `None`) for save — otherwise falls through to coordinate parse and prints "坐标格式错误".
- `input_replacement` returns `(-1, -1)` on undo/load (sentinel to abort replacement chain).

## Persisted files

- `gomoku_config.json` — `ai_level`, `board_size`, `starting_stones`, `ai_delay_ms`, `theme` (all in `.gitignore`)
- `gomoku_save.json` — full game state via `Game.serialize()` (in `.gitignore`)
- `gomoku_stats.json` — cross-session stats (in `.gitignore`)
- All persisted files live at repo root, written with `json.dump` and caught exceptions silently.

## Notable pitfalls

- `GameUI` is conditionally defined; `from .ui import GameUI` at module level fails if tkinter absent — pattern is `from .ui import GameUI` in `__init__.py`, guarded by `GameUI = None`.
- `Game.serialize()` includes `timers` and `history` for full save/load fidelity; `Game.deserialize()` calls `_rebuild_cache()`.
- `Game.save_snapshot()` tracks `move_log_len` — undo pops all entries since snapshot.
- CLI `_handle_line_loop` and GUI `perform_placement`/`conclude_turn` are separate implementations with same logic — fixes must be applied to both.
- `withdraw()`/`deiconify()` in `GameUI.__init__` eliminates window flash on startup.
- `_hard_move` passes `level` to `_simulate_placement`, which uses it for replacement logic consistency.
