#!/usr/bin/env python3
"""
Dev tool for aggregating AI solver results.
"""

from collections import defaultdict
from contextlib import contextmanager
from time import perf_counter
from unittest.mock import patch
import multiprocessing
import os

import click

from terminal_mines.main import DifficultyParamType, create_minefield
from terminal_mines.solver import solve_game
from terminal_mines.game_model import GameState


# No-op functions to efficiently replace unneeded output logic
def dummy_func(*args, **kwargs):
    pass


@contextmanager
def dummy_renderer(*args, **kwargs):
    yield dummy_func


def worker_func(num_iterations, difficulty, mines_lines, queue):
    """
    This function is run in each worker subprocess to solve its portion of the total number of games. Reports progress 
    and final results via the given message queue.
    """
    with patch("terminal_mines.solver.echo", dummy_func), \
         patch("terminal_mines.solver.sleep", dummy_func), \
         patch("terminal_mines.solver.terminal_renderer", dummy_renderer):
        for index in range(num_iterations):
            minefield = create_minefield(None, difficulty, mines_lines)
            metrics = solve_game(minefield)
            if minefield.state == GameState.WON:
                metrics["wins"] = 1
            queue.put((metrics, index + 1 == num_iterations))


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.pass_context
@click.argument("difficulty", default="balanced", type=DifficultyParamType())
@click.option("-m", "--mines", "mines_file", type=click.File(), help="Provide a file containing custom mine placements.")
@click.option("-i", "--iterations", default=1000, type=int, help="Number of iterations to run the solver.")
def main(ctx, difficulty, mines_file, iterations):
    """
    Run the Terminal Mines AI solver repeatedly with the given game generation arguments. Reports the win rate and average metrics.
    """
    if iterations < 1:
        ctx.fail("Invalid number of iterations")

    mines_lines = mines_file.readlines() if mines_file else None

    # Validate mines file / difficulty combination prior to spawning subprocesses
    create_minefield(ctx, difficulty, mines_lines)

    num_workers = min(os.cpu_count() or 2, iterations)
    base_iterations = iterations // num_workers
    remainder = iterations % num_workers
    worker_iterations = [base_iterations + (1 if index < remainder else 0) for index in range(num_workers)]

    queue = multiprocessing.Queue()  # Message queue for reporting results of each game
    active_workers = 0
    total_metrics = defaultdict(int)
    status_func = lambda _: f"({active_workers}/{num_workers} workers active)"

    with click.progressbar(length=iterations, label="Solving games...", item_show_func=status_func, 
                           show_pos=True, show_percent=False) as bar:
        worker_processes = []
        for index in range(num_workers):
            process = multiprocessing.Process(
                target=worker_func,
                args=(worker_iterations[index], difficulty, mines_lines, queue)
            )
            process.start()
            worker_processes.append(process)
            active_workers += 1

        start = perf_counter()
        while active_workers > 0:
            metrics, is_done = queue.get()
            for metric, count in metrics.items():
                total_metrics[metric] += count
            if is_done:
                active_workers -= 1
            bar.update(1)

        end = perf_counter()
        for process in worker_processes:
            process.join()

    # ANSI escape codes to move up one line and clear the line (hides the completed progress bar)
    click.echo("\x1b[1A\x1b[2K", nl=False)

    # Print the results
    fmt_iterations = iterations if iterations < 1000 else f"{iterations / 1000}k"
    win_percent = total_metrics["wins"] / iterations * 100
    click.echo(f"Completed {fmt_iterations} games in {end - start:.1f} seconds. Win rate: {win_percent:.1f}%")
    click.echo("Average metrics: " + ", ".join(
        f"{metric}={total / iterations:.2f}" for metric, total in sorted(total_metrics.items())
        if metric != "wins"
    ))


if __name__ == "__main__":
    main()
