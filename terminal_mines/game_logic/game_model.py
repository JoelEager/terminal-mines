"""
Models the game state and exposes functions for manipulating it.
"""

from enum import Enum
from random import randint


class CellState(Enum):
    UNKNOWN = "?"
    SAFE = "-"
    WARN1 = "1"
    WARN2 = "2"
    WARN3 = "3"
    WARN4 = "4"
    WARN5 = "5"
    WARN6 = "6"
    WARN7 = "7"
    WARN8 = "8"
    FLAGGED = "F"
    EXPLODED = "X"


class GameState(Enum):
    IN_PROGRESS = 0
    WON = 1
    LOST = 2


class Cell:
    """
    Represents one cell on the game board. The state is shown to the user while the is_mine value is used internally.
    """
    def __init__(self, is_mine):
        self.is_mine = is_mine
        self.state = CellState.UNKNOWN

    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__, self.is_mine, self.state.value)


class Minefield:
    """
    Stores the state of the game and the position of the cursor. Provides functions for interacting with the game.
    """
    def __init__(self, width, height, mines):
        """
        The mines arg must be a set of strings of the form "x,y".
        """
        self.width = width
        self.height = height

        self.x = 0      # The x cord of the currently selected cell
        self.y = 0      # The y cord of the currently selected cell
        self.state = GameState.IN_PROGRESS

        self.rows = [[Cell("{},{}".format(x, y) in mines) for x in range(width)] for y in range(height)]

    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__, self.width, self.height)

    @property
    def cells(self):
        for row in self.rows:
            for cell in row:
                yield cell

    @property
    def num_mines(self):
        return len([cell for cell in self.cells if cell.is_mine])

    @property
    def flags_remaining(self):
        return self.num_mines - len([cell for cell in self.cells if cell.state == CellState.FLAGGED])

    def get_cell(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.rows[y][x]
        else:
            raise IndexError

    def neighbors(self, x, y):
        """
        Iterates over neighboring cells
        """
        for offset_x, offset_y in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
            try:
                yield self.get_cell(x + offset_x, y + offset_y)
            except IndexError:
                continue

    def reveal_cell(self, x, y):
        """
        Reveals the given cell and updates the game state. Will recursively reveal other cells if the given one is safe.
        """
        target = self.get_cell(x, y)

        if target.state != CellState.UNKNOWN:
            return

        if target.is_mine:
            # Game lost; update all un-flagged mines as exploded
            target.state = CellState.EXPLODED
            
            for cell in self.cells:
                if cell.state == CellState.UNKNOWN and cell.is_mine:
                    cell.state = CellState.EXPLODED
                        
            self.state = GameState.LOST
        else:
            neighbor_mines = len([cell for cell in self.neighbors(x, y) if cell.is_mine])

            if neighbor_mines == 0:
                target.state = CellState.SAFE

                # Use recursion to propagate the reveal to neighboring cells
                for offset_x, offset_y in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
                    try:
                        self.reveal_cell(x + offset_x, y + offset_y)
                    except IndexError:
                        continue
            else:
                target.state = CellState(str(neighbor_mines))
                
    def flag_cell(self, x, y):
        """
        Toggles a cell between the unknown and flagged states. Does nothing if called on a revealed cell or if the
        player is out of flags.
        """
        target = self.get_cell(x, y)

        if target.state == CellState.FLAGGED:
            target.state = CellState.UNKNOWN
        elif target.state == CellState.UNKNOWN and self.flags_remaining > 0:
            target.state = CellState.FLAGGED

            # Check if the game has been won
            for cell in self.cells:
                if cell.is_mine and cell.state != CellState.FLAGGED:
                    return
                elif not cell.is_mine and cell.state == CellState.FLAGGED:
                    return

            self.state = GameState.WON


def random_minefield(num_mines, width, height):
    """
    :return: A new Minefield instance with a random set of mines.
    """
    mines = set()

    while len(mines) != num_mines:
        mines.add("{},{}".format(randint(0, width - 1), randint(0, height - 1)))

    return Minefield(width, height, mines)
