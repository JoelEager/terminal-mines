"""
Handles the rendering of the game state to the console.
"""

from itertools import chain

from click import clear, style, echo

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


def render(minefield):
    """
    Clears the screen and renders the current game state.
    """
    clear()

    def render_cell(iter_x, iter_y):
        cell = minefield.get_cell(iter_x, iter_y)

        fg = fg_mapping.get(cell.state, None)

        if iter_x == minefield.x and iter_y == minefield.y:
            bg = "green"
            fg = "black"    # Override the foreground color to make it more readable against the green background
        elif minefield.state != GameState.IN_PROGRESS and cell.state == CellState.FLAGGED:
            bg = None if cell.is_mine else "red"    # Indicates incorrectly placed flag
        else:
            bg = None

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
            yield " Flags remaining: {}".format(minefield.flags_remaining)

    echo("\n".join(gen_lines()))
