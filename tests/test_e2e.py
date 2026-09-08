import unittest
from click.testing import CliRunner
from terminal_mines.main import main


class TestE2E(unittest.TestCase):
    def test_solver_difficulty_3_2_2(self):
        runner = CliRunner()
        result = runner.invoke(main, ["3,2,2", "-s"])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Game won", result.output)

    def test_normal_play_difficulty_3_2_2(self):
        runner = CliRunner()
        result = runner.invoke(main, ["3,2,2"], input=" ")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Game won", result.output)


if __name__ == "__main__":
    unittest.main()
