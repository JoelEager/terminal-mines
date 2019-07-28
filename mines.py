import click
from sys import exit

from terminal_mines import random_minefield, GameState, input_loop, render

DIFFICULTY_PRESETS = {
    "easy": (10, 8, 8),
    "intermediate": (40, 16, 16),
    "expert": (99, 16, 30)
}


@click.command()
@click.option("-d", "--difficulty", type=click.Choice(list(DIFFICULTY_PRESETS.keys())), default="easy")
def main(difficulty):
    minefield = random_minefield(*DIFFICULTY_PRESETS[difficulty])

    def handle_key(key):
        if key == "w":
            minefield.y = (minefield.y - 1) % minefield.height
        elif key == "s":
            minefield.y = (minefield.y + 1) % minefield.height
        elif key == "a":
            minefield.x = (minefield.x - 1) % minefield.width
        elif key == "d":
            minefield.x = (minefield.x + 1) % minefield.width
        elif key == "e":
            minefield.flag_cell(minefield.x, minefield.y)
        elif key == "\n":
            minefield.reveal_cell(minefield.x, minefield.y)

        render(minefield)

        if minefield.state != GameState.IN_PROGRESS:
            exit(0)

    render(minefield)
    input_loop(handle_key)


if __name__ == "__main__":
    main()
