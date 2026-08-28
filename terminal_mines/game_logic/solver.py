"""
A simple minesweeper board solver. Includes logic to display moves as they are made.
"""
from random import randint, shuffle
from time import sleep

from click import echo

from .game_model import GameState, CellState
from .renderer import render

DEBUG_AI = True  # Set to True to show and pause for debug messages from the AI


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
    Returns the move the AI wants to take. This function is ordered from "best" to "worst" strategy and returns once a
    valid move is found.
    """
    # Place a flag via process of elimination
    for x, y, cell in minefield.cords_and_cells:
        if cell.state.value.isdigit():
            # This cell is revealed and has at least 1 mine neighboring it
            state_num = int(cell.state.value)
            num_unknown_neighbors = len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.UNKNOWN])
            num_flagged_neighbors = len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.FLAGGED])

            if state_num == num_unknown_neighbors + num_flagged_neighbors:
                # All unknown neighboring cells must be mines
                for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y):
                    if minefield.get_cell(neighbor_x, neighbor_y).state == CellState.UNKNOWN:
                        return Move(minefield.flag_cell, neighbor_x, neighbor_y)

    # Reveal a cell via process of elimination
    for x, y, cell in minefield.cords_and_cells:
        if cell.state.value.isdigit():
            # This cell is revealed and has at least 1 mine neighboring it
            state_num = int(cell.state.value)
            num_flagged_neighbors = len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.FLAGGED])

            if state_num == num_flagged_neighbors:
                # All unknown neighboring cells must be safe
                for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y):
                    if minefield.get_cell(neighbor_x, neighbor_y).state == CellState.UNKNOWN:
                        return Move(minefield.reveal_cell, neighbor_x, neighbor_y)

    # Perform two cell analysis
    for x_a, y_a, cell_a in minefield.cords_and_cells:
        if cell_a.state.value.isdigit():
            unknown_neighbors_a = {(x, y) for x, y in minefield.neighboring_cords(x_a, y_a) if minefield.get_cell(x, y).state == CellState.UNKNOWN}
            if unknown_neighbors_a:
                remaining_mines_a = int(cell_a.state.value) - len([cell for cell in minefield.neighbors(x_a, y_a) if cell.state == CellState.FLAGGED])

                for x_b, y_b in minefield.neighboring_cords(x_a, y_a):
                    cell_b = minefield.get_cell(x_b, y_b)
                    if cell_b.state.value.isdigit():
                        unknown_neighbors_b = {(x, y) for x, y in minefield.neighboring_cords(x_b, y_b) if minefield.get_cell(x, y).state == CellState.UNKNOWN}
                        if unknown_neighbors_b:

                            if unknown_neighbors_a > unknown_neighbors_b:
                                unknown_a_not_b = unknown_neighbors_a - unknown_neighbors_b
                                if unknown_a_not_b:
                                    # The preceding code has selected cells A and B such that:
                                    #  - Both are revealed numbers with unknown neighbors.
                                    #  - B's unknown neighbors are a strict subset of A's.
                                    #  - At least one cell is an unknown neighbor of A but not B.

                                    remaining_mines_b = int(cell_b.state.value) - len([cell for cell in minefield.neighbors(x_b, y_b) if cell.state == CellState.FLAGGED])
                                    debug_details = "Cell A ({}, {}) has {} remaining mines; Cell B ({}, {}) has {} remaining mines".format(x_a, y_a, remaining_mines_a, x_b, y_b, remaining_mines_b)

                                    if remaining_mines_a - remaining_mines_b == len(unknown_a_not_b):
                                        return Move(minefield.flag_cell, *unknown_a_not_b.pop(), debug="Two cell flag; " + debug_details)
                                    if remaining_mines_a - remaining_mines_b == 0:
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
    guesses = 0

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
            message_format = "\n"
            if guesses == 1:
                message_format += "The AI made {} moves of which {} was a guess."
            else:
                message_format += "The AI made {} moves of which {} were guesses."

            if move.guess and minefield.state == GameState.LOST:
                message_format += " One of those guesses went poorly."

            echo(message_format.format(moves, guesses))
            return
