import click
from sys import exit

from terminal_mines import random_minefield, GameState, input_loop, render

DIFFICULTY_PRESETS = {
    "easy": (10, 8, 8),
    "intermediate": (40, 16, 16),
    "expert": (99, 16, 30)
}


class DifficultyParamType(click.ParamType):
    """
    Converts the provided difficulty string into the 3 args expected by random_minefield().
    """
    def convert(self, value, param, ctx):
        if value in DIFFICULTY_PRESETS:
            return DIFFICULTY_PRESETS[value]
        elif "," not in value:
            self.fail("'{}' is not a valid difficulty name".format(value), param, ctx)
        else:
            try:
                args = tuple(map(int, value.split(",")))

                if len(args) != 3:
                    raise ValueError
                elif args[0] < 0 or args[1] < 0 or args[2] < 0:
                    raise ValueError
                elif args[1] > 50 or args[2] > 50:
                    self.fail("the game board cannot be larger than 50 cells on either side", param, ctx)
                elif args[0] > args[1] * args[2]:
                    self.fail("{} mines cannot fit in a board size of {} by {}".format(*args), param, ctx)

                return args
            except ValueError:
                self.fail("a custom difficulty must be made of 3 positive integers separated by commas", param, ctx)


@click.command()
@click.argument("difficulty", default="easy", type=DifficultyParamType())
def main(difficulty):
    """
    Terminal Mines

    A CLI port of Minesweeper in Python.

    DIFFICULTY can either be "easy", "intermediate", "expert" or a custom difficulty of the form
    "<number of mines>,<width>,<height>". If no difficulty is specified Terminal Mines will default to easy.
    """
    minefield = random_minefield(*difficulty)

    def handle_key(key):
        if key == "w":
            minefield.y = (minefield.y - 1) % minefield.height
        elif key == "s":
            minefield.y = (minefield.y + 1) % minefield.height
        elif key == "a":
            minefield.x = (minefield.x - 1) % minefield.width
        elif key == "d":
            minefield.x = (minefield.x + 1) % minefield.width
        elif key == "e" or key == "'":
            minefield.flag_cell(minefield.x, minefield.y)
        elif key == "\n" or key == " ":
            minefield.reveal_cell(minefield.x, minefield.y)

        render(minefield)

        if minefield.state != GameState.IN_PROGRESS:
            exit(0)

    render(minefield)
    input_loop(handle_key)


if __name__ == "__main__":
    main()
