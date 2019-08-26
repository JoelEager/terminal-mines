"""
A minesweeper board solver. Includes logic to display moves as they are made.
"""
from random import randint, shuffle
from time import sleep

from click import echo

from .game_model import GameState, CellState
from .renderer import render


class Stats:
    """
    Stores stats on the AI. This class is used as a singleton.
    """
    moves = 0
    guesses = 0
    last_move_guess = False


def take_action(func, x, y, guess=False):
    """
    Utility function to update cursor, increment stats, and call an action function. Used by take_turn().
    """
    func.__self__.x = x
    func.__self__.y = y

    Stats.moves += 1
    Stats.last_move_guess = guess
    if guess:
        Stats.guesses += 1

    func(x, y)


def take_turn(minefield):
    """
    Completes one turn for the AI. This function is ordered from "best" to "worst" strategy and returns once a valid
    move is found and taken.
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
                        take_action(minefield.flag_cell, neighbor_x, neighbor_y)
                        return

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
                        take_action(minefield.reveal_cell, neighbor_x, neighbor_y)
                        return

    # Take a guess by revealing a corner cell
    corners = [(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)]
    shuffle(corners)

    for x, y in corners:
        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            take_action(minefield.reveal_cell, x, y, guess=True)
            return

    # Take a guess by revealing a random cell
    while True:
        x = randint(0, minefield.width - 1)
        y = randint(0, minefield.height - 1)

        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            take_action(minefield.reveal_cell, x, y, guess=True)
            return


def print_stats(minefield):
    """
    Prints stats about actions taken by the AI. Called after a game ends.
    """
    message_format = "\n"
    if Stats.guesses == 1:
        message_format += "The AI made {} moves of which {} was a guess."
    else:
        message_format += "The AI made {} moves of which {} were guesses."

    if Stats.last_move_guess and minefield.state == GameState.LOST:
        message_format += " One of those guesses went poorly."

    echo(message_format.format(Stats.moves, Stats.guesses))


def solve_game(minefield):
    """
    Runs the AI against the given minefield. Renders game after each turn.
    """
    render(minefield)

    while True:
        sleep(0.1)

        take_turn(minefield)
        render(minefield)

        if minefield.state != GameState.IN_PROGRESS:
            print_stats(minefield)
            return
