import unittest
from gomoku.game import Game
from gomoku.ai import (
    select_ai_move, select_ai_replacement,
    _light_score, _score_all_moves, _simulate_placement,
)
from gomoku.board import Board


class TestAI(unittest.TestCase):
    def _place(self, g, player, x, y):
        g.current = player
        g.place_stone(x, y)
        g.current = g.opponent()

    def test_ai_simple_returns_valid_move(self):
        b = Board()
        x, y = select_ai_move(b, 1, 'simple')
        self.assertTrue(b.in_bounds(x, y))
        self.assertTrue(b.is_empty(x, y))

    def test_ai_medium_returns_valid_move(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        x, y = select_ai_move(b, 1, 'medium')
        self.assertTrue(b.in_bounds(x, y))
        self.assertTrue(b.is_empty(x, y))

    def test_ai_hard_returns_valid_move(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        x, y = select_ai_move(b, 1, 'hard')
        self.assertTrue(b.in_bounds(x, y))
        self.assertTrue(b.is_empty(x, y))

    def test_ai_replacement_simple(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        rep = select_ai_replacement(b, 1, 'simple')
        self.assertIsNotNone(rep)
        rx, ry = rep
        self.assertEqual(b.get(rx, ry), 2)

    def test_ai_replacement_medium(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        b.set(8, 7, 1)
        rep = select_ai_replacement(b, 1, 'medium')
        self.assertIsNotNone(rep)
        rx, ry = rep
        self.assertEqual(b.get(rx, ry), 2)

    def test_ai_replacement_hard(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        b.set(8, 7, 1)
        rep = select_ai_replacement(b, 1, 'hard')
        self.assertIsNotNone(rep)
        rx, ry = rep
        self.assertEqual(b.get(rx, ry), 2)

    def test_ai_replacement_quick_medium(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        rep = select_ai_replacement(b, 1, 'medium', quick=True)
        self.assertIsNotNone(rep)
        rx, ry = rep
        self.assertEqual(b.get(rx, ry), 2)

    def test_ai_replacement_quick_hard(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(7, 8, 2)
        b.set(8, 7, 1)
        rep = select_ai_replacement(b, 1, 'hard', quick=True)
        self.assertIsNotNone(rep)
        rx, ry = rep
        self.assertEqual(b.get(rx, ry), 2)

    def test_ai_replacement_no_candidates(self):
        b = Board()
        rep = select_ai_replacement(b, 1, 'hard')
        self.assertIsNone(rep)

    def test_game_with_ai(self):
        g = Game()
        g.player_types = {1: 'ai', 2: 'ai'}
        g.ai_levels = {1: 'medium', 2: 'medium'}

        for _ in range(20):
            if g.has_lost(g.current):
                break
            x, y = select_ai_move(g.board, g.current, g.ai_levels[g.current])
            self.assertTrue(g.board.is_empty(x, y))
            g.place_stone(x, y)
            r = g.process_stone_placement(x, y)
            if r.result == 'recovered' and r.can_replace:
                rep = select_ai_replacement(g.board, g.current, g.ai_levels[g.current])
                if rep:
                    g.apply_replacement(*rep)
                    g.process_stone_placement(*rep)
            if not g.has_lost(g.current):
                g.current = g.opponent()

    def test_ai_medium_takes_winning_move(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        x, y = select_ai_move(b, 1, 'medium')
        self.assertEqual((x, y), (4, 7))

    def test_ai_hard_takes_winning_move(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        b.set(5, 7, 2)
        b.set(6, 7, 2)
        x, y = select_ai_move(b, 1, 'hard')
        self.assertTrue(b.in_bounds(x, y))
        self.assertTrue(b.is_empty(x, y))

    def test_ai_medium_blocks_opponent_five(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 2)
        x, y = select_ai_move(b, 1, 'medium')
        self.assertEqual((x, y), (4, 7))

    def test_ai_hard_blocks_opponent_five(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 2)
        x, y = select_ai_move(b, 1, 'hard')
        self.assertTrue(b.in_bounds(x, y))
        self.assertTrue(b.is_empty(x, y))

    def test_ai_simple_does_not_always_win(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        x, y = select_ai_move(b, 1, 'simple')
        self.assertTrue(b.in_bounds(x, y))

    def test_ai_medium_picks_winning_move_early(self):
        b = Board(15)
        for x in range(4):
            b.set(x, 0, 1)
        x, y = select_ai_move(b, 1, 'medium')
        self.assertEqual((x, y), (4, 0))

    def test_ai_hard_blocks_opponent_five_exact(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 2)
        x, y = select_ai_move(b, 1, 'hard')
        self.assertEqual((x, y), (4, 7))

    def test_ai_no_legal_moves(self):
        b = Board(5)
        for y in range(5):
            for x in range(5):
                b.set(x, y, 1 if (x + y) % 2 == 0 else 2)
        move = select_ai_move(b, 1, 'simple')
        self.assertIsNone(move)
        move = select_ai_move(b, 1, 'medium')
        self.assertIsNone(move)
        move = select_ai_move(b, 1, 'hard')
        self.assertIsNone(move)


class TestAIInternals(unittest.TestCase):
    # --- _light_score ---
    def test_light_score_empty_board(self):
        b = Board()
        score = _light_score(b, 1, 7, 7)
        self.assertIsInstance(score, (int, float))
        self.assertGreaterEqual(score, 0)

    def test_light_score_bonus_for_five(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        score = _light_score(b, 1, 4, 7)
        self.assertGreaterEqual(score, 50000)

    def test_light_score_no_bonus_without_five(self):
        b = Board()
        for x in range(3):
            b.set(x, 7, 1)
        score = _light_score(b, 1, 4, 7)
        self.assertLess(score, 50000)

    def test_light_score_center_higher_than_edge(self):
        b = Board()
        b.set(7, 6, 1)
        b.set(7, 8, 2)
        center = _light_score(b, 1, 7, 7)
        corner = _light_score(b, 1, 0, 0)
        self.assertGreater(center, corner)

    # --- _score_all_moves ---
    def test_score_all_moves_empty_board(self):
        b = Board()
        scored = _score_all_moves(b, 1)
        self.assertEqual(len(scored), 225)
        for score, x, y in scored:
            self.assertIsInstance(score, float)
            self.assertTrue(b.in_bounds(x, y))

    def test_score_all_moves_returns_sorted(self):
        b = Board()
        b.set(7, 7, 1)
        scored = _score_all_moves(b, 2)
        for i in range(len(scored) - 1):
            self.assertGreaterEqual(scored[i][0], scored[i + 1][0])

    def test_score_all_moves_early_return_on_win(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        scored = _score_all_moves(b, 1)
        self.assertEqual(len(scored), 1)
        self.assertEqual((scored[0][1], scored[0][2]), (4, 7))

    def test_score_all_moves_defensive_bonus_when_opponent_threatens(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 2)
        scored = _score_all_moves(b, 1)
        blocking_found = any((x, y) == (4, 7) for _, x, y in scored)
        self.assertTrue(blocking_found)

    def test_score_all_moves_no_moves(self):
        b = Board(5)
        for y in range(5):
            for x in range(5):
                b.set(x, y, 1 if (x + y) % 2 == 0 else 2)
        scored = _score_all_moves(b, 1)
        self.assertEqual(len(scored), 0)

    # --- _simulate_placement ---
    def test_simulate_placement_no_line(self):
        b = Board()
        b.set(7, 8, 2)
        sim = _simulate_placement(b, 1, 7, 7, 'hard')
        self.assertEqual(sim.get(7, 7), 1)
        self.assertIsNot(b, sim)

    def test_simulate_placement_with_line_and_replacement(self):
        b = Board()
        for x in range(4):
            b.set(x, 0, 1)
        b.set(5, 0, 2)
        b.set(6, 0, 2)
        sim = _simulate_placement(b, 1, 4, 0, 'hard')
        self.assertIsInstance(sim, Board)
        self.assertTrue(sim.is_empty(4, 0))

    def test_simulate_placement_original_unchanged(self):
        b = Board()
        for x in range(4):
            b.set(x, 0, 1)
        b.set(5, 0, 2)
        original = b.clone()
        _simulate_placement(b, 1, 4, 0, 'hard')
        self.assertEqual(b.grid, original.grid)

    def test_simulate_placement_no_candidates(self):
        b = Board()
        for x in range(5):
            b.set(x, 0, 1)
        b.set(0, 1, 2)
        sim = _simulate_placement(b, 1, 2, 0, 'hard')
        self.assertIsInstance(sim, Board)
        self.assertTrue(sim.is_empty(2, 0))


if __name__ == '__main__':
    unittest.main()
