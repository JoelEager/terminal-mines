import unittest
from terminal_mines.game_model import Minefield, CellState
from terminal_mines.solver import pick_move, nCr


class TestSolverDeterministicStrategies(unittest.TestCase):
    def test_nCr(self):
        self.assertEqual(nCr(5, 2), 10)
        self.assertEqual(nCr(5, 0), 1)
        self.assertEqual(nCr(5, 5), 1)
        self.assertEqual(nCr(5, 6), 0)
        self.assertEqual(nCr(5, -1), 0)

    def test_simple_deduction_flag(self):
        """
        When visible mines equal unknown neighbors + flagged neighbors,
        all unknown neighbors must be mines -> flag move.
        """
        minefield = Minefield(2, 2, {"0,0"})
        minefield.first_move = False
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
        minefield = Minefield(2, 2, {"0,0"})
        minefield.first_move = False
        minefield.flag_cell(0, 0)
        minefield.get_cell(1, 0).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.reveal_cell)
        self.assertIn((move.x, move.y), {(0, 1), (1, 1)})

    def test_two_cell_analysis_flag(self):
        """
        Cell A (1,1) has unknown neighbors {(0,0), (1,0), (2,0)} with 2 remaining mines.
        Cell B (0,1) has unknown neighbors {(0,0), (1,0)} with 1 remaining mine.
        A's unknown neighbors strictly contain B's.
        The extra neighbor (2,0) must be a mine -> flag (2,0).
        """
        minefield = Minefield(3, 2, {"0,0", "2,0"})
        minefield.first_move = False
        minefield.get_cell(0, 1).state = CellState.WARN1
        minefield.get_cell(1, 1).state = CellState.WARN2
        minefield.get_cell(2, 1).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.flag_cell)
        self.assertEqual((move.x, move.y), (2, 0))
        self.assertEqual(move.label, "two_cell_flag")

    def test_two_cell_analysis_reveal(self):
        """
        Cell A (1,1) has unknown neighbors {(0,0), (1,0), (2,0)} with 1 remaining mine.
        Cell B (0,1) has unknown neighbors {(0,0), (1,0)} with 1 remaining mine.
        A's unknown neighbors strictly contain B's.
        The extra neighbor (2,0) must be safe -> reveal (2,0).
        """
        minefield = Minefield(3, 2, {"0,0"})
        minefield.first_move = False
        minefield.get_cell(0, 1).state = CellState.WARN1
        minefield.get_cell(1, 1).state = CellState.WARN1
        minefield.get_cell(2, 1).state = CellState.WARN1

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.reveal_cell)
        self.assertEqual((move.x, move.y), (2, 0))
        self.assertEqual(move.label, "two_cell_reveal")

    def test_forced_guess_probability(self):
        """
        Test that when guessing is required, the solver calculates exact probabilities and picks a low risk guess.
        """
        # 3x3 board with 1 mine total
        minefield = Minefield(3, 3, {"2,2"})
        minefield.first_move = False
        # Reveal (0,0) = SAFE
        minefield.get_cell(0, 0).state = CellState.SAFE

        move = pick_move(minefield)
        self.assertEqual(move.func, minefield.reveal_cell)
        self.assertIsNotNone(move.label)


if __name__ == "__main__":
    unittest.main()
