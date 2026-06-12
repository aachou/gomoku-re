import unittest
from gomoku.board import (
    Board, BOARD_SIZE, DIRECTIONS,
    _pattern_score, _consecutive_count, _would_form_five,
    _evaluate_direction, _evaluate_potential, _has_immediate_five,
)


class TestBoard(unittest.TestCase):
    def test_init(self):
        b = Board()
        self.assertEqual(b.size, BOARD_SIZE)
        self.assertEqual(len(b._empty_cells), BOARD_SIZE * BOARD_SIZE)
        self.assertEqual(b._stone_count, [0, 0, 0])
        self.assertEqual(len(b._player_cells[1]), 0)
        self.assertEqual(len(b._player_cells[2]), 0)
        self.assertFalse(b.is_full())

    def test_set_and_get(self):
        b = Board()
        b.set(7, 7, 1)
        self.assertEqual(b.get(7, 7), 1)
        self.assertFalse(b.is_empty(7, 7))
        self.assertEqual(len(b._empty_cells), BOARD_SIZE * BOARD_SIZE - 1)
        self.assertEqual(b._stone_count[1], 1)
        self.assertIn((7, 7), b._player_cells[1])
        self.assertNotIn((7, 7), b._player_cells[2])

        b.set(7, 7, 0)
        self.assertTrue(b.is_empty(7, 7))
        self.assertEqual(len(b._empty_cells), BOARD_SIZE * BOARD_SIZE)
        self.assertEqual(b._stone_count[1], 0)
        self.assertNotIn((7, 7), b._player_cells[1])

    def test_legal_moves(self):
        b = Board()
        self.assertEqual(len(b.legal_moves()), 225)
        b.set(0, 0, 1)
        self.assertEqual(len(b.legal_moves()), 224)
        self.assertNotIn((0, 0), b.legal_moves())

    def test_in_bounds(self):
        b = Board()
        self.assertTrue(b.in_bounds(0, 0))
        self.assertTrue(b.in_bounds(14, 14))
        self.assertFalse(b.in_bounds(-1, 0))
        self.assertFalse(b.in_bounds(0, 15))

    def test_scan_line_horizontal(self):
        b = Board()
        for x in range(5):
            b.set(x, 7, 1)
        coords = b.scan_line(2, 7, 1, 0, 1)
        self.assertEqual(len(coords), 5)
        self.assertEqual(coords, [(0, 7), (1, 7), (2, 7), (3, 7), (4, 7)])

    def test_scan_line_vertical(self):
        b = Board()
        for y in range(5):
            b.set(7, y, 2)
        coords = b.scan_line(7, 2, 0, 1, 2)
        self.assertEqual(len(coords), 5)
        self.assertEqual(coords, [(7, 0), (7, 1), (7, 2), (7, 3), (7, 4)])

    def test_scan_line_diagonal(self):
        b = Board()
        for i in range(5):
            b.set(i, i, 1)
        coords = b.scan_line(2, 2, 1, 1, 1)
        self.assertEqual(len(coords), 5)
        self.assertEqual(coords, [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)])

    def test_find_connected_line(self):
        b = Board()
        for x in range(5):
            b.set(x, 7, 1)
        line = b.find_connected_line(2, 7, 1)
        self.assertIsNotNone(line)
        self.assertEqual(len(line), 5)

    def test_find_connected_line_not_found(self):
        b = Board()
        b.set(0, 0, 1)
        b.set(1, 0, 1)
        b.set(3, 0, 1)
        b.set(4, 0, 1)
        line = b.find_connected_line(0, 0, 1)
        self.assertIsNone(line)

    def test_remove_line(self):
        b = Board()
        for x in range(5):
            b.set(x, 0, 1)
        line = b.find_connected_line(0, 0, 1)
        self.assertIsNotNone(line)
        b.remove_line(line)
        for x in range(5):
            self.assertTrue(b.is_empty(x, 0))

    def test_count_opponent_stones(self):
        b = Board()
        b.set(0, 0, 1)
        b.set(1, 0, 2)
        self.assertEqual(b.count_opponent_stones(1), 1)
        self.assertEqual(b.count_opponent_stones(2), 1)
        self.assertEqual(len(b._player_cells[2]), 1)
        self.assertEqual(len(b._player_cells[1]), 1)

    def test_clone(self):
        b = Board()
        b.set(7, 7, 1)
        b.set(0, 0, 2)
        c = b.clone()
        self.assertEqual(c.get(7, 7), 1)
        self.assertEqual(len(c._empty_cells), len(b._empty_cells))
        self.assertEqual(c._stone_count, b._stone_count)
        self.assertEqual(c._player_cells[1], b._player_cells[1])
        self.assertEqual(c._player_cells[2], b._player_cells[2])
        c.set(7, 7, 2)
        self.assertEqual(b.get(7, 7), 1)
        self.assertIn((7, 7), b._player_cells[1])
        self.assertIn((7, 7), c._player_cells[2])

    def test_is_full(self):
        b = Board(5)
        self.assertFalse(b.is_full())
        for y in range(5):
            for x in range(5):
                b.set(x, y, 1)
        self.assertTrue(b.is_full())
        self.assertEqual(len(b._empty_cells), 0)

    def test_rebuild_cache(self):
        b = Board()
        b.set(0, 0, 1)
        b.set(1, 1, 2)
        clone = Board(15)
        clone.grid = [row.copy() for row in b.grid]
        clone._rebuild_cache()
        self.assertEqual(len(clone._empty_cells), 223)
        self.assertEqual(clone._stone_count[1], 1)
        self.assertEqual(clone._stone_count[2], 1)
        self.assertIn((0, 0), clone._player_cells[1])
        self.assertIn((1, 1), clone._player_cells[2])
        self.assertNotIn((0, 0), clone._player_cells[2])

    def test_scan_line_anti_diagonal(self):
        b = Board()
        for i in range(5):
            b.set(4 - i, i, 1)
        coords = b.scan_line(2, 2, 1, -1, 1)
        self.assertEqual(len(coords), 5)
        self.assertEqual(coords, [(0, 4), (1, 3), (2, 2), (3, 1), (4, 0)])

    def test_has_immediate_five_false_when_empty(self):
        b = Board()
        self.assertFalse(b.has_immediate_five(1))
        self.assertFalse(b.has_immediate_five(2))

    def test_has_immediate_five_true(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        self.assertTrue(b.has_immediate_five(1))

    def test_has_immediate_five_cache_invalidated_on_set(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        b.set(0, 0, 2)
        self.assertTrue(b.has_immediate_five(1))
        b.set(4, 7, 2)
        self.assertFalse(b.has_immediate_five(1))

    def test_clone_preserves_five_threat(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        self.assertTrue(b.has_immediate_five(1))
        c = b.clone()
        self.assertTrue(c.has_immediate_five(1))
        c.set(4, 7, 2)
        self.assertFalse(c.has_immediate_five(1))
        self.assertTrue(b.has_immediate_five(1))

    def test_set_replacement_path(self):
        b = Board()
        b.set(7, 7, 1)
        self.assertEqual(b._stone_count[1], 1)
        self.assertEqual(b._stone_count[2], 0)
        self.assertIn((7, 7), b._player_cells[1])
        self.assertNotIn((7, 7), b._player_cells[2])
        self.assertNotIn((7, 7), b._empty_cells)

        b.set(7, 7, 2)
        self.assertEqual(b._stone_count[1], 0)
        self.assertEqual(b._stone_count[2], 1)
        self.assertNotIn((7, 7), b._player_cells[1])
        self.assertIn((7, 7), b._player_cells[2])
        self.assertNotIn((7, 7), b._empty_cells)

    def test_find_connected_line_more_than_five(self):
        b = Board()
        for x in range(7):
            b.set(x, 7, 1)
        line = b.find_connected_line(3, 7, 1)
        self.assertIsNotNone(line)
        self.assertEqual(len(line), 5)
        for x, y in line:
            self.assertEqual(y, 7)
            self.assertIn(x, range(7))

    def test_potential_around_limited_to_5_steps(self):
        b = Board(19)
        b.set(9, 9, 1)
        before = b._cell_potential[8][9][1] if b._cell_potential[8][9] is not None else 0
        b.set(0, 0, 2)
        # cell (9, 8) is 10+ cells from (0, 0) — beyond 5-step limit, should be unchanged
        after = b._cell_potential[8][9][1] if b._cell_potential[8][9] is not None else 0
        self.assertEqual(before, after)


class TestBoardInternals(unittest.TestCase):
    # --- _pattern_score ---
    def test_pattern_score_exact_table_entries(self):
        self.assertEqual(_pattern_score(4, 2), 50000)
        self.assertEqual(_pattern_score(4, 1), 5000)
        self.assertEqual(_pattern_score(4, 0), 5000)
        self.assertEqual(_pattern_score(3, 2), 3000)
        self.assertEqual(_pattern_score(3, 1), 300)
        self.assertEqual(_pattern_score(3, 0), 50)
        self.assertEqual(_pattern_score(2, 2), 200)
        self.assertEqual(_pattern_score(2, 1), 30)
        self.assertEqual(_pattern_score(2, 0), 10)
        self.assertEqual(_pattern_score(1, 2), 10)
        self.assertEqual(_pattern_score(1, 1), 3)
        self.assertEqual(_pattern_score(1, 0), 1)

    def test_pattern_score_none(self):
        self.assertEqual(_pattern_score(0, 0), 0)
        self.assertEqual(_pattern_score(0, 2), 0)

    def test_pattern_score_clamped_count(self):
        self.assertEqual(_pattern_score(6, 2), 0)
        self.assertEqual(_pattern_score(7, 0), 0)

    def test_pattern_score_clamped_open_ends(self):
        self.assertEqual(_pattern_score(3, 5), 3000)

    # --- _consecutive_count ---
    def test_consecutive_count_empty(self):
        b = Board()
        self.assertEqual(_consecutive_count(b, 7, 7, 1, 0, 1), 0)

    def test_consecutive_count_one_side(self):
        b = Board()
        b.set(8, 7, 1)
        self.assertEqual(_consecutive_count(b, 7, 7, 1, 0, 1), 1)

    def test_consecutive_count_both_sides(self):
        b = Board()
        b.set(6, 7, 1)
        b.set(8, 7, 1)
        self.assertEqual(_consecutive_count(b, 7, 7, 1, 0, 1), 2)

    def test_consecutive_count_opponent_stops(self):
        b = Board()
        b.set(8, 7, 2)
        b.set(6, 7, 1)
        self.assertEqual(_consecutive_count(b, 7, 7, 1, 0, 1), 1)

    def test_consecutive_count_at_boundary(self):
        b = Board()
        b.set(1, 0, 1)
        self.assertEqual(_consecutive_count(b, 0, 0, 1, 0, 1), 1)
        self.assertEqual(_consecutive_count(b, 0, 0, 0, 1, 1), 0)

    def test_consecutive_count_long_line(self):
        b = Board()
        for x in range(10):
            b.set(x, 7, 1)
        self.assertEqual(_consecutive_count(b, 5, 7, 1, 0, 1), 9)

    # --- _would_form_five ---
    def test_would_form_five_true_horizontal(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        self.assertTrue(_would_form_five(b, 1, 4, 7))

    def test_would_form_five_true_vertical(self):
        b = Board()
        for y in range(4):
            b.set(7, y, 1)
        self.assertTrue(_would_form_five(b, 1, 7, 4))

    def test_would_form_five_true_diagonal(self):
        b = Board()
        for i in range(4):
            b.set(i, i, 1)
        self.assertTrue(_would_form_five(b, 1, 4, 4))

    def test_would_form_five_false_short(self):
        b = Board()
        for x in range(3):
            b.set(x, 7, 1)
        self.assertFalse(_would_form_five(b, 1, 4, 7))

    def test_would_form_five_false_blocked(self):
        b = Board()
        b.set(0, 7, 1)
        b.set(1, 7, 1)
        b.set(2, 7, 1)
        b.set(4, 7, 2)
        self.assertFalse(_would_form_five(b, 1, 3, 7))

    def test_would_form_five_edge_of_board(self):
        b = Board()
        for y in range(4):
            b.set(0, y, 1)
        self.assertTrue(_would_form_five(b, 1, 0, 4))
        self.assertFalse(_would_form_five(b, 1, 1, 4))

    # --- _evaluate_direction ---
    def test_evaluate_direction_empty(self):
        b = Board()
        self.assertEqual(_evaluate_direction(1, 7, 7, 1, 0, b), 0)

    def test_evaluate_direction_one_stone_one_end(self):
        b = Board()
        b.set(8, 7, 1)
        self.assertEqual(_evaluate_direction(1, 7, 7, 1, 0, b), 10)

    def test_evaluate_direction_two_stones_open(self):
        b = Board()
        b.set(8, 7, 1)
        b.set(9, 7, 1)
        self.assertEqual(_evaluate_direction(1, 7, 7, 1, 0, b), 200)

    def test_evaluate_direction_one_end_blocked_by_opponent(self):
        b = Board()
        b.set(8, 7, 1)
        b.set(9, 7, 2)
        self.assertEqual(_evaluate_direction(1, 7, 7, 1, 0, b), 3)

    def test_evaluate_direction_one_end_blocked_by_edge(self):
        b = Board()
        b.set(1, 0, 1)
        self.assertEqual(_evaluate_direction(1, 0, 0, 1, 0, b), 3)

    def test_evaluate_direction_opponent_only(self):
        b = Board()
        b.set(8, 7, 2)
        self.assertEqual(_evaluate_direction(1, 7, 7, 1, 0, b), 0)

    def test_evaluate_direction_three_open(self):
        b = Board()
        b.set(8, 7, 1)
        b.set(9, 7, 1)
        b.set(10, 7, 1)
        self.assertEqual(_evaluate_direction(1, 7, 7, 1, 0, b), 3000)

    # --- _evaluate_potential ---
    def test_evaluate_potential_empty(self):
        b = Board()
        self.assertEqual(_evaluate_potential(1, 7, 7, b), 0)

    def test_evaluate_potential_horizontal_only(self):
        b = Board()
        b.set(8, 7, 1)
        expected = _evaluate_direction(1, 7, 7, 1, 0, b)
        self.assertEqual(_evaluate_potential(1, 7, 7, b), expected)

    def test_evaluate_potential_vertical(self):
        b = Board()
        b.set(7, 8, 1)
        b.set(7, 9, 1)
        expected = _evaluate_direction(1, 7, 7, 1, 0, b) + _evaluate_direction(1, 7, 7, 0, 1, b)
        self.assertEqual(_evaluate_potential(1, 7, 7, b), expected)

    def test_evaluate_potential_cross_shape(self):
        b = Board()
        b.set(8, 7, 1)
        b.set(6, 7, 1)
        b.set(7, 8, 1)
        expected = (
            _evaluate_direction(1, 7, 7, 1, 0, b) +
            _evaluate_direction(1, 7, 7, 0, 1, b) +
            _evaluate_direction(1, 7, 7, 1, 1, b) +
            _evaluate_direction(1, 7, 7, 1, -1, b)
        )
        self.assertEqual(_evaluate_potential(1, 7, 7, b), expected)

    # --- _has_immediate_five ---
    def test_has_immediate_five_function_four_in_row(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        self.assertTrue(_has_immediate_five(b, 1))
        self.assertFalse(_has_immediate_five(b, 2))

    def test_has_immediate_five_function_not_present(self):
        b = Board()
        for x in range(3):
            b.set(x, 7, 1)
        self.assertFalse(_has_immediate_five(b, 1))

    def test_has_immediate_five_function_multi_cell_check(self):
        b = Board()
        b.set(0, 0, 1)
        b.set(0, 1, 1)
        b.set(0, 2, 1)
        b.set(0, 3, 1)
        self.assertTrue(_has_immediate_five(b, 1))

    def test_has_immediate_five_function_with_gap(self):
        b = Board()
        b.set(0, 0, 1)
        b.set(1, 0, 1)
        b.set(2, 0, 1)
        b.set(4, 0, 1)
        self.assertTrue(_has_immediate_five(b, 1))
        self.assertFalse(_has_immediate_five(b, 2))

    def test_has_immediate_five_function_both_players(self):
        b = Board()
        for x in range(4):
            b.set(x, 7, 1)
        for x in range(4):
            b.set(x, 8, 2)
        self.assertTrue(_has_immediate_five(b, 1))
        self.assertTrue(_has_immediate_five(b, 2))


if __name__ == '__main__':
    unittest.main()
