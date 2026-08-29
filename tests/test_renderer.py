import unittest
from unittest.mock import patch
from terminal_mines.game_model import Minefield, CellState, GameState
from terminal_mines.renderer import terminal_renderer


class TestRenderer(unittest.TestCase):
    @patch("terminal_mines.renderer.echo")
    def test_render_start(self, mock_echo):
        minefield = Minefield(2, 2, {"0,0"})
        with terminal_renderer() as render:
            render(minefield)

        # Check cursor ANSI escape codes
        self.assertTrue(mock_echo.call_args_list[0][0][0].startswith("\033[?25l"))
        self.assertTrue(mock_echo.call_args_list[2][0][0].endswith("\033[?25h"))

        # Check borders and status
        rendered_output = mock_echo.call_args_list[1][0][0]
        self.assertIn("┌─────┐", rendered_output)
        self.assertIn("└─────┘", rendered_output)
        self.assertIn("First reveal is always safe", rendered_output)

        # Check overwrite ANSI escape codes
        self.assertIn("\033[H", rendered_output)
        self.assertIn("\033[K", rendered_output)

    @patch("terminal_mines.renderer.echo")
    def test_render_overwrite_false(self, mock_echo):
        minefield = Minefield(2, 2, {"0,0"})
        with terminal_renderer(overwrite=False) as render:
            render(minefield)

        rendered_output = mock_echo.call_args_list[1][0][0]
        self.assertNotIn("\033[H", rendered_output)
        self.assertNotIn("\033[K", rendered_output)

    @patch("terminal_mines.renderer.echo")
    def test_render_in_progress_one_safe_cell_remains(self, mock_echo):
        minefield = Minefield(2, 2, {"0,0"})
        minefield.first_move = False
        minefield.get_cell(1, 0).state = CellState.SAFE
        minefield.get_cell(0, 1).state = CellState.WARN1

        with terminal_renderer() as render:
            render(minefield)

        rendered_output = mock_echo.call_args_list[1][0][0]
        self.assertIn("0 / 1 marked; 1 safe cell remains", rendered_output)

    @patch("terminal_mines.renderer.echo")
    def test_render_won(self, mock_echo):
        minefield = Minefield(2, 2, {"0,0"})
        minefield.reveal_cell(1, 0)
        minefield.reveal_cell(0, 1)
        minefield.reveal_cell(1, 1)

        self.assertEqual(minefield.state, GameState.WON)
        with terminal_renderer() as render:
            render(minefield)

        rendered_output = mock_echo.call_args_list[1][0][0]
        self.assertIn("Game won", rendered_output)

    @patch("terminal_mines.renderer.echo")
    def test_render_lost(self, mock_echo):
        minefield = Minefield(2, 2, {"0,0"})
        minefield.reveal_cell(1, 1)
        minefield.reveal_cell(0, 0)

        self.assertEqual(minefield.state, GameState.LOST)
        with terminal_renderer() as render:
            render(minefield)

        rendered_output = mock_echo.call_args_list[1][0][0]
        self.assertIn("Game lost", rendered_output)


if __name__ == "__main__":
    unittest.main()
