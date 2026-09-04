"""
An optimal Minesweeper board solver using exact probability calculations.

Divides unknown frontier cells into independent connected components, enumerates valid mine configurations via
constraint-pruned backtracking, combines components with interior cells using binomial coefficient math to account
for the total mine count, and derives exact mine probabilities for all cells.
"""

from collections import defaultdict
import math
from os import getenv
from random import choice
from time import sleep

from click import echo, pause

from .game_model import GameState, CellState
from .renderer import terminal_renderer

AI_DEBUG_MODE = getenv("MINES_AI_DEBUG", False)

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


class SolverCell:
    """
    Stores attributes about a revealed number cell with unknown neighbors for use in the AI solver's analysis.
    """
    def __init__(self, x, y, cell, unknown_neighbors, num_flagged_neighbors):
        self.x = x
        self.y = y
        self.unknown_neighbors = unknown_neighbors
        self.num_neighboring_mines = int(cell.state.value)
        self.num_flagged_neighbors = num_flagged_neighbors
        self.num_remaining_mines = self.num_neighboring_mines - self.num_flagged_neighbors

    def __repr__(self):
        return f"({self.x}, {self.y}, n={self.num_neighboring_mines} rm={self.num_remaining_mines})"


def nCr(n, r):
    """
    Combinations function nCr = n! / (r! * (n - r)!).
    """
    if r < 0 or r > n:
        return 0
    return math.comb(n, r)


def pick_move(minefield):
    """
    Returns the move the AI wants to take based on exact probability calculation and heuristic tie-breaking.
    """
    corners = [(0, 0), (0, minefield.height - 1), (minefield.width - 1, 0), (minefield.width - 1, minefield.height - 1)]
    if minefield.first_move:
        return Move(minefield.reveal_cell, *choice(corners))

    # Identify all unknown cells and active number cells with unknown neighbors
    all_unknown = set()
    number_cells = []

    for x, y, cell in minefield.cords_and_cells:
        if cell.state == CellState.UNKNOWN:
            all_unknown.add((x, y))
        elif cell.state.value.isdigit():
            unknown_neighbors = set()
            num_flagged_neighbors = 0
            for nx, ny in minefield.neighboring_cords(x, y):
                neighbor = minefield.get_cell(nx, ny)
                if neighbor.state == CellState.UNKNOWN:
                    unknown_neighbors.add((nx, ny))
                elif neighbor.state == CellState.FLAGGED:
                    num_flagged_neighbors += 1

            if unknown_neighbors:
                number_cells.append(SolverCell(x, y, cell, unknown_neighbors, num_flagged_neighbors))

    if not all_unknown:
        return Move(minefield.reveal_cell, 0, 0)

    # Simple deduction pass first (fast path & maintains exact legacy move labels where applicable)
    for sc in number_cells:
        if sc.num_remaining_mines == len(sc.unknown_neighbors):
            return Move(minefield.flag_cell, *sc.unknown_neighbors.pop())
        if sc.num_remaining_mines == 0:
            return Move(minefield.reveal_cell, *sc.unknown_neighbors.pop())

    # Check for two-cell deduction labels to maintain legacy test compatibility
    for sc_a in number_cells:
        for sc_b in number_cells:
            if sc_a is sc_b:
                continue
            diff_a_b = sc_a.unknown_neighbors - sc_b.unknown_neighbors
            common = sc_a.unknown_neighbors & sc_b.unknown_neighbors
            if diff_a_b and common:
                if sc_a.num_remaining_mines - sc_b.num_remaining_mines == len(diff_a_b):
                    return Move(minefield.flag_cell, *diff_a_b.pop(), label="two_cell_flag", debug=f"A{sc_a} B{sc_b}")
                if sc_a.num_remaining_mines == sc_b.num_remaining_mines and sc_a.unknown_neighbors > sc_b.unknown_neighbors:
                    return Move(minefield.reveal_cell, *diff_a_b.pop(), label="two_cell_reveal", debug=f"A{sc_a} B{sc_b}")

    # Build frontier and interior unknown cell sets
    frontier_unknowns = set()
    for sc in number_cells:
        frontier_unknowns.update(sc.unknown_neighbors)

    interior_unknowns = all_unknown - frontier_unknowns

    # Partition frontier unknowns into connected components
    cell_to_number_cells = defaultdict(list)
    for sc in number_cells:
        for cell_coord in sc.unknown_neighbors:
            cell_to_number_cells[cell_coord].append(sc)

    adjacency = defaultdict(set)
    for sc in number_cells:
        neighbors_list = list(sc.unknown_neighbors)
        for i in range(len(neighbors_list)):
            for j in range(i + 1, len(neighbors_list)):
                c1, c2 = neighbors_list[i], neighbors_list[j]
                adjacency[c1].add(c2)
                adjacency[c2].add(c1)

    visited_frontier = set()
    components = []

    for cell_coord in frontier_unknowns:
        if cell_coord not in visited_frontier:
            comp_cells = []
            queue = [cell_coord]
            visited_frontier.add(cell_coord)
            while queue:
                curr = queue.pop()
                comp_cells.append(curr)
                for neighbor in adjacency[curr]:
                    if neighbor not in visited_frontier:
                        visited_frontier.add(neighbor)
                        queue.append(neighbor)
            components.append(comp_cells)

    total_flags = minefield.count_cells_with_state(CellState.FLAGGED)
    remaining_total_mines = minefield.num_mines - total_flags

    # For each component, find all valid mine assignments via constraint-pruned backtracking
    comp_results = []

    for comp_cells in components:
        comp_cells_set = set(comp_cells)
        comp_scs = [sc for sc in number_cells if sc.unknown_neighbors & comp_cells_set]

        # Build local constraints for backtracking
        cell_to_idx = {coord: idx for idx, coord in enumerate(comp_cells)}

        constraints = []
        for sc in comp_scs:
            indices = [cell_to_idx[c] for c in sc.unknown_neighbors if c in comp_cells_set]
            constraints.append((sc.num_remaining_mines, indices))

        cell_constraints = [[] for _ in range(len(comp_cells))]
        for constr_idx, (rem_mines, indices) in enumerate(constraints):
            for idx in indices:
                cell_constraints[idx].append(constr_idx)

        valid_counts_by_mine_count = defaultdict(int)
        mine_counts_by_cell_and_mine_count = defaultdict(lambda: [0] * len(comp_cells))

        constr_current = [0] * len(constraints)
        constr_unassigned = [len(indices) for _, indices in constraints]

        assignment = [0] * len(comp_cells)

        def backtrack(cell_idx, current_mines):
            if current_mines > remaining_total_mines:
                return

            if cell_idx == len(comp_cells):
                valid_counts_by_mine_count[current_mines] += 1
                for idx, is_mine in enumerate(assignment):
                    if is_mine:
                        mine_counts_by_cell_and_mine_count[current_mines][idx] += 1
                return

            # Try assigning cell_idx = 0 (Safe)
            can_be_safe = True
            for constr_idx in cell_constraints[cell_idx]:
                req, _ = constraints[constr_idx]
                curr = constr_current[constr_idx]
                unas = constr_unassigned[constr_idx] - 1
                if curr + unas < req:
                    can_be_safe = False
                    break

            if can_be_safe:
                for constr_idx in cell_constraints[cell_idx]:
                    constr_unassigned[constr_idx] -= 1
                assignment[cell_idx] = 0
                backtrack(cell_idx + 1, current_mines)
                for constr_idx in cell_constraints[cell_idx]:
                    constr_unassigned[constr_idx] += 1

            # Try assigning cell_idx = 1 (Mine)
            can_be_mine = True
            for constr_idx in cell_constraints[cell_idx]:
                req, _ = constraints[constr_idx]
                curr = constr_current[constr_idx] + 1
                if curr > req:
                    can_be_mine = False
                    break

            if can_be_mine:
                for constr_idx in cell_constraints[cell_idx]:
                    constr_current[constr_idx] += 1
                    constr_unassigned[constr_idx] -= 1
                assignment[cell_idx] = 1
                backtrack(cell_idx + 1, current_mines + 1)
                for constr_idx in cell_constraints[cell_idx]:
                    constr_current[constr_idx] -= 1
                    constr_unassigned[constr_idx] += 1

        backtrack(0, 0)

        comp_results.append({
            'cells': comp_cells,
            'valid_counts': valid_counts_by_mine_count,
            'mine_counts_by_cell': mine_counts_by_cell_and_mine_count
        })

    # Global Combination Across Components & Interior
    num_components = len(comp_results)
    num_interior = len(interior_unknowns)

    def combine_components(comp_idx):
        if comp_idx == num_components:
            return {(): 1}

        res = {}
        sub = combine_components(comp_idx + 1)
        comp_valid_counts = comp_results[comp_idx]['valid_counts']

        for m_count, count in comp_valid_counts.items():
            for sub_tuple, sub_weight in sub.items():
                new_tuple = (m_count,) + sub_tuple
                res[new_tuple] = count * sub_weight
        return res

    combo_weights = combine_components(0)

    total_board_configs = 0
    cell_weighted_mine_counts = defaultdict(float)
    total_interior_mines_weighted = 0.0

    for mine_tuple, comp_weight in combo_weights.items():
        comp_mines_sum = sum(mine_tuple)
        rem_for_interior = remaining_total_mines - comp_mines_sum

        if rem_for_interior < 0 or rem_for_interior > num_interior:
            continue

        interior_combos = nCr(num_interior, rem_for_interior)
        combo_total_weight = comp_weight * interior_combos
        if combo_total_weight == 0:
            continue

        total_board_configs += combo_total_weight
        total_interior_mines_weighted += combo_total_weight * rem_for_interior

        for k in range(num_components):
            m_k = mine_tuple[k]
            m_k_weight_others = (comp_weight // comp_results[k]['valid_counts'][m_k]) * interior_combos
            cells = comp_results[k]['cells']
            mine_counts_for_mk = comp_results[k]['mine_counts_by_cell'][m_k]
            for idx, c in enumerate(cells):
                cell_weighted_mine_counts[c] += mine_counts_for_mk[idx] * m_k_weight_others

    cell_probabilities = {}

    if total_board_configs > 0:
        for c in frontier_unknowns:
            cell_probabilities[c] = cell_weighted_mine_counts[c] / total_board_configs

        interior_prob = (total_interior_mines_weighted / (num_interior * total_board_configs)) if num_interior > 0 else 0.0
        for c in interior_unknowns:
            cell_probabilities[c] = interior_prob
    else:
        base_risk = max(0.0, min(1.0, remaining_total_mines / max(1, len(all_unknown))))
        for c in all_unknown:
            cell_probabilities[c] = base_risk

    # Safe cells (Prob == 0)
    safe_cells = [c for c, p in cell_probabilities.items() if p <= 1e-12]
    if safe_cells:
        selected = safe_cells[0]
        return Move(minefield.reveal_cell, *selected)

    # Flagged mine cells (Prob == 1)
    mine_cells = [c for c, p in cell_probabilities.items() if p >= 1.0 - 1e-12]
    if mine_cells:
        selected = mine_cells[0]
        return Move(minefield.flag_cell, *selected)

    # Forced Guessing: find lowest risk cells
    min_prob = min(cell_probabilities.values())
    candidate_guesses = [c for c, p in cell_probabilities.items() if abs(p - min_prob) <= 1e-9]

    # Prioritized Tie-Breaking Heuristics:
    # Heuristic 1: Corners
    unknown_corners = [c for c in candidate_guesses if c in corners]
    if unknown_corners:
        return Move(minefield.reveal_cell, *choice(unknown_corners), label="corner_guess", debug=f"prob={min_prob:.4f}")

    # Heuristic 2: Greenfield / Interior cells
    greenfield_candidates = [c for c in candidate_guesses if count_neighboring_numbers(minefield, *c) == 0]
    if greenfield_candidates:
        return Move(minefield.reveal_cell, *choice(greenfield_candidates), label="greenfield_guess", debug=f"prob={min_prob:.4f}")

    # Heuristic 3: Low risk guess adjacent to numbers with maximum reveal potential
    best_guess = candidate_guesses[0]
    max_num_neighbors = -1

    for c in candidate_guesses:
        num_neighbors = count_neighboring_numbers(minefield, *c)
        if num_neighbors > max_num_neighbors:
            max_num_neighbors = num_neighbors
            best_guess = c

    return Move(minefield.reveal_cell, *best_guess, label="low_risk_guess", debug=f"prob={min_prob:.4f}")


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
                        metrics[f"killed_by_{move.label}"] = 1
                    echo(summary)

                return metrics
