import os
import tempfile
import unittest
from unittest.mock import patch
from click.testing import CliRunner
import terminal_mines.game_logic.solver as solver
from terminal_mines.mines import main


class TestE2E(unittest.TestCase):
    def setUp(self):
        solver.all_guesses = -1

    @patch("terminal_mines.game_logic.solver.sleep")
    @patch("terminal_mines.game_logic.renderer.clear")
    def test_solve_deterministic_game(self, mock_clear, mock_sleep):
        """
        Tests solving a board deterministically using a custom mines file.
        Verifies that the output contains 'Game won' and 'with no unsafe guesses.'.
        """
        runner = CliRunner()
        with tempfile.NamedTemporaryFile("w+", delete=False) as tf:
            tf.write("2,1\n2,3")
            tf.flush()
            mines_file_path = tf.name

        try:
            result = runner.invoke(main, ["2,5,5", "--solve", "--mines", mines_file_path])
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Game won", result.output)
            self.assertIn("with no unsafe guesses.", result.output)
        finally:
            if os.path.exists(mines_file_path):
                os.remove(mines_file_path)


if __name__ == "__main__":
    unittest.main()
