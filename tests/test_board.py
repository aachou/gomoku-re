import unittest
from gomoku.board import Board, BOARD_SIZE, DIRECTIONS


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
        before = b._cell_potential.get((9, 8), [0, 0])[1]
        b.set(0, 0, 2)
        # cell (9, 8) is 10+ cells from (0, 0) — beyond 5-step limit, should be unchanged
        after = b._cell_potential.get((9, 8), [0, 0])[1]
        self.assertEqual(before, after)


if __name__ == '__main__':
    unittest.main()
