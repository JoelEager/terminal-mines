"""
A simple minesweeper board solver. Includes logic to display moves as they are made.
"""
from random import randint, shuffle
from time import sleep

from click import echo

from .game_model import GameState, CellState
from .renderer import render

DEBUG_AI = False  # Set to True to show and pause for debug messages from the AI


class Move:
    """
    Models a move for the AI.
    """
    def __init__(self, func, x, y, guess=False, debug=None):
        self.func = func
        self.x = x
        self.y = y
        self.guess = guess
        self.debug = debug


def pick_move(minefield):
    """
    Returns the move the AI wants to take. First it attempts simple deduction. Then two cell deductive analysis. If 
    neither of those work it resorts to guessing. Corner guesses are preferred since they result in a higher win rate.
    """
    # Lambda: Iterate over revealed cells with at least 1 neighboring mine
    iter_revealed_nums = lambda: ((x, y, cell) for x, y, cell in minefield.cords_and_cells if cell.state.value.isdigit())

    # Lambda: Iterate over the unknown neighbors of a given cell
    iter_unknown_neighbors = lambda x, y: (
        (neighbor_x, neighbor_y) for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y)
        if minefield.get_cell(neighbor_x, neighbor_y).state == CellState.UNKNOWN
    )

    # Lambda: The number of mines visible to a revealed number cell
    count_visible_mines = lambda cell: int(cell.state.value)

    # Lambda: Count the number of flagged neighbors
    count_flagged_neighbors = lambda x, y: len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.FLAGGED])

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
                                debug_details = "cell A ({}, {}) has {} remaining mines; cell B ({}, {}) has {} remaining mines".format(x_a, y_a, remaining_mines_a, x_b, y_b, remaining_mines_b)

                                if remaining_mines_a - remaining_mines_b == len(unknown_a_not_b):
                                    # All unknown neighbors of A that are not neighbors of B must be mines
                                    return Move(minefield.flag_cell, *unknown_a_not_b.pop(), debug="Two cell flag; " + debug_details)
                                if remaining_mines_a - remaining_mines_b == 0:
                                    # All unknown neighbors of A that are not neighbors of B must be safe
                                    return Move(minefield.reveal_cell, *unknown_a_not_b.pop(), debug="Two cell reveal; " + debug_details)

    # Take a guess by revealing a corner cell
    corners = [(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)]
    shuffle(corners)

    for x, y in corners:
        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            return Move(minefield.reveal_cell, x, y, guess=True, debug="Corner guess")

    # Take a guess by revealing a random cell
    while True:
        x = randint(0, minefield.width - 1)
        y = randint(0, minefield.height - 1)

        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            return Move(minefield.reveal_cell, x, y, guess=True, debug="Random guess")


def solve_game(minefield):
    """
    Runs the AI against the given minefield. Renders game after each turn.
    """
    render(minefield)

    # Track some stats on the AI's attempt
    moves = 0
    guesses = -1  # Don't count the first guess because it's safe

    while True:
        sleep(0.1)

        # Make a move
        move = pick_move(minefield)
        move.func(move.x, move.y)

        # Update the selected cell to indicate the move the AI just made
        minefield.x = move.x
        minefield.y = move.y

        # Increment the stats
        moves += 1
        if move.guess:
            guesses += 1

        # Render the updated game state
        render(minefield)

        if DEBUG_AI and move.debug:
            print("AI debug ({}, {}): {}".format(move.x, move.y, move.debug))
            input("Press Enter to continue...")

        if minefield.state != GameState.IN_PROGRESS:
            # Print the stats and return
            message_format = "\nThe AI made {} moves "

            if guesses == 0:
                message_format += "with no risky guesses."
            elif guesses == 1:
                message_format += "of which {} was a risky guess."
                if minefield.state == GameState.LOST:
                    message_format += " That guess went poorly."
            else:
                message_format += "of which {} were risky guesses."
                if minefield.state == GameState.LOST:
                    message_format += " One of those guesses went poorly."

            echo(message_format.format(moves, guesses))
            return
