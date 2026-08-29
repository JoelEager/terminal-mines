"""
Handles the rendering of the game state to the console.
"""

from contextlib import contextmanager
from itertools import chain
from shutil import get_terminal_size

from click import style, echo, get_current_context

from .game_model import GameState, CellState

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


def style_cell(minefield, x, y):
    """
    Return a color styled character for the cell at the given position in the minefield.
    """
    cell = minefield.get_cell(x, y)

    fg = fg_mapping.get(cell.state, None)
    bg = None

    if minefield.state != GameState.WON and x == minefield.x and y == minefield.y:
        # Highlight the currently selected cell
        bg = "bright_green"
        fg = "black"            # Override the foreground color to make it more readable against the green background
    elif minefield.state == GameState.LOST and cell.state == CellState.FLAGGED and not cell.is_mine:
        # Indicate incorrectly placed flags
        bg = "red"

    return style(cell.state.value, bg=bg, fg=fg)


def generate_lines(minefield):
    """
    Generator to construct each line of the game board followed by the status message.
    """
    yield chr(0x250C) + chr(0x2500) * (minefield.width * 2 + 1) + chr(0x2510)

    for y in range(minefield.height):
        yield " ".join(chain(
            chr(0x2502), 
            (style_cell(minefield, x, y) for x in range(minefield.width)), 
            chr(0x2502)
        ))

    yield chr(0x2514) + chr(0x2500) * (minefield.width * 2 + 1) + chr(0x2518)

    if minefield.state == GameState.WON:
        yield " Game won"
    elif minefield.state == GameState.LOST:
        yield " Game lost"
    elif minefield.first_move:
        yield " First reveal is always safe"
    else:
        total_safe = minefield.width * minefield.height - minefield.num_mines
        remain_safe = total_safe - len([cell for cell in minefield.cells if cell.state == CellState.SAFE or cell.state.value.isdigit()])
        remain_str = "cell remains" if remain_safe == 1 else "cells remain"
        yield f" {minefield.count_cells_with_state(CellState.FLAGGED)} / {minefield.num_mines} marked; {remain_safe} safe {remain_str}"


@contextmanager
def terminal_renderer(overwrite=True):
    """
    Setup and tear down game rendering via ANSI escape sequences. If overwrite is disabled previous game frames will be 
    left in the scrollback buffer.
    """
    def render(minefield):
        """
        Render the current game state to the terminal.
        """
        frame = "\n".join(generate_lines(minefield))
        if overwrite:
            frame = "".join([
                "\033[H",  # Move the cursor to the top-left (home) position
                frame,
                "\033[K",  # Erase from the cursor position to the end of the line to hide remaining text from the previous status message
            ])

        try:
            echo(frame)
        except UnicodeEncodeError:
            # The Git Bash emulator on Windows doesn't support Unicode or the input loop; quit with a helpful message
            get_current_context().fail("Terminal Mines does not support the Git Bash emulator on Windows. Use Windows Terminal instead.")

    setup = "\033[?25l"  # Hide the cursor to prevent flicker/jumping
    if overwrite:
        # Clear the visible terminal screen while preserving the existing scrollback buffer
        setup += "\n" * get_terminal_size().lines
    echo(setup, nl=False)
    try:
        yield render
    finally:
        echo("\033[?25h", nl=False)  # Restore cursor visibility
