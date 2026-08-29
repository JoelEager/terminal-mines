import unittest
import click
from terminal_mines.main import DifficultyParamType, DIFFICULTY_PRESETS


class TestDifficultyParamType(unittest.TestCase):
    def setUp(self):
        self.param_type = DifficultyParamType()

    def test_preset_difficulties(self):
        for preset_name, expected_args in DIFFICULTY_PRESETS.items():
            result = self.param_type.convert(preset_name, None, None)
            self.assertEqual(result, expected_args)

    def test_custom_valid_difficulty(self):
        result = self.param_type.convert("10,15,20", None, None)
        self.assertEqual(result, (10, 15, 20))

    def test_invalid_difficulty_name(self):
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("invalid_name", None, None)
        self.assertIn("'invalid_name' is not a valid difficulty name", str(cm.exception))

    def test_invalid_format_non_integer(self):
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("10,abc,20", None, None)
        self.assertIn("a custom difficulty must be made of 3 positive integers separated by commas", str(cm.exception))

    def test_invalid_format_wrong_arg_count(self):
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("10,20", None, None)
        self.assertIn("a custom difficulty must be made of 3 positive integers separated by commas", str(cm.exception))

        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("10,20,30,40", None, None)
        self.assertIn("a custom difficulty must be made of 3 positive integers separated by commas", str(cm.exception))

    def test_invalid_non_positive_integers(self):
        # 0 mines
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("0,10,10", None, None)
        self.assertIn("a custom difficulty must be made of 3 positive integers separated by commas", str(cm.exception))

        # negative dimension
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("5,-10,10", None, None)
        self.assertIn("a custom difficulty must be made of 3 positive integers separated by commas", str(cm.exception))

        # float dimension
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("5,1.5,10", None, None)
        self.assertIn("a custom difficulty must be made of 3 positive integers separated by commas", str(cm.exception))

    def test_board_size_limit_exceeded(self):
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("10,31,10", None, None)
        self.assertIn("the game board cannot be larger than 30 cells on either side", str(cm.exception))

        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("10,10,51", None, None)
        self.assertIn("the game board cannot be larger than 30 cells on either side", str(cm.exception))

    def test_too_many_mines(self):
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("100,5,5", None, None)
        self.assertIn("the game board must have at least one safe cell", str(cm.exception))

    def test_all_mines(self):
        with self.assertRaises(click.BadParameter) as cm:
            self.param_type.convert("25,5,5", None, None)
        self.assertIn("the game board must have at least one safe cell", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
