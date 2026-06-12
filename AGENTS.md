# AGENTS.md

## Commands

- `uv run python main.py` — launch GUI (tkinter required; falls back to CLI)
- `uv run python main.py cli` — force CLI mode
- `uv run pytest` — run all 153 tests
- `uv run pytest tests/test_file.py::TestClass::test_method` — single test
- `uv lock` — sync lockfile after dependency changes

## Architecture

- `main.py` — sole entry point; conditionally launches `GameUI` (GUI) or `cli_play` (CLI)
- `gomoku/` — internal package
  - `board.py` — `Board` (N×N grid: 0=empty, 1=black, 2=white), incremental cache (`_cell_potential` 2D list of `[s1,s2]` or `None`, `_board_potential`, `_five_threat_cache`), line scanning
  - `game.py` — `Game`, `PlacementResult`, config/stats persistence, undo history (`_history` stack + `move_log_len`), JSON serialization, `do_placement`/`do_replacement` as canonical action+log+process wrappers, `_replay_snapshots` list for non-destructive replay
  - `ai.py` — 3 difficulty levels; `select_ai_replacement(quick=True)` for simulation; `_simulate_placement` passes `level` for consistent sub-simulation
  - `cli.py` — interactive CLI; coordinate parse (A1 or `1 1`); `_handle_line_loop` is one implementation of turn logic
  - `ui.py` — tkinter GUI (`GameUI`); `perform_placement`/`conclude_turn` is the other implementation of turn logic; conditionally defined — `GameUI = None` when tkinter absent. Features star points, ghost stone hover preview, and replay mode.
- `tests/` — unittest-based, no plugins needed, pure stdlib
- `__init__.py` re-exports `Game`, `GameUI`, `Board`, etc.

## Key facts

- Board grid is `grid[y][x]`, values 0/1/2. Coordinates: 0-indexed internally, 1-indexed in user I/O (`A1` or `1 1`).
- `find_connected_line()` returns exactly 5 coords or `None`. `scan_line()` returns all contiguous coords in one direction.
- `Board.set(x, y, value)` updates all caches and returns the old value. `_rebuild_cache()` must be called after manually mutating `grid` or after undo.
- `Board.clone()` does shallow copy of `_cell_potential` (list of ints — safe). `_cell_potential` is `N×N` 2D array of `[s1, s2]` or `None` (was dict before v1.6.2).
- `_score_all_moves` filters to cells within distance 2 of any stone (pruning ~80% of candidates).
- `has_immediate_five(player)` uses lazy `_five_threat_cache`, invalidated on every `set()`.
- Supply starts at 30 per player (configurable). AI delay defaults to 300ms.
- `select_ai_move()` returns `Optional[Tuple[int, int]]` — `None` when no legal moves.
- Themes: 默认, 森林, 暖阳 (3 themes).
- No external dependencies (pure stdlib). Requires Python ≥3.8.
- Star points: drawn for boards ≥15×15 at standard 9-star positions; uses `tags='grid'` so redrawn on layout change.
- Ghost stone: `_on_canvas_motion` shows semi-transparent (`stipple='gray25'`) stone at hovered empty cell; hidden during AI turn, replacement chain, or replay mode.
- Replay mode: `_enter_replay_mode()` saves live state via `serialize()`, then steps through `_replay_snapshots` using `restore_replay_snapshot`. Auto-play at 800ms interval. Exit restores live state and re-packs log listbox.

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
- `Game.serialize()` returns a copy of `board.grid` (not the mutable reference). `Game.deserialize()` calls `_rebuild_cache()`.
- `Game.save_snapshot()` tracks `move_log_len` — undo pops all entries since snapshot.
- CLI `_handle_line_loop` and GUI `perform_placement`/`perform_replacement` are separate implementations of replacement chain logic (CLI sync, GUI event-driven). Both now use `do_placement`/`do_replacement` and share the same game-logic path through `Game`. GUI extracts the common UI handling into `_after_placement`.
- `withdraw()`/`deiconify()` in `GameUI.__init__` eliminates window flash on startup.
- `_hard_move` passes `level` to `_simulate_placement`, which uses it for replacement logic consistency.
- `_hard_move` uses alpha-beta pruning (depth 2: our move → opponent's best response → evaluate). `_alpha_beta` checks `has_immediate_five(current_player)` for early termination.
- `_evaluate_board` uses `_board_potential` difference + immediate five bonuses (no supply tracking in simulation).
- `_replay_snapshots` stores grid snapshots after each `conclude_turn` (including game-over states). `restore_replay_snapshot` mutates `board.grid` directly and calls `_rebuild_cache()`. Replay exits by deserializing the saved `_live_state`.
- Ghost stone uses `tags='ghost'` and is removed at the start of `draw_board()`. Stone tag is `'stone'`, highlight is `'highlight'`, grid/star-points are `'grid'`.
