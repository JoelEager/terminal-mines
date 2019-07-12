from terminal_mines.game_model import Minefield, GameState
from terminal_mines.keyboard_listener import input_loop
from click import clear
from sys import exit

minefield = Minefield(10, 10, {"3,3", "8,8", "5,2", "0,4", "6,0"})

x = 0
y = 0


def render():
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

    render()


render()
input_loop(handle_key)
clear()
