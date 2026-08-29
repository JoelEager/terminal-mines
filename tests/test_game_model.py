import unittest
from terminal_mines.game_model import (
    Cell, CellState, GameState, Minefield, random_minefield
)


class TestCell(unittest.TestCase):
    def test_cell_init_and_repr(self):
        cell_mine = Cell(is_mine=True)
        self.assertTrue(cell_mine.is_mine)
        self.assertEqual(cell_mine.state, CellState.UNKNOWN)

        cell_safe = Cell(is_mine=False)
        self.assertFalse(cell_safe.is_mine)


class TestMinefield(unittest.TestCase):
    def test_minefield_init_and_properties(self):
        mines = {"0,0", "1,1"}
        minefield = Minefield(3, 3, mines)

        self.assertEqual(minefield.width, 3)
        self.assertEqual(minefield.height, 3)
        self.assertEqual(minefield.x, 0)
        self.assertEqual(minefield.y, 0)
        self.assertEqual(minefield.state, GameState.IN_PROGRESS)
        self.assertEqual(minefield.num_mines, 2)
        self.assertEqual(minefield.flags_remaining, 2)

        # Test cells iterator
        all_cells = list(minefield.cells)
        self.assertEqual(len(all_cells), 9)

        # Test cords_and_cells iterator
        cords_cells = list(minefield.cords_and_cells)
        self.assertEqual(len(cords_cells), 9)
        self.assertEqual(cords_cells[0][0], 0)
        self.assertEqual(cords_cells[0][1], 0)

    def test_get_cell(self):
        minefield = Minefield(3, 3, {"0,0"})
        cell = minefield.get_cell(0, 0)
        self.assertTrue(cell.is_mine)

        with self.assertRaises(IndexError):
            minefield.get_cell(-1, 0)
        with self.assertRaises(IndexError):
            minefield.get_cell(0, -1)
        with self.assertRaises(IndexError):
            minefield.get_cell(3, 0)
        with self.assertRaises(IndexError):
            minefield.get_cell(0, 3)

    def test_neighboring_cords_and_neighbors(self):
        minefield = Minefield(3, 3, set())

        # Corner (0,0) has 3 neighbors
        cords = list(minefield.neighboring_cords(0, 0))
        self.assertEqual(sorted(cords), [(0, 1), (1, 0), (1, 1)])
        neighbors = list(minefield.neighbors(0, 0))
        self.assertEqual(len(neighbors), 3)

        # Center (1,1) has 8 neighbors
        cords = list(minefield.neighboring_cords(1, 1))
        self.assertEqual(len(cords), 8)

    def test_flag_cell(self):
        minefield = Minefield(2, 2, {"0,0"})

        # Toggle flag ON
        minefield.flag_cell(0, 1)
        self.assertEqual(minefield.get_cell(0, 1).state, CellState.FLAGGED)
        self.assertEqual(minefield.flags_remaining, 0)

        # Try flagging when flags_remaining is 0
        minefield.flag_cell(1, 0)
        self.assertEqual(minefield.get_cell(1, 0).state, CellState.UNKNOWN)

        # Toggle flag OFF
        minefield.flag_cell(0, 1)
        self.assertEqual(minefield.get_cell(0, 1).state, CellState.UNKNOWN)
        self.assertEqual(minefield.flags_remaining, 1)

        # Flag cannot be placed on revealed cell
        minefield.reveal_cell(1, 1)
        state_before = minefield.get_cell(1, 1).state
        self.assertNotEqual(state_before, CellState.UNKNOWN)
        minefield.flag_cell(1, 1)
        self.assertEqual(minefield.get_cell(1, 1).state, state_before)

    def test_reveal_cell_warning_and_win(self):
        # 2x2 board with 1 mine at (0,0)
        minefield = Minefield(2, 2, {"0,0"})

        # First move on non-mine cell (1,0) - neighbor count is 1
        minefield.reveal_cell(1, 0)
        self.assertEqual(minefield.get_cell(1, 0).state, CellState.WARN1)
        self.assertEqual(minefield.state, GameState.IN_PROGRESS)

        # Reveal remaining non-mine cells (0,1) and (1,1)
        minefield.reveal_cell(0, 1)
        self.assertEqual(minefield.get_cell(0, 1).state, CellState.WARN1)
        self.assertEqual(minefield.state, GameState.IN_PROGRESS)

        minefield.reveal_cell(1, 1)
        self.assertEqual(minefield.get_cell(1, 1).state, CellState.WARN1)
        self.assertEqual(minefield.state, GameState.WON)

    def test_reveal_cell_recursive_safe_expansion(self):
        # 3x3 board with mine at (2,2)
        minefield = Minefield(3, 3, {"2,2"})

        # Revealing (0,0) should expand recursively to (0,1), (1,0), (1,1) which are safe (0 neighbor mines)
        minefield.reveal_cell(0, 0)

        self.assertEqual(minefield.get_cell(0, 0).state, CellState.SAFE)
        self.assertEqual(minefield.get_cell(0, 1).state, CellState.SAFE)
        self.assertEqual(minefield.get_cell(1, 0).state, CellState.SAFE)
        self.assertEqual(minefield.get_cell(1, 1).state, CellState.WARN1)
        self.assertEqual(minefield.get_cell(0, 2).state, CellState.SAFE)
        self.assertEqual(minefield.get_cell(2, 0).state, CellState.SAFE)

    def test_reveal_cell_first_move_relocation(self):
        # Board where all cells except (0,0) are NOT mines
        minefield = Minefield(2, 2, {"0,0"})

        # First move is on mine cell (0,0) -> mine relocated to another cell
        minefield.reveal_cell(0, 0)
        self.assertFalse(minefield.get_cell(0, 0).is_mine)
        self.assertEqual(minefield.num_mines, 1)
        self.assertEqual(minefield.state, GameState.IN_PROGRESS)

    def test_reveal_cell_loss(self):
        # 2x2 board with mine at (0,0)
        minefield = Minefield(2, 2, {"0,0"})

        # Make a safe move first so first_move flag is set to False
        minefield.reveal_cell(1, 1)
        self.assertEqual(minefield.state, GameState.IN_PROGRESS)

        # Now hit mine at (0,0)
        minefield.reveal_cell(0, 0)
        self.assertEqual(minefield.get_cell(0, 0).state, CellState.EXPLODED)
        self.assertEqual(minefield.state, GameState.LOST)

    def test_reveal_already_revealed_cell(self):
        minefield = Minefield(2, 2, set())
        minefield.reveal_cell(0, 0)
        self.assertEqual(minefield.get_cell(0, 0).state, CellState.SAFE)
        # Calling reveal again does nothing
        minefield.reveal_cell(0, 0)
        self.assertEqual(minefield.get_cell(0, 0).state, CellState.SAFE)


class TestRandomMinefield(unittest.TestCase):
    def test_random_minefield(self):
        field = random_minefield(5, 10, 8)
        self.assertEqual(field.width, 10)
        self.assertEqual(field.height, 8)
        self.assertEqual(field.num_mines, 5)


if __name__ == "__main__":
    unittest.main()
