"""
Handles the rendering of the game state to the console.
"""

from itertools import chain

from click import clear, style, echo, get_current_context

from .game_model import UNREVEALED_CELL_STATES, GameState, CellState

fg_mapping = {
    CellState.FLAGGED: "bright_green",
    CellState.WARN1: "bright_cyan",
    CellState.WARN2: "cyan",
    CellState.WARN3: "bright_blue",
    CellState.WARN4: "bright_magenta",
    CellState.WARN5: "magenta",
    CellState.WARN6: "bright_yellow",
    CellState.WARN7: "red",
    CellState.WARN8: "red",
    CellState.EXPLODED: "bright_red"
}


def render(minefield):
    """
    Clears the screen and renders the current game state.
    """
    clear()

    def render_cell(iter_x, iter_y):
        cell = minefield.get_cell(iter_x, iter_y)

        fg = fg_mapping.get(cell.state, None)
        bg = None

        if minefield.state != GameState.WON and iter_x == minefield.x and iter_y == minefield.y:
            # Highlight the currently selected cell
            bg = "bright_green"
            fg = "black"            # Override the foreground color to make it more readable against the green background
        elif minefield.state != GameState.IN_PROGRESS and cell.state == CellState.FLAGGED and not cell.is_mine:
            # Indicate incorrectly placed flag
            bg = "red"

        return style(cell.state.value, bg=bg, fg=fg)

    def gen_lines():
        yield chr(0x250C) + chr(0x2500) * (minefield.width * 2 + 1) + chr(0x2510)

        for iter_y in range(minefield.height):
            iter_cells = (render_cell(iter_x, iter_y) for iter_x in range(minefield.width))
            yield " ".join(chain(chr(0x2502), iter_cells, chr(0x2502)))

        yield chr(0x2514) + chr(0x2500) * (minefield.width * 2 + 1) + chr(0x2518)

        if minefield.state == GameState.WON:
            yield " Game won"
        elif minefield.state == GameState.LOST:
            yield " Game lost"
        else:
            total_safe = minefield.width * minefield.height - minefield.num_mines
            remain_safe = total_safe - minefield.count_cells_with_state(CellState.SAFE)
            yield " {} / {} marked; {} safe {}".format(
                minefield.count_cells_with_state(CellState.FLAGGED),
                minefield.num_mines, 
                remain_safe, 
                "cell remains" if remain_safe == 1 else "cells remain"
            )

    try:
        echo("\n".join(gen_lines()))
    except UnicodeEncodeError:
        # The Git bash emulator on Windows doesn't support unicode or the input loop; quit with a helpful message
        get_current_context().fail("terminal-mines does not support the Git bash emulator on Windows. Please use CMD "
                                   "or PowerShell instead.")
