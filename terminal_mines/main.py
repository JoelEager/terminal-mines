"""
Entry point and CLI implementation for Terminal Mines.
"""

import click

from .game_model import random_minefield, Minefield, GameState
from .keyboard_listener import input_loop
from .renderer import terminal_renderer
from .solver import solve_game

DIFFICULTY_PRESETS = {
    "balanced": (35, 20, 15),
    "challenging": (70, 25, 20),
    "max": (150, 30, 30),
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
            self.fail(f"'{value}' is not a valid difficulty name", param, ctx)
        else:
            try:
                args = tuple(map(int, value.split(",")))

                if len(args) != 3:
                    raise ValueError
                elif args[0] <= 0 or args[1] <= 0 or args[2] <= 0:
                    raise ValueError
                elif args[1] > 30 or args[2] > 30:
                    self.fail("The game board cannot be larger than 30 cells on either side", param, ctx)
                elif args[0] >= args[1] * args[2]:
                    self.fail("The game board must have at least one safe cell", param, ctx)

                return args
            except ValueError:
                self.fail("A custom difficulty must be made of 3 positive integers separated by commas", param, ctx)


def create_minefield(ctx, difficulty, mines_file):
    """
    Creates a Minefield instance using a difficulty tuple and optional mines file.
    """
    if mines_file:
        mines = set(map(lambda line: line.strip(), mines_file))
        minefield = Minefield(difficulty[1], difficulty[2], mines)
        if minefield.num_mines == 0:
            ctx.fail("Mines file does not contain any valid mines")
        return minefield
    
    return random_minefield(*difficulty)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
@click.argument("difficulty", default="balanced", type=DifficultyParamType())
@click.option("-s", "--solve", is_flag=True, help="Watch the included AI attempt to solve the minefield.")
@click.option("-m", "--mines", "mines_file", type=click.File(), help="Provide a file containing custom mine placements.")
def main(ctx, difficulty, solve, mines_file):
    """
    Terminal Mines

    A command-line variant of Minesweeper in Python.

    \b
    Controls:
    - WASD or arrow keys to move the cursor
    - Enter or space to reveal the current cell
    - e or ' to place a flag
    - ESC to quit

    DIFFICULTY can either be one of the modes listed below or a custom difficulty of the form
    "<number of mines>,<width>,<height>". If no difficulty is specified, then Terminal Mines will default to balanced.

    \b
    Terminal Mines difficulties:
    - balanced: A 20x15 board with 35 mines
    - challenging: A 25x20 board with 70 mines
    - max: A 30x30 board with 150 mines

    \b
    Official Minesweeper difficulties:
    - easy: A 8x8 board with 10 mines
    - intermediate: A 16x16 board with 40 mines
    - expert: A 16x30 board with 99 mines

    The mines file (if provided) is used to control the placement of mines. It must be a CSV where each line is of the
    form "<x>,<y>". Both coordinates are 0-based and count from the top-left corner of the game board. If any of the
    specified mines are outside the bounds of the game board they will be skipped. If a mines file is provided the
    "number of mines" portion of the difficulty setting will be ignored. If the first move would reveal a mine it will
    be relocated to a random cell that does not contain a mine.
    """
    minefield = create_minefield(ctx, difficulty, mines_file)

    if solve:
        solve_game(minefield)
    else:
        with terminal_renderer() as render:
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
