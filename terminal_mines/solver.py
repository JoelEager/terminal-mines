"""
This branch implements an optimal Minesweeper board solver using set-based deduction and disjoint union analysis.

Selects moves by deductive analysis (set differences, subset reductions, and global disjoint unions)
with probabilistic calculations for guesses when no deduction is possible. Includes a gameplay animation loop.
"""

from collections import defaultdict
from os import getenv
from random import choice
from time import sleep

from click import echo, pause

from .game_model import GameState, CellState
from .renderer import terminal_renderer

# Set this environment variable to enable logging for non-obvious AI moves, show end of game metrics, retain previous 
# game frames in the scrollback buffer, and disable the animation delay so the AI runs at max speed. If set to "step" 
# it will also pause after each labeled move. If set to the same value as a move label it will pause after each move 
# with that label.
AI_DEBUG_MODE = getenv("MINES_AI_DEBUG", False)

# Utility lambda for the AI:
count_neighboring_numbers = lambda minefield, x, y: len([cell for cell in minefield.neighbors(x, y) if cell.state.value.isdigit()])


class Move:
    """
    Models a move for the AI. Includes optional fields for labeling the move and debugging information.
    """
    def __init__(self, func, x, y, label=None, debug=""):
        self.func = func
        self.x = x
        self.y = y
        self.label = label
        self.debug = debug


class MineSet:
    """
    Represents a set of unknown cells known to contain a specific number of mines.
    """
    __slots__ = ("cells", "mines", "is_derived")

    def __init__(self, cells, mines, is_derived=False):
        self.cells = cells  # frozenset of (x, y)
        self.mines = mines
        self.is_derived = is_derived

    def __repr__(self):
        return f"MineSet(n={len(self.cells)}, m={self.mines}, derived={self.is_derived})"


def get_known_sets(minefield):
    """
    Builds the initial list of sets from revealed number cells on the board.
    """
    sets = []
    for x, y, cell in minefield.cords_and_cells:
        if cell.state.value.isdigit():
            unknown_neighbors = []
            num_flagged_neighbors = 0
            for neighbor_x, neighbor_y in minefield.neighboring_cords(x, y):
                neighbor = minefield.get_cell(neighbor_x, neighbor_y)
                if neighbor.state == CellState.UNKNOWN:
                    unknown_neighbors.append((neighbor_x, neighbor_y))
                elif neighbor.state == CellState.FLAGGED:
                    num_flagged_neighbors += 1

            if unknown_neighbors:
                remaining_mines = int(cell.state.value) - num_flagged_neighbors
                sets.append(MineSet(frozenset(unknown_neighbors), remaining_mines, is_derived=False))
    return sets


def build_all_sets(minefield):
    """
    Derives new sets by pairwise subset reductions iteratively.
    """
    sets = get_known_sets(minefield)
    seen = {s.cells for s in sets}

    added = True
    while added:
        added = False
        new_sets = []
        n = len(sets)
        for i in range(n):
            for j in range(i + 1, n):
                s1, s2 = sets[i], sets[j]
                if s1.cells < s2.cells:
                    diff_cells = s2.cells - s1.cells
                    if diff_cells not in seen:
                        seen.add(diff_cells)
                        new_sets.append(MineSet(diff_cells, s2.mines - s1.mines, is_derived=True))
                        added = True
                elif s2.cells < s1.cells:
                    diff_cells = s1.cells - s2.cells
                    if diff_cells not in seen:
                        seen.add(diff_cells)
                        new_sets.append(MineSet(diff_cells, s1.mines - s2.mines, is_derived=True))
                        added = True

        if new_sets:
            sets.extend(new_sets)

    return sets


def find_deductive_move(minefield):
    """
    Attempts to find a guaranteed move using set deductions and global disjoint union analysis.
    Returns a Move object or None if no deterministic move can be made.
    """
    sets = build_all_sets(minefield)

    # 1. Single Set Deductions (includes base and derived subset differences)
    for s in sets:
        if not s.cells:
            continue
        if len(s.cells) == s.mines:
            target_cell = next(iter(s.cells))
            label = "single_derived_set_flag" if s.is_derived else "single_base_set_flag"
            return Move(minefield.flag_cell, *target_cell, label=label, debug=f"set={s}")
        if s.mines == 0:
            target_cell = next(iter(s.cells))
            label = "single_derived_set_reveal" if s.is_derived else "single_base_set_reveal"
            return Move(minefield.reveal_cell, *target_cell, label=label, debug=f"set={s}")

    # 2. Pairwise Set Wing / Overlap Deductions
    for i in range(len(sets)):
        s1 = sets[i]
        for j in range(i + 1, len(sets)):
            s2 = sets[j]
            common = s1.cells & s2.cells
            if not common:
                continue
            w1 = s1.cells - common
            w2 = s2.cells - common

            diff1 = s1.mines - s2.mines
            if len(w1) == diff1:
                if w1:
                    target_cell = next(iter(w1))
                    return Move(minefield.flag_cell, *target_cell, label="two_set_flag", debug=f"s1={s1}, s2={s2}")
                if w2:
                    target_cell = next(iter(w2))
                    return Move(minefield.reveal_cell, *target_cell, label="two_set_reveal", debug=f"s1={s1}, s2={s2}")

            diff2 = s2.mines - s1.mines
            if len(w2) == diff2:
                if w2:
                    target_cell = next(iter(w2))
                    return Move(minefield.flag_cell, *target_cell, label="two_set_flag", debug=f"s1={s1}, s2={s2}")
                if w1:
                    target_cell = next(iter(w1))
                    return Move(minefield.reveal_cell, *target_cell, label="two_set_reveal", debug=f"s1={s1}, s2={s2}")

    # 3. Global Disjoint Union Deductions
    all_unknown = frozenset((x, y) for x, y, cell in minefield.cords_and_cells if cell.state == CellState.UNKNOWN)
    flagged_count = minefield.count_cells_with_state(CellState.FLAGGED)
    global_mines_left = minefield.num_mines - flagged_count
    global_squares_left = len(all_unknown)

    if global_squares_left > 0 and (global_mines_left == 0 or global_mines_left == global_squares_left):
        target_cell = next(iter(all_unknown))
        if global_mines_left == 0:
            return Move(minefield.reveal_cell, *target_cell, label="union_reveal")
        else:
            return Move(minefield.flag_cell, *target_cell, label="union_flag")

    # Limit search for disjoint union combinations
    active_sets = [s for s in sets if s.cells and 0 < s.mines < len(s.cells)]
    unique_sets = []
    seen_cells = set()
    for s in active_sets:
        if s.cells not in seen_cells:
            seen_cells.add(s.cells)
            unique_sets.append(s)

    unique_sets.sort(key=lambda s: len(s.cells), reverse=True)
    candidate_sets = unique_sets[:10]

    def backtrack_disjoint(index, current_union_cells, current_mines):
        if index == len(candidate_sets):
            outside_squares = global_squares_left - len(current_union_cells)
            outside_mines = global_mines_left - current_mines
            if outside_squares > 0:
                if outside_mines == 0:
                    outside_cells = all_unknown - current_union_cells
                    return Move(minefield.reveal_cell, *next(iter(outside_cells)), label="backtrack_reveal")
                elif outside_mines == outside_squares:
                    outside_cells = all_unknown - current_union_cells
                    return Move(minefield.flag_cell, *next(iter(outside_cells)), label="backtrack_flag")
            return None

        s = candidate_sets[index]
        if not (s.cells & current_union_cells):
            move = backtrack_disjoint(index + 1, current_union_cells | s.cells, current_mines + s.mines)
            if move:
                return move

        return backtrack_disjoint(index + 1, current_union_cells, current_mines)

    if candidate_sets:
        move = backtrack_disjoint(0, frozenset(), 0)
        if move:
            return move

    return None


def pick_move(minefield):
    """
    Returns the move the AI wants to take.
    First attempts set-based deductive analysis and global disjoint union analysis.
    If no deductive move is found, resorts to optimal probabilistic / heuristic guessing.
    """
    corners = [(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)]
    if minefield.first_move:
        return Move(minefield.reveal_cell, *choice(corners))

    # Attempt deductive analysis
    deductive_move = find_deductive_move(minefield)
    if deductive_move:
        return deductive_move

    # Look for a low risk guess based on boundary unknown cells
    all_unknown = [(x, y) for x, y, cell in minefield.cords_and_cells if cell.state == CellState.UNKNOWN]
    if not all_unknown:
        return None

    global_flags = minefield.count_cells_with_state(CellState.FLAGGED)
    global_mines_left = max(0, minefield.num_mines - global_flags)
    base_risk = global_mines_left / len(all_unknown)
    best_risk = base_risk
    best_guess = None

    sets = get_known_sets(minefield)
    for s in sets:
        if s.cells and len(s.cells) > 0:
            neighbor_risk = s.mines / len(s.cells)
            if neighbor_risk < best_risk:
                for candidate_x, candidate_y in s.cells:
                    if count_neighboring_numbers(minefield, candidate_x, candidate_y) == 1:
                        best_guess = (candidate_x, candidate_y)
                        best_risk = neighbor_risk
                        break

    if best_guess:
        return Move(minefield.reveal_cell, *best_guess, label="low_risk_guess", debug=f"{best_risk} vs {base_risk}")

    # Pick an unknown corner if available
    unknown_corners = [(x, y) for x, y in corners if minefield.get_cell(x, y).state == CellState.UNKNOWN]
    if unknown_corners:
        return Move(minefield.reveal_cell, *choice(unknown_corners), label="corner_guess", debug=base_risk)

    # Greenfield guess (cell not neighboring any revealed number)
    unknown_no_number_neighbors = [(x, y) for x, y in all_unknown if count_neighboring_numbers(minefield, x, y) == 0]
    if unknown_no_number_neighbors:
        return Move(minefield.reveal_cell, *choice(unknown_no_number_neighbors), label="greenfield_guess", debug=base_risk)

    return Move(minefield.reveal_cell, *choice(all_unknown), label="fallback_guess", debug=base_risk)


def solve_game(minefield):
    """
    Runs the AI against the given minefield. Renders the game after each move.
    """
    with terminal_renderer(overwrite=not AI_DEBUG_MODE) as render:
        render(minefield)
        metrics = defaultdict(int)
        while True:
            if not AI_DEBUG_MODE:
                sleep(0.1)

            # Make a move
            move = pick_move(minefield)
            move.func(move.x, move.y)

            # Update the selected cell to indicate the move the AI just made
            minefield.x = move.x
            minefield.y = move.y

            # Render the updated game state
            render(minefield)

            # Update the AI metrics
            metrics["moves"] += 1
            if move.label:
                metrics[move.label] += 1
                if "guess" in move.label:
                    metrics["all_guesses"] += 1
                if AI_DEBUG_MODE:
                    echo(f" Move({move.x}, {move.y}, {move.label}) {move.debug}")
                    if AI_DEBUG_MODE == "step" or AI_DEBUG_MODE == move.label:
                        pause()

            # Show additional end of game message(s)
            if minefield.state != GameState.IN_PROGRESS:
                if AI_DEBUG_MODE:
                    echo("\nMetrics:")
                    for metric, count in metrics.items():
                        echo(f" {metric}: {count}")
                else:
                    summary = f"\nThe AI made {metrics['moves']} moves "
                    if metrics["all_guesses"] == 0:
                        summary += "with no guesses."
                    elif metrics["all_guesses"] == 1:
                        summary += "of which 1 was a guess."
                    else:
                        summary += f"of which {metrics['all_guesses']} were guesses."
                    if minefield.state == GameState.LOST:
                        summary += " The last guess went poorly."
                        # Extra metric for the solver harness to aggregate causes of lost games
                        metrics[f"killed_by_{move.label}"] = 1
                    echo(summary)

                return metrics
