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


if __name__ == '__main__':
    unittest.main()
