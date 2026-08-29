import unittest
from terminal_mines.game_model import Minefield, CellState
from terminal_mines.solver import pick_move


class TestSolverDeterministicStrategies(unittest.TestCase):
    def test_simple_deduction_flag(self):
        """
        When visible mines equal unknown neighbors + flagged neighbors,
        all unknown neighbors must be mines -> flag move.
        """
        # 2x2 board, mine at (0,0)
        # Reveal (1,0), (0,1), (1,1) as WARN1 ('1')
        minefield = Minefield(2, 2, {"0,0"})
        minefield.get_cell(1, 0).state = CellState.WARN1
        minefield.get_cell(0, 1).state = CellState.WARN1
        minefield.get_cell(1, 1).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.flag_cell)
        self.assertEqual((move.x, move.y), (0, 0))

    def test_simple_deduction_reveal(self):
        """
        When visible mines equal flagged neighbors,
        all remaining unknown neighbors are safe -> reveal move.
        """
        # 2x2 board, mine at (0,0)
        # Flag (0,0)
        # Reveal (1,0) as WARN1 ('1')
        minefield = Minefield(2, 2, {"0,0"})
        minefield.flag_cell(0, 0)
        minefield.get_cell(1, 0).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.reveal_cell)
        # Neighbors of (1,0) are (0,0) [flagged], (0,1) [unknown], (1,1) [unknown]
        self.assertIn((move.x, move.y), {(0, 1), (1, 1)})

    def test_two_cell_analysis_flag(self):
        """
        Cell A (1,1) has unknown neighbors {(0,0), (1,0), (2,0)} with 2 remaining mines.
        Cell B (0,1) has unknown neighbors {(0,0), (1,0)} with 1 remaining mine.
        A's unknown neighbors strictly contain B's.
        The extra neighbor (2,0) must be a mine -> flag (2,0).
        """
        minefield = Minefield(3, 2, {"0,0", "2,0"})
        # Setup revealed numbers
        minefield.get_cell(0, 1).state = CellState.WARN1
        minefield.get_cell(1, 1).state = CellState.WARN2
        minefield.get_cell(2, 1).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.flag_cell)
        self.assertEqual((move.x, move.y), (2, 0))
        self.assertTrue(move.debug and move.debug.startswith("Two cell flag"))

    def test_two_cell_analysis_reveal(self):
        """
        Cell A (1,1) has unknown neighbors {(0,0), (1,0), (2,0)} with 1 remaining mine.
        Cell B (0,1) has unknown neighbors {(0,0), (1,0)} with 1 remaining mine.
        A's unknown neighbors strictly contain B's.
        The extra neighbor (2,0) must be safe -> reveal (2,0).
        """
        minefield = Minefield(3, 2, {"0,0"})
        # Setup revealed numbers
        minefield.get_cell(0, 1).state = CellState.WARN1
        minefield.get_cell(1, 1).state = CellState.WARN1
        minefield.get_cell(2, 1).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.reveal_cell)
        self.assertEqual((move.x, move.y), (2, 0))
        self.assertTrue(move.debug and move.debug.startswith("Two cell reveal"))


if __name__ == "__main__":
    unittest.main()
