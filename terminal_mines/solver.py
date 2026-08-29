"""
A simple minesweeper board solver. Includes logic to display moves as they are made.
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


class Move:
    """
    Models a move for the AI. Includes optional fields for reporting metrics and debugging messages about the selected move.
    """
    def __init__(self, func, x, y, metrics=[], debug=None):
        self.func = func
        self.x = x
        self.y = y
        self.metrics = metrics
        self.debug = debug


def pick_move(minefield):
    """
    Returns the move the AI wants to take. First it attempts simple deduction. Then two cell deductive analysis. If
    neither of those work it resorts to guessing.
    """
    # Utility lambdas for the AI:
    #   Iterate over revealed cells with at least 1 neighboring mine
    iter_revealed_nums = lambda: ((x, y, cell) for x, y, cell in minefield.cords_and_cells if cell.state.value.isdigit())
    #   Iterate over the unknown neighbors of a given cell
    iter_unknown_neighbors = lambda x, y: (
        (neighbor_x, neighbor_y) for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y)
        if minefield.get_cell(neighbor_x, neighbor_y).state == CellState.UNKNOWN
    )
    #   Count the number of mines visible to a revealed number cell
    count_visible_mines = lambda cell: int(cell.state.value)
    #   Count the number of flagged neighbors
    count_flagged_neighbors = lambda x, y: len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.FLAGGED])
    #   Count the number of neighbors with a number state
    count_number_neighbors = lambda x, y: len([cell for cell in minefield.neighbors(x, y) if cell.state.value.isdigit()])

    # Pick a corner for the first move (which results in a better win probability)
    if minefield.first_move:
        x, y = choice([(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)])
        return Move(minefield.reveal_cell, x, y)

    # If possible, place a flag via simple deduction
    for x, y, cell in iter_revealed_nums():
        unknown_neighbors = list(iter_unknown_neighbors(x, y))
        if count_visible_mines(cell) == len(unknown_neighbors) + count_flagged_neighbors(x, y):
            # All unknown neighboring cells must be mines
            for neighbor_x, neighbor_y in unknown_neighbors:
                    return Move(minefield.flag_cell, neighbor_x, neighbor_y)

    # If possible, reveal a cell via simple deduction
    for x, y, cell in iter_revealed_nums():
        if count_visible_mines(cell) == count_flagged_neighbors(x, y):
            # All unknown neighboring cells must be safe
            for neighbor_x, neighbor_y in iter_unknown_neighbors(x, y):
                return Move(minefield.reveal_cell, neighbor_x, neighbor_y)

    # Perform two cell analysis
    for x_a, y_a, cell_a in iter_revealed_nums():
        unknown_neighbors_a = set(iter_unknown_neighbors(x_a, y_a))
        if unknown_neighbors_a:
            remaining_mines_a = count_visible_mines(cell_a) - count_flagged_neighbors(x_a, y_a)

            for x_b, y_b in minefield.neighboring_cords(x_a, y_a):
                cell_b = minefield.get_cell(x_b, y_b)
                if cell_b.state.value.isdigit():
                    unknown_neighbors_b = set(iter_unknown_neighbors(x_b, y_b))
                    if unknown_neighbors_b:

                        if unknown_neighbors_a > unknown_neighbors_b:
                            unknown_a_not_b = unknown_neighbors_a - unknown_neighbors_b
                            if unknown_a_not_b:
                                # The preceding code has selected cells A and B such that:
                                #  - Both are revealed numbers with unknown neighbors.
                                #  - B's unknown neighbors are a strict subset of A's.
                                #  - At least one cell is an unknown neighbor of A but not B.

                                remaining_mines_b = count_visible_mines(cell_b) - count_flagged_neighbors(x_b, y_b)
                                debug_details = f"cell A ({x_a}, {y_a}) has {remaining_mines_a} remaining mines; cell B ({x_b}, {y_b}) has {remaining_mines_b} remaining mines"

                                if remaining_mines_a - remaining_mines_b == len(unknown_a_not_b):
                                    # All unknown neighbors of A that are not neighbors of B must be mines
                                    return Move(minefield.flag_cell, *unknown_a_not_b.pop(), metrics=["two_cell_moves"], debug="Two cell flag; " + debug_details)
                                if remaining_mines_a - remaining_mines_b == 0:
                                    # All unknown neighbors of A that are not neighbors of B must be safe
                                    return Move(minefield.reveal_cell, *unknown_a_not_b.pop(), metrics=["two_cell_moves"], debug="Two cell reveal; " + debug_details)

    # Look for a low risk guess
    num_flags = minefield.count_cells_with_state(CellState.FLAGGED)
    num_unknown = minefield.count_cells_with_state(CellState.UNKNOWN)
    base_risk = (minefield.num_mines - num_flags) / num_unknown
    base_risk_debug = f"base risk of {base_risk}"
    risk = base_risk  # Start with the worst case risk
    best_guess = None

    for x, y, cell in iter_revealed_nums():
        unknown_neighbors = list(iter_unknown_neighbors(x, y))
        if unknown_neighbors:
            remaining_mines = count_visible_mines(cell) - count_flagged_neighbors(x, y)
            neighbor_risk = remaining_mines / len(unknown_neighbors)
            if neighbor_risk < risk:
                # Neighbors of this cell have a lower risk than what has been observed so far
                shuffle(unknown_neighbors)
                for candidate_x, candidate_y in unknown_neighbors:
                    # Make sure the candidate guess hasn't had its risk influenced by another neighboring number
                    if count_number_neighbors(candidate_x, candidate_y) == 1:
                        best_guess = (candidate_x, candidate_y)
                        risk = neighbor_risk
                        break

    if best_guess:
        return Move(minefield.reveal_cell, best_guess[0], best_guess[1], metrics=["low_risk_guesses", "all_guesses"], debug=f"Low risk guess of {risk} vs {base_risk_debug}")

    # Take a guess by revealing a random cell; preferably one not neighboring a revealed number
    all_unknown = [(x, y) for x, y, cell in minefield.cords_and_cells if cell.state == CellState.UNKNOWN]
    unknown_without_number_neighbors = [(x, y) for x, y in all_unknown if count_number_neighbors(x, y) == 0]

    if unknown_without_number_neighbors:
        shuffle(unknown_without_number_neighbors)
        return Move(minefield.reveal_cell, unknown_without_number_neighbors[0][0], unknown_without_number_neighbors[0][1],
                    metrics=["all_guesses"], debug=f"Greenfield guess ({base_risk_debug})")

    shuffle(all_unknown)
    return Move(minefield.reveal_cell, all_unknown[0][0], all_unknown[0][1], metrics=["all_guesses"], debug=f"Fallback guess ({base_risk_debug})")


def solve_game(minefield):
    """
    Runs the AI against the given minefield. Renders game after each move.
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
