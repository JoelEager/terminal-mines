"""
A simple minesweeper board solver. It selects known correct moves by deductive analysis rather than pre-determined 
patterns. For guesses it uses basic probabilistic calculation. As a result, the win rate is a bit lower than truly 
optimal play, but hopefully the implementation is more understandable. Includes a gameplay animation loop to display 
moves as they are made.
"""

from collections import defaultdict
from os import getenv
from random import shuffle, choice
from time import sleep

from click import echo

from .game_model import GameState, CellState
from .renderer import terminal_renderer

# Set this environment variable to enable debug messages for non-obvious AI moves, show end of game AI metrics, retain 
# previous game frames in the scrollback buffer, and disable the animation delay so the AI runs at max speed. If set to 
# "step" it will also pause after each debug message.
AI_DEBUG_MODE = getenv("MINES_AI_DEBUG", False)

# Utility lambda for the AI:
count_neighboring_numbers = lambda minefield, x, y: len([cell for cell in minefield.neighbors(x, y) if cell.state.value.isdigit()])


class Move:
    """
    Models a move for the AI. Includes optional fields for reporting metrics and debug messages about the selected move.
    """
    def __init__(self, func, x, y, metrics=[], debug=None):
        self.func = func
        self.x = x
        self.y = y
        self.metrics = metrics
        self.debug = debug


class SolverCell:
    """
    Stores attributes about a revealed number cell with unknown neighbors for use in the AI solver's analysis.
    """
    def __init__(self, x, y, cell, unknown_neighbors, num_flagged_neighbors):
        self.x = x
        self.y = y
        self.unknown_neighbors = unknown_neighbors
        self.num_neighboring_mines = int(cell.state.value)
        self.num_flagged_neighbors = num_flagged_neighbors
        self.num_remaining_mines = self.num_neighboring_mines - self.num_flagged_neighbors

    def __repr__(self):
        return f"({self.x}, {self.y}, n={self.num_neighboring_mines} rm={self.num_remaining_mines})"


def pick_move(minefield):
    """
    Returns the move the AI wants to take. First it attempts simple deduction. Then two cell deductive analysis. If
    neither of those work then it resorts to guessing.
    """
    # Pick a corner for the first move
    if minefield.first_move:
        x, y = choice([(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)])
        return Move(minefield.reveal_cell, x, y)

    # Pre-process the board to improve performance on cells that are analyzed multiple times
    number_cells_with_unknown_neighbors = []
    for x, y, cell in minefield.cords_and_cells:
        if cell.state.value.isdigit():
            unknown_neighbors = set()
            num_flagged_neighbors = 0
            for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y):
                neighbor = minefield.get_cell(neighbor_x, neighbor_y)
                if neighbor.state == CellState.UNKNOWN:
                    unknown_neighbors.add((neighbor_x, neighbor_y))
                elif neighbor.state == CellState.FLAGGED:
                    num_flagged_neighbors += 1
            
            if unknown_neighbors:
                number_cells_with_unknown_neighbors.append(SolverCell(x, y, cell, unknown_neighbors, num_flagged_neighbors))

    # If possible, place a flag via simple deduction
    for solver_cell in number_cells_with_unknown_neighbors:
        if solver_cell.num_remaining_mines == len(solver_cell.unknown_neighbors):
            # The only way for the remaining mines to fit is if every unknown neighbor is a mine
            return Move(minefield.flag_cell, *solver_cell.unknown_neighbors.pop())

    # If possible, reveal a cell via simple deduction
    for solver_cell in number_cells_with_unknown_neighbors:
        if solver_cell.num_remaining_mines == 0:
            # All mines are flagged, so every unknown neighbor is safe
            return Move(minefield.reveal_cell, *solver_cell.unknown_neighbors.pop())

    # Perform two cell analysis
    for solver_cell_a in number_cells_with_unknown_neighbors:
        for solver_cell_b in number_cells_with_unknown_neighbors:
            unknown_a_not_b = solver_cell_a.unknown_neighbors - solver_cell_b.unknown_neighbors
            unknown_both = solver_cell_a.unknown_neighbors & solver_cell_b.unknown_neighbors
            if unknown_a_not_b and unknown_both:
                # The preceding code has selected cells A and B such that:
                #  - Both are revealed numbers with unknown neighbors.
                #  - At least one cell is an unknown neighbor of A but not B.
                #  - A and B have at least one unknown neighbor in common

                if solver_cell_a.num_remaining_mines - solver_cell_b.num_remaining_mines == len(unknown_a_not_b):
                    # The only way for there to be room for all of A's remaining mines is if every unknown cell
                    # neighboring A but not B is a mine
                    return Move(minefield.flag_cell, *unknown_a_not_b.pop(), metrics=["two_cell_flag"], 
                                debug=f"Two cell flag A{solver_cell_a} B{solver_cell_b}")

                if solver_cell_a.num_remaining_mines == solver_cell_b.num_remaining_mines and \
                    solver_cell_a.unknown_neighbors > solver_cell_b.unknown_neighbors:
                    # A and B have the same number of remaining mines and B's unknown neighbors are a strict subset of 
                    # A's. Since all of B's remaining mines must also neighbor A, every unknown cell neighboring A but 
                    # not B is safe.
                    return Move(minefield.reveal_cell, *unknown_a_not_b.pop(), metrics=["two_cell_reveal"], 
                                debug=f"Two cell reveal A{solver_cell_a} B{solver_cell_b}")

    # Look for a low risk guess
    num_flags = minefield.count_cells_with_state(CellState.FLAGGED)
    num_unknown = minefield.count_cells_with_state(CellState.UNKNOWN)
    base_risk = (minefield.num_mines - num_flags) / num_unknown
    base_risk_debug = f"base risk of {base_risk}"
    risk = base_risk  # Start with the worst case risk
    best_guess = None

    for solver_cell in number_cells_with_unknown_neighbors:
        neighbor_risk = solver_cell.num_remaining_mines / len(solver_cell.unknown_neighbors)
        if neighbor_risk < risk:
            # Neighbors of this cell have a lower risk than what has been observed so far
            for candidate_x, candidate_y in solver_cell.unknown_neighbors:
                # Make sure the candidate guess hasn't had its risk influenced by another neighboring number
                if count_neighboring_numbers(minefield, candidate_x, candidate_y) == 1:
                    best_guess = (candidate_x, candidate_y)
                    risk = neighbor_risk
                    break

    if best_guess:
        return Move(minefield.reveal_cell, best_guess[0], best_guess[1], 
                    metrics=["low_risk_guesses", "all_guesses"], debug=f"Low risk guess of {risk} vs {base_risk_debug}")

    # Take a guess by revealing a random cell; preferably one not neighboring a revealed number
    all_unknown = [(x, y) for x, y, cell in minefield.cords_and_cells if cell.state == CellState.UNKNOWN]
    unknown_without_number_neighbors = [(x, y) for x, y in all_unknown if count_neighboring_numbers(minefield, x, y) == 0]

    if unknown_without_number_neighbors:
        shuffle(unknown_without_number_neighbors)
        return Move(minefield.reveal_cell, unknown_without_number_neighbors[0][0], unknown_without_number_neighbors[0][1],
                    metrics=["all_guesses"], debug=f"Greenfield guess ({base_risk_debug})")

    shuffle(all_unknown)
    return Move(minefield.reveal_cell, all_unknown[0][0], all_unknown[0][1], metrics=["all_guesses"], 
                debug=f"Fallback guess ({base_risk_debug})")


def solve_game(minefield):
    """
    Runs the AI against the given minefield. Renders the game after each move.
    """
    with terminal_renderer(overwrite=not AI_DEBUG_MODE) as render:
        render(minefield)
        metrics = defaultdict(int)
        while True:
            if not AI_DEBUG_MODE:
                sleep(0.1)

            # Make a move
            move = pick_move(minefield)
            move.func(move.x, move.y)

            # Update the AI statistics
            metrics["moves"] += 1
            for metric in move.metrics:
                metrics[metric] += 1

            # Update the selected cell to indicate the move the AI just made
            minefield.x = move.x
            minefield.y = move.y

            # Render the updated game state
            render(minefield)

            if AI_DEBUG_MODE and move.debug:
                echo(f" Move({move.x}, {move.y}): {move.debug}")
                if AI_DEBUG_MODE == "step":
                    input(" Press Enter to continue...")

            # Show additional end of game message(s)
            if minefield.state != GameState.IN_PROGRESS:
                if AI_DEBUG_MODE:
                    echo("\nMetrics:")
                    for metric, count in metrics.items():
                        echo(f" {metric}: {count}")
                else:
                    summary = f"\nThe AI made {metrics['moves']} moves "
                    if metrics["all_guesses"] == 0:
                        summary += "with no guesses."
                    elif metrics["all_guesses"] == 1:
                        summary += "of which 1 was a guess."
                    else:
                        summary += f"of which {metrics['all_guesses']} were guesses."
                    if minefield.state == GameState.LOST:
                        summary += " The last guess went poorly."
                    echo(summary)

                return metrics
