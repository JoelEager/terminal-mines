"""
Entry point and CLI implementation for terminal-mines.
"""

import click

from .game_logic import random_minefield, Minefield, GameState, input_loop, render

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
@click.pass_context
@click.argument("difficulty", default="easy", type=DifficultyParamType())
@click.option("mines_file", "--mines", type=click.File(), help="File containing custom mine placements.")
def main(ctx, difficulty, mines_file):
    """
    Terminal Mines

    A command-line clone of Minesweeper in Python.

    \b
    Controls:
    - WASD or arrow keys to move the cursor
    - Enter or space to reveal the current cell
    - e or ' to place a flag
    - ESC to quit

    DIFFICULTY can either be "easy", "intermediate", "expert" or a custom difficulty of the form
    "<number of mines>,<width>,<height>". If no difficulty is specified Terminal Mines will default to easy.

    The mines file (if provided) is used to control the placement of mines. It must be a CSV where each line is of the
    form "<x>,<y>". Both coordinates are 0-based and count from the top-left corner of the game board. If any of the
    specified mines are outside the bounds of the game board they will be skipped. If a mines file is provided the
    "number of mines" portion of the difficulty setting will be ignored.
    """
    if mines_file:
        mines = set(map(lambda line: line.strip(), mines_file))
        minefield = Minefield(difficulty[1], difficulty[2], mines)

        if minefield.num_mines == 0:
            ctx.fail("Mines file did not contain any valid mines")
    else:
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
            ctx.exit(0)

    render(minefield)
    input_loop(handle_key)
