#!/usr/bin/env python3
"""
Dev tool for aggregating AI solver results.
"""

from collections import defaultdict
from unittest.mock import patch
from time import perf_counter

import click

from terminal_mines.main import DifficultyParamType, create_minefield
from terminal_mines.solver import solve_game
from terminal_mines.game_model import GameState


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
@click.argument("difficulty", default="balanced", type=DifficultyParamType())
@click.option("-m", "--mines", "mines_file", type=click.File(), help="Provide a file containing custom mine placements.")
@click.option("-i", "--iterations", default=100, type=int, help="Number of iterations to run the solver.")
def main(ctx, difficulty, mines_file, iterations):
    """
    Run the Terminal Mines AI solver repeatedly with the given game generation arguments. Reports the win rate and average metrics.
    """
    if iterations < 1:
        ctx.fail("Invalid number of iterations")

    total_metrics = defaultdict(int)
    wins = 0

    with patch("terminal_mines.solver.echo"), patch("terminal_mines.solver.sleep"), patch("terminal_mines.solver.render"), \
         click.progressbar(range(iterations), label="Solving games...") as bar:
        start = perf_counter()

        for _ in bar:
            minefield = create_minefield(ctx, difficulty, mines_file)
            metrics = solve_game(minefield)

            if minefield.state == GameState.WON:
                wins += 1

            for metric, count in metrics.items():
                total_metrics[metric] += count

        end = perf_counter()
    click.echo(f"Completed in {end - start:.1f} seconds. Win rate: {wins / iterations * 100:.1f}%")
    click.echo("Average metrics: " + ", ".join(f"{metric}={total / iterations:.2f}" for metric, total in total_metrics.items()))


if __name__ == "__main__":
    main()
