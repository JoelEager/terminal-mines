import multiprocessing
import unittest
from solver_harness import worker_func
from terminal_mines.main import DIFFICULTY_PRESETS


class TestSolverHarness(unittest.TestCase):
    def test_worker_func(self):
        queue = multiprocessing.Queue()
        difficulty = DIFFICULTY_PRESETS["beginner"]
        worker_func(5, difficulty, None, queue)

        progress_count = 0
        done = False
        wins = 0
        metrics = {}

        for _ in range(5):
            msg = queue.get()
            if msg[0] == "progress":
                progress_count += 1
            elif msg[0] == "done":
                done = True
                wins = msg[1]
                metrics = msg[2]

        self.assertEqual(progress_count, 4)
        self.assertTrue(done)
        self.assertGreaterEqual(wins, 0)
        self.assertIn("moves", metrics)


if __name__ == "__main__":
    unittest.main()
