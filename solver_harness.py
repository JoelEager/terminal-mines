#!/usr/bin/env python3
"""
Dev tool for aggregating AI solver results.
"""

from collections import defaultdict
import multiprocessing
import os
from time import perf_counter
from unittest.mock import patch

import click

from terminal_mines.main import DifficultyParamType, create_minefield
from terminal_mines.solver import solve_game
from terminal_mines.game_model import GameState


def worker_func(worker_id, num_iterations, difficulty, mines_lines, queue):
    if num_iterations == 0:
        queue.put(("done", worker_id, 0, {}))
        return

    with patch("terminal_mines.solver.echo"), patch("terminal_mines.solver.sleep"), patch("terminal_mines.solver.terminal_renderer"):
        wins = 0
        total_metrics = defaultdict(int)

        for _ in range(num_iterations):
            minefield = create_minefield(None, difficulty, mines_lines)
            metrics = solve_game(minefield)

            if minefield.state == GameState.WON:
                wins += 1

            for metric, count in metrics.items():
                total_metrics[metric] += count

            queue.put(("progress", worker_id, 1))

        queue.put(("done", worker_id, wins, dict(total_metrics)))


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

    num_workers = os.cpu_count() or 1
    base_iterations = iterations // num_workers
    remainder = iterations % num_workers
    worker_iterations = [base_iterations + (1 if i < remainder else 0) for i in range(num_workers)]

    queue = multiprocessing.Queue()
    processes = []
    progress_bars = [
        click.progressbar(length=count, label=f"Worker {i + 1}")
        for i, count in enumerate(worker_iterations)
    ]

    for bar in progress_bars:
        bar.__enter__()

    start = perf_counter()

    for i in range(num_workers):
        p = multiprocessing.Process(
            target=worker_func,
            args=(i, worker_iterations[i], difficulty, mines_lines, queue)
        )
        p.start()
        processes.append(p)

    active_workers = num_workers
    total_metrics = defaultdict(int)
    wins = 0

    while active_workers > 0:
        msg_type, worker_id, arg1, *rest = queue.get()
        if msg_type == "progress":
            progress_bars[worker_id].update(arg1)
        elif msg_type == "done":
            active_workers -= 1
            worker_wins = arg1
            worker_metrics = rest[0]
            wins += worker_wins
            for metric, count in worker_metrics.items():
                total_metrics[metric] += count

    for p in processes:
        p.join()

    end = perf_counter()

    for bar in progress_bars:
        bar.__exit__(None, None, None)

    click.echo(f"Completed in {end - start:.1f} seconds. Win rate: {wins / iterations * 100:.1f}%")
    click.echo("Average metrics: " + ", ".join(
        f"{metric}={total / iterations:.2f}" for metric, total in sorted(total_metrics.items())
    ))


if __name__ == "__main__":
    main()
