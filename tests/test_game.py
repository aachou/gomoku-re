import json
import unittest
from gomoku.game import Game, STARTING_STONES, PlacementResult


class TestGame(unittest.TestCase):
    def test_init(self):
        g = Game()
        self.assertEqual(g.supply[1], STARTING_STONES)
        self.assertEqual(g.supply[2], STARTING_STONES)
        self.assertEqual(g.current, 1)
        self.assertFalse(g.has_lost(1))

    def test_place_stone(self):
        g = Game()
        self.assertTrue(g.place_stone(7, 7))
        self.assertFalse(g.board.is_empty(7, 7))
        self.assertEqual(g.supply[1], STARTING_STONES - 1)

    def test_place_stone_no_supply(self):
        g = Game(starting_stones=1)
        g.place_stone(7, 7)
        self.assertFalse(g.place_stone(7, 8))

    def test_opponent(self):
        g = Game()
        self.assertEqual(g.opponent(), 2)
        g.current = 2
        self.assertEqual(g.opponent(), 1)

    def test_has_lost(self):
        g = Game(starting_stones=0)
        self.assertTrue(g.has_lost(1))
        self.assertTrue(g.has_lost(2))

    def test_replacement_is_available(self):
        g = Game()
        self.assertFalse(g.replacement_is_available())
        g.place_stone(7, 7)
        g.current = 2
        g.place_stone(7, 8)
        g.current = 1
        self.assertTrue(g.replacement_is_available())

    def test_apply_replacement(self):
        g = Game()
        g.place_stone(7, 7)
        g.current = 2
        g.place_stone(7, 8)
        g.current = 1
        self.assertTrue(g.apply_replacement(7, 8))
        self.assertEqual(g.board.get(7, 8), 1)
        self.assertEqual(g.supply[1], STARTING_STONES - 2)

    def test_apply_replacement_wrong_target(self):
        g = Game()
        self.assertFalse(g.apply_replacement(7, 7))

    def test_five_in_row_recovery(self):
        g = Game(size=15, starting_stones=30)
        for x in range(4):
            g.place_stone(x, 7)
        self.assertEqual(g.supply[1], 26)

        g.place_stone(4, 7)
        self.assertEqual(g.supply[1], 25)

        result = g.process_stone_placement(4, 7)
        self.assertEqual(result.result, 'recovered')
        self.assertEqual(result.recovered, 5)
        self.assertEqual(g.supply[1], 30)
        self.assertFalse(result.can_replace)

    def test_serialize_deserialize(self):
        g = Game(size=15, starting_stones=25)
        g.place_stone(7, 7)
        g.current = 2
        g.player_types[2] = 'ai'
        g.ai_levels[2] = 'medium'

        data = g.serialize()
        self.assertEqual(data['size'], 15)
        self.assertEqual(data['supply'], [24, 25])
        self.assertEqual(data['current'], 2)
        self.assertEqual(data['player_types'], ['human', 'ai'])
        self.assertEqual(data['ai_levels'], [None, 'medium'])
        self.assertEqual(data['grid'][7][7], 1)

        g2 = Game.deserialize(data)
        self.assertEqual(g2.board.get(7, 7), 1)
        self.assertEqual(g2.supply[1], 24)
        self.assertEqual(g2.supply[2], 25)
        self.assertEqual(g2.current, 2)
        self.assertEqual(g2.player_types[2], 'ai')
        self.assertEqual(g2.ai_levels[2], 'medium')
        self.assertEqual(len(g2.board._empty_cells), 224)

    def test_json_roundtrip(self):
        g = Game(size=15, starting_stones=20)
        g.place_stone(7, 7)
        g.place_stone(7, 8)
        g.current = 2

        data = g.serialize()
        json_str = json.dumps(data)
        restored = json.loads(json_str)
        g2 = Game.deserialize(restored)

        self.assertEqual(g2.board.get(7, 7), 1)
        self.assertEqual(g2.board.get(7, 8), 1)
        self.assertEqual(g2.supply[1], 18)
        self.assertEqual(g2.supply[2], 20)
        self.assertEqual(g2.current, 2)

    def test_undo(self):
        g = Game()
        g.save_snapshot()
        g.place_stone(7, 7)
        self.assertEqual(g.supply[1], STARTING_STONES - 1)
        self.assertTrue(g.undo())
        self.assertEqual(g.supply[1], STARTING_STONES)
        self.assertTrue(g.board.is_empty(7, 7))

    def test_undo_empty(self):
        g = Game()
        self.assertFalse(g.undo())

    def test_undo_multiple(self):
        g = Game()
        g.save_snapshot()
        g.place_stone(7, 7)
        g.current = 2
        g.save_snapshot()
        g.place_stone(7, 8)
        g.current = 1

        self.assertEqual(g.board.get(7, 7), 1)
        self.assertEqual(g.board.get(7, 8), 2)
        self.assertEqual(g.current, 1)

        self.assertTrue(g.undo())
        self.assertTrue(g.board.is_empty(7, 8))
        self.assertEqual(g.current, 2)
        self.assertEqual(g.board.get(7, 7), 1)

        self.assertTrue(g.undo())
        self.assertTrue(g.board.is_empty(7, 7))
        self.assertEqual(g.current, 1)

    def test_recovery_chain(self):
        g = Game(size=15, starting_stones=30)
        for x in range(4):
            g.place_stone(x, 0)
        g.current = 2
        for x in range(4):
            g.place_stone(x, 1)
        g.current = 1
        g.place_stone(4, 0)
        result = g.process_stone_placement(4, 0)
        self.assertEqual(result.result, 'recovered')
        self.assertEqual(result.recovered, 5)
        self.assertTrue(result.can_replace)
        self.assertEqual(g.supply[1], 30)
        self.assertTrue(g.apply_replacement(3, 1))
        self.assertEqual(g.supply[1], 29)
        r2 = g.process_stone_placement(3, 1)
        self.assertEqual(r2.result, 'no_line')

    def test_process_no_line(self):
        g = Game(size=15, starting_stones=30)
        g.place_stone(7, 7)
        result = g.process_stone_placement(7, 7)
        self.assertEqual(result.result, 'no_line')
        self.assertIsNone(result.recovered)
        self.assertFalse(result.can_replace)

    def test_is_draw_false(self):
        g = Game()
        self.assertFalse(g.is_draw())

    def test_is_draw_true(self):
        g = Game(size=5, starting_stones=25)
        g.supply = {1: 13, 2: 12}
        for y in range(5):
            for x in range(5):
                g.board.set(x, y, 1 if (x + y) % 2 == 0 else 2)
        g.board._rebuild_cache()
        self.assertTrue(g.is_draw())

    def test_undo_after_replacement(self):
        g = Game(starting_stones=30)
        g.place_stone(7, 7)
        g.current = 2
        g.place_stone(7, 8)
        g.current = 1
        g.save_snapshot()
        g.apply_replacement(7, 8)
        self.assertEqual(g.board.get(7, 8), 1)
        self.assertEqual(g.supply[1], 28)
        self.assertTrue(g.undo())
        self.assertEqual(g.board.get(7, 8), 2)
        self.assertEqual(g.supply[1], 29)

    def test_do_placement_normal(self):
        g = Game()
        result = g.do_placement(7, 7)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, 'no_line')
        self.assertIsNone(result.recovered)
        self.assertFalse(result.can_replace)
        self.assertEqual(g.supply[1], STARTING_STONES - 1)
        self.assertEqual(len(g.move_log), 1)
        self.assertEqual(g.move_log[0]['action'], 'place')

    def test_do_placement_no_supply(self):
        g = Game(starting_stones=0)
        result = g.do_placement(7, 7)
        self.assertIsNone(result)
        self.assertTrue(g.board.is_empty(7, 7))

    def test_do_placement_with_recovery(self):
        g = Game()
        for x in range(4):
            g.place_stone(x, 7)
        g.supply[1] = 30
        result = g.do_placement(4, 7)
        self.assertIsNotNone(result)
        self.assertEqual(result.result, 'recovered')
        self.assertEqual(result.recovered, 5)

    def test_do_replacement_normal(self):
        g = Game()
        g.place_stone(7, 7)
        g.current = 2
        g.place_stone(7, 8)
        g.current = 1
        result = g.do_replacement(7, 8)
        self.assertIsNotNone(result)
        self.assertEqual(g.board.get(7, 8), 1)
        self.assertEqual(g.supply[1], STARTING_STONES - 2)
        self.assertEqual(len(g.move_log), 1)

    def test_do_replacement_wrong_target(self):
        g = Game()
        result = g.do_replacement(7, 7)
        self.assertIsNone(result)

    def test_timers_in_serialize(self):
        g = Game()
        g.timers = {1: 12.5, 2: 8.3}
        data = g.serialize()
        self.assertEqual(data['timers'], [12.5, 8.3])

    def test_timers_restored_on_deserialize(self):
        g = Game()
        g.timers = {1: 30.0, 2: 15.5}
        data = g.serialize()
        g2 = Game.deserialize(data)
        self.assertEqual(g2.timers[1], 30.0)
        self.assertEqual(g2.timers[2], 15.5)

    def test_history_in_serialize(self):
        g = Game()
        g.save_snapshot()
        g.place_stone(7, 7)
        data = g.serialize()
        self.assertEqual(len(data['history']), 1)

    def test_history_restored_on_deserialize(self):
        g = Game()
        g.save_snapshot()
        g.place_stone(7, 7)
        data = g.serialize()
        g2 = Game.deserialize(data)
        self.assertTrue(g2.undo())
        self.assertTrue(g2.board.is_empty(7, 7))

    def test_move_log_stats(self):
        g = Game()
        g.do_placement(0, 0)
        g.current = 2
        g.do_placement(0, 1)
        g.current = 1
        b_moves = sum(1 for m in g.move_log if m['player'] == 1)
        w_moves = sum(1 for m in g.move_log if m['player'] == 2)
        total = len(g.move_log)
        self.assertEqual(total, 2)
        self.assertEqual(b_moves, 1)
        self.assertEqual(w_moves, 1)

    def test_compute_game_stats_winner(self):
        from gomoku.game import compute_game_stats
        g = Game()
        g.do_placement(0, 0)
        g.current = 2
        g.do_placement(0, 1)
        stats = compute_game_stats(g, 1)
        self.assertEqual(stats['wins'][1], 1)
        self.assertEqual(stats['wins'][2], 0)
        self.assertEqual(stats['draws'], 0)
        self.assertEqual(stats['moves'][1], 1)
        self.assertEqual(stats['moves'][2], 1)

    def test_compute_game_stats_draw(self):
        from gomoku.game import compute_game_stats
        g = Game()
        g.do_placement(0, 0)
        stats = compute_game_stats(g, None)
        self.assertEqual(stats['wins'][1], 0)
        self.assertEqual(stats['wins'][2], 0)
        self.assertEqual(stats['draws'], 1)

    def test_undo_with_multiple_log_entries(self):
        g = Game()
        g.do_placement(7, 7)
        g.current = 2
        g.do_placement(7, 8)
        g.current = 1
        g.save_snapshot()
        g.do_replacement(7, 8)
        self.assertEqual(len(g.move_log), 3)
        self.assertTrue(g.undo())
        self.assertEqual(len(g.move_log), 2)
        self.assertEqual(g.board.get(7, 7), 1)
        self.assertEqual(g.board.get(7, 8), 2)

    def test_serialize_empty(self):
        g = Game()
        data = g.serialize()
        g2 = Game.deserialize(data)
        self.assertEqual(g2.supply[1], STARTING_STONES)
        self.assertEqual(g2.current, 1)
        self.assertTrue(g2.board.is_empty(7, 7))
        self.assertEqual(len(g2.board.legal_moves()), 225)

    def test_is_draw_with_supply_exhaustion_and_full_board(self):
        g = Game(size=5, starting_stones=0)
        g.supply = {1: 0, 2: 0}
        for y in range(5):
            for x in range(5):
                g.board.set(x, y, 1 if (x + y) % 2 == 0 else 2)
        g.board._rebuild_cache()
        self.assertTrue(g.board.is_full())
        self.assertFalse(g.is_draw())

    def test_recovery_supply_correct(self):
        g = Game(starting_stones=5)
        for x in range(4):
            g.place_stone(x, 7)
        self.assertEqual(g.supply[1], 1)
        g.place_stone(4, 7)
        g.process_stone_placement(4, 7)
        self.assertEqual(g.supply[1], 5)

    def test_recovery_supply_overflow(self):
        g = Game(starting_stones=5)
        g.supply[1] = 10
        g.supply[2] = 10
        for x in range(5):
            g.board.set(x, 7, 1)
        g.board._rebuild_cache()
        g.board.set(0, 7, 0)
        g.board.set(0, 0, 2)
        g.board._rebuild_cache()
        g.place_stone(0, 7)
        g.process_stone_placement(0, 7)
        self.assertGreater(g.supply[1], 10)

    def test_complex_cache_coherence(self):
        from gomoku.board import Board
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        b.set(6, 7, 1)
        b.set(8, 7, 1)
        b.set(9, 7, 1)
        b.set(10, 7, 1)
        b.remove_line([(6, 7), (7, 7), (8, 7), (9, 7)])
        self.assertTrue(b.is_empty(7, 7))
        self.assertEqual(b._stone_count[1], 1)
        self.assertEqual(b._stone_count[2], 1)
        self.assertIn((7, 8), b._player_cells[2])

    def test_save_load_stats_corrupt_file(self):
        from gomoku.game import save_stats, load_stats, DEFAULT_STATS, STATS_FILE
        with open(STATS_FILE, 'w') as f:
            f.write('corrupt json')
        loaded = load_stats()
        self.assertEqual(loaded['total_games'], 0)
        self.assertEqual(loaded['wins'][1], 0)

    def test_save_load_stats(self):
        from gomoku.game import save_stats, load_stats, DEFAULT_STATS
        save_stats(DEFAULT_STATS)
        loaded = load_stats()
        self.assertEqual(loaded['total_games'], 0)
        self.assertEqual(loaded['wins'][1], 0)

    def test_replay_snapshots_empty_initially(self):
        g = Game()
        self.assertEqual(len(g._replay_snapshots), 0)

    def test_save_replay_snapshot(self):
        g = Game(starting_stones=10)
        g.place_stone(7, 7)
        g.save_replay_snapshot()
        self.assertEqual(len(g._replay_snapshots), 1)
        snap = g._replay_snapshots[0]
        self.assertEqual(snap['grid'][7][7], 1)
        self.assertEqual(snap['supply'][1], 9)
        self.assertEqual(snap['current'], 1)
        self.assertEqual(len(snap['move_log']), 0)

    def test_save_replay_snapshot_tracks_multiple(self):
        g = Game(starting_stones=30)
        g.place_stone(7, 7)
        g.current = 2
        g.save_replay_snapshot()
        g.place_stone(7, 8)
        g.current = 1
        g.save_replay_snapshot()
        self.assertEqual(len(g._replay_snapshots), 2)
        self.assertEqual(g._replay_snapshots[0]['current'], 2)
        self.assertEqual(g._replay_snapshots[0]['supply'][1], 29)
        self.assertEqual(g._replay_snapshots[1]['current'], 1)
        self.assertEqual(g._replay_snapshots[1]['grid'][8][7], 2)

    def test_restore_replay_snapshot(self):
        g = Game(starting_stones=30)
        g.place_stone(7, 7)
        g.current = 2
        g.save_replay_snapshot()
        g.place_stone(9, 9)
        g.current = 1
        g.restore_replay_snapshot(g._replay_snapshots[0])
        self.assertEqual(g.current, 2)
        self.assertEqual(g.board.get(7, 7), 1)
        self.assertTrue(g.board.is_empty(9, 9))
        self.assertEqual(g.supply[1], 29)
        self.assertEqual(g.supply[2], 30)

    def test_restore_replay_snapshot_mutates_grid_independently(self):
        g = Game(starting_stones=30)
        g.save_replay_snapshot()
        g.place_stone(7, 7)
        g.save_replay_snapshot()
        grid_before = [row.copy() for row in g.board.grid]
        g.restore_replay_snapshot(g._replay_snapshots[0])
        self.assertTrue(g.board.is_empty(7, 7))
        grid_before[7][7] = 0
        for y in range(g.size):
            for x in range(g.size):
                self.assertEqual(g.board.grid[y][x], grid_before[y][x])

    def test_replay_snapshots_in_serialize(self):
        g = Game()
        g.save_replay_snapshot()
        g.place_stone(7, 7)
        g.current = 2
        g.save_replay_snapshot()
        data = g.serialize()
        self.assertIn('replay_snapshots', data)
        self.assertEqual(len(data['replay_snapshots']), 2)

    def test_replay_snapshots_restored_on_deserialize(self):
        g = Game()
        g.save_replay_snapshot()
        g.place_stone(7, 7)
        g.current = 2
        g.save_replay_snapshot()
        data = g.serialize()
        g2 = Game.deserialize(data)
        self.assertEqual(len(g2._replay_snapshots), 2)
        self.assertEqual(g2._replay_snapshots[0]['current'], 1)
        self.assertEqual(g2._replay_snapshots[1]['current'], 2)

    def test_replay_snapshots_restore_timers(self):
        g = Game()
        g.timers = {1: 10.0, 2: 5.0}
        g.save_replay_snapshot()
        g.restore_replay_snapshot(g._replay_snapshots[0])
        self.assertEqual(g.timers[1], 10.0)
        self.assertEqual(g.timers[2], 5.0)

    def test_stats_persistence(self):
        from gomoku.game import save_stats, load_stats, compute_game_stats
        g = Game()
        g.do_placement(0, 0)
        g.current = 2
        g.do_placement(0, 1)
        cur = compute_game_stats(g, 1)
        stats = load_stats()
        stats['total_games'] += 1
        for k in ('wins', 'moves', 'recoveries', 'total_time'):
            for side in (1, 2):
                stats[k][side] += cur[k][side]
        stats['draws'] += cur['draws']
        save_stats(stats)
        loaded = load_stats()
        self.assertEqual(loaded['total_games'], 1)
        self.assertEqual(loaded['wins'][1], 1)
        self.assertEqual(loaded['moves'][1], 1)
        self.assertEqual(loaded['moves'][2], 1)


if __name__ == '__main__':
    unittest.main()
