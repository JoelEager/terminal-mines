import unittest
from unittest.mock import patch
from terminal_mines.game_model import Minefield, CellState, GameState
from terminal_mines.renderer import render


class TestRenderer(unittest.TestCase):
    @patch("terminal_mines.renderer.clear")
    @patch("terminal_mines.renderer.echo")
    def test_render_in_progress(self, mock_echo, mock_clear):
        minefield = Minefield(2, 2, {"0,0"})
        render(minefield)

        mock_clear.assert_called_once()
        mock_echo.assert_called_once()
        rendered_output = mock_echo.call_args[0][0]

        # Check borders and state line for in progress
        self.assertIn("┌─────┐", rendered_output)
        self.assertIn("└─────┘", rendered_output)
        self.assertIn("0 / 1 marked; 3 safe cells remain", rendered_output)

    @patch("terminal_mines.renderer.clear")
    @patch("terminal_mines.renderer.echo")
    def test_render_in_progress_one_safe_cell_remains(self, mock_echo, mock_clear):
        minefield = Minefield(2, 2, {"0,0"})
        minefield.get_cell(1, 0).state = CellState.SAFE
        minefield.get_cell(0, 1).state = CellState.WARN1

        render(minefield)

        rendered_output = mock_echo.call_args[0][0]
        self.assertIn("0 / 1 marked; 1 safe cell remains", rendered_output)

    @patch("terminal_mines.renderer.clear")
    @patch("terminal_mines.renderer.echo")
    def test_render_won(self, mock_echo, mock_clear):
        minefield = Minefield(2, 2, {"0,0"})
        minefield.reveal_cell(1, 0)
        minefield.reveal_cell(0, 1)
        minefield.reveal_cell(1, 1)

        self.assertEqual(minefield.state, GameState.WON)
        render(minefield)

        rendered_output = mock_echo.call_args[0][0]
        self.assertIn("Game won", rendered_output)

    @patch("terminal_mines.renderer.clear")
    @patch("terminal_mines.renderer.echo")
    def test_render_lost(self, mock_echo, mock_clear):
        minefield = Minefield(2, 2, {"0,0"})
        minefield.reveal_cell(1, 1)
        minefield.reveal_cell(0, 0)

        self.assertEqual(minefield.state, GameState.LOST)
        render(minefield)

        rendered_output = mock_echo.call_args[0][0]
        self.assertIn("Game lost", rendered_output)

    @patch("terminal_mines.renderer.clear")
    @patch("terminal_mines.renderer.echo")
    def test_render_incorrect_flag(self, mock_echo, mock_clear):
        # 2x2 board, mine at (0,0)
        # Flag at (1,1) (which is NOT a mine) and lose game by hitting (0,0)
        minefield = Minefield(2, 2, {"0,0"})
        minefield.flag_cell(1, 1)
        minefield.reveal_cell(1, 0)
        minefield.reveal_cell(0, 0)  # Game LOST

        self.assertEqual(minefield.state, GameState.LOST)
        render(minefield)

        rendered_output = mock_echo.call_args[0][0]
        self.assertIn("Game lost", rendered_output)


if __name__ == "__main__":
    unittest.main()
