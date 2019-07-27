from terminal_mines import GameState
from click import clear
from sys import exit


def render(minefield, x, y):
    clear()

    def render_cell(iter_x, iter_y):
        if iter_x == x and iter_y == y:
            return "@"
        else:
            return minefield.get_cell(iter_x, iter_y).state.value

    print("\n".join(" ".join(render_cell(iter_x, iter_y) for iter_x in range(minefield.width))
                    for iter_y in range(minefield.height)))

    if minefield.state == GameState.WON:
        print("Game won")
    elif minefield.state == GameState.LOST:
        print("Game lost")
    else:
        print("Flags remaining: {}".format(minefield.flags_remaining))

    print("Current cell:", minefield.get_cell(x, y).state.value)

    if minefield.state != GameState.IN_PROGRESS:
        exit(0)
