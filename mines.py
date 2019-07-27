from sys import exit

from terminal_mines import Minefield, GameState, input_loop, render

difficulty_presets = {
    "easy": (10, 8, 8),
    "intermediate": (40, 16, 16),
    "expert": (99, 16, 30)
}

minefield = Minefield(*difficulty_presets["easy"])

x = 0
y = 0


def handle_key(key):
    global x, y

    if key == "w":
        y = (y - 1) % minefield.height
    elif key == "s":
        y = (y + 1) % minefield.height
    elif key == "a":
        x = (x - 1) % minefield.width
    elif key == "d":
        x = (x + 1) % minefield.width
    elif key == "e":
        minefield.flag_cell(x, y)
    elif key == "\n":
        minefield.reveal_cell(x, y)

    render(minefield, x, y)

    if minefield.state != GameState.IN_PROGRESS:
        exit(0)


render(minefield, x, y)
input_loop(handle_key)
