"""
A minesweeper board solver. Includes logic to display moves as they are made.
"""
from random import randint, shuffle
from time import sleep

from .game_model import GameState, CellState
from .renderer import render


def take_action(func, x, y):
    """
    Utility function to update cursor and call an action function. Used by take_turn().
    """
    func.__self__.x = x
    func.__self__.y = y
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
            take_action(minefield.reveal_cell, x, y)
            return

    # Take a guess by revealing a random cell
    while True:
        x = randint(0, minefield.width - 1)
        y = randint(0, minefield.height - 1)

        if minefield.get_cell(x, y).state == CellState.UNKNOWN:
            take_action(minefield.reveal_cell, x, y)
            return


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
            return
