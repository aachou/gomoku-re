import json
import unittest
from unittest.mock import patch, MagicMock
from gomoku.board import Board, BOARD_SIZE
from gomoku.game import Game
from gomoku.cli import parse_coordinate, _handle_command, choose_option


class TestParseCoordinate(unittest.TestCase):
    def setUp(self):
        self.board = Board(15)

    def test_parse_a1(self):
        self.assertEqual(parse_coordinate('A1', self.board), (0, 0))

    def test_parse_h8(self):
        self.assertEqual(parse_coordinate('H8', self.board), (7, 7))

    def test_parse_o15(self):
        self.assertEqual(parse_coordinate('O15', self.board), (14, 14))

    def test_parse_lowercase(self):
        self.assertEqual(parse_coordinate('a1', self.board), (0, 0))

    def test_parse_numeric(self):
        self.assertEqual(parse_coordinate('1 1', self.board), (0, 0))
        self.assertEqual(parse_coordinate('15 15', self.board), (14, 14))

    def test_parse_out_of_bounds_alpha(self):
        self.assertIsNone(parse_coordinate('Z1', self.board))
        self.assertIsNone(parse_coordinate('A16', self.board))

    def test_parse_out_of_bounds_numeric(self):
        self.assertIsNone(parse_coordinate('0 0', self.board))
        self.assertIsNone(parse_coordinate('16 16', self.board))

    def test_parse_empty_string(self):
        self.assertIsNone(parse_coordinate('', self.board))

    def test_parse_invalid_format(self):
        self.assertIsNone(parse_coordinate('ABC', self.board))
        self.assertIsNone(parse_coordinate('A', self.board))
        self.assertIsNone(parse_coordinate('1 A', self.board))


class TestHandleCommand(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_quit(self):
        self.assertEqual(_handle_command('quit', self.game), 'quit')

    def test_quit_uppercase(self):
        self.assertEqual(_handle_command('QUIT', self.game), 'quit')

    def test_save_returns_empty_string(self):
        with patch('builtins.open', MagicMock()):
            result = _handle_command('save', self.game)
            self.assertEqual(result, '')

    def test_load_returns_refresh(self):
        with patch('builtins.open', MagicMock()):
            with patch('json.load', return_value={
                'size': 15, 'grid': [[0]*15 for _ in range(15)],
                'supply': [30, 30], 'current': 1,
                'player_types': ['human', 'human'], 'ai_levels': [None, None],
                'move_log': [], 'timers': [0.0, 0.0], 'history': [],
            }):
                result = _handle_command('load', self.game)
                self.assertEqual(result, 'refresh')

    def test_undo_with_no_history(self):
        result = _handle_command('undo', self.game)
        self.assertIsNone(result)

    def test_undo_with_snapshot(self):
        self.game.save_snapshot()
        result = _handle_command('undo', self.game)
        self.assertEqual(result, 'refresh')

    def test_unknown_command(self):
        result = _handle_command('xyz', self.game)
        self.assertIsNone(result)

    def test_load_file_not_found_returns_refresh(self):
        with patch('builtins.open', side_effect=FileNotFoundError):
            result = _handle_command('load', self.game)
            self.assertEqual(result, 'refresh')


class TestChooseOption(unittest.TestCase):
    def test_single_valid_choice(self):
        with patch('builtins.input', return_value='2'):
            result = choose_option('prompt', ['1', '2', '3'])
            self.assertEqual(result, '2')

    def test_retry_on_invalid(self):
        inputs = ['invalid', '5', '2']
        with patch('builtins.input', side_effect=inputs):
            result = choose_option('prompt', ['1', '2', '3'])
            self.assertEqual(result, '2')

    def test_strips_whitespace(self):
        with patch('builtins.input', return_value='  2  '):
            result = choose_option('prompt', ['1', '2', '3'])
            self.assertEqual(result, '2')


if __name__ == '__main__':
    unittest.main()
