"""
A minesweeper board solver. Includes logic to display moves as they are made.
"""
from random import randint, shuffle
from time import sleep

from click import echo

from .game_model import GameState, CellState
from .renderer import render


class Move:
    """
    Models a move for the AI.
    """
    def __init__(self, func, x, y, guess=False):
        self.func = func
        self.x = x
        self.y = y
        self.guess = guess


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
            unknown_neighbors = len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.UNKNOWN])
            flagged_neighbors = len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.FLAGGED])

            if state_num == unknown_neighbors + flagged_neighbors:
                # All unknown neighboring cells must be mines
                for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y):
                    if minefield.get_cell(neighbor_x, neighbor_y).state == CellState.UNKNOWN:
                        return Move(minefield.flag_cell, neighbor_x, neighbor_y)

    # Reveal a cell via process of elimination
    for x, y, cell in minefield.cords_and_cells:
        if cell.state.value.isdigit():
            # This cell is revealed and has at least 1 mine neighboring it
            state_num = int(cell.state.value)
            flagged_neighbors = len([cell for cell in minefield.neighbors(x, y) if cell.state == CellState.FLAGGED])

            if state_num == flagged_neighbors:
                # All unknown neighboring cells must be safe
                for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y):
                    if minefield.get_cell(neighbor_x, neighbor_y).state == CellState.UNKNOWN:
                        return Move(minefield.reveal_cell, neighbor_x, neighbor_y)

    # Take a guess by revealing a corner cell
    corners = [(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)]
    shuffle(corners)

    for x, y in corners:
        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            return Move(minefield.reveal_cell, x, y, guess=True)

    # Take a guess by revealing a random cell
    while True:
        x = randint(0, minefield.width - 1)
        y = randint(0, minefield.height - 1)

        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            return Move(minefield.reveal_cell, x, y, guess=True)


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

        minefield.x = move.x
        minefield.y = move.y

        moves += 1
        if move.guess:
            guesses += 1

        move.func(move.x, move.y)

        # Render the updated game state
        render(minefield)

        if minefield.state != GameState.IN_PROGRESS:
            # Print the stats info and return
            message_format = "\n"
            if guesses == 1:
                message_format += "The AI made {} moves of which {} was a guess."
            else:
                message_format += "The AI made {} moves of which {} were guesses."

            if move.guess and minefield.state == GameState.LOST:
                message_format += " One of those guesses went poorly."

            echo(message_format.format(moves, guesses))
            return
