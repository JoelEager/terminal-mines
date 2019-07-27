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
    FLAG = "F"
    EXPLODED = "X"


class GameState(Enum):
    IN_PROGRESS = 0
    WON = 1
    LOST = 2


class Cell:
    def __init__(self, is_mine):
        self.is_mine = is_mine
        self.state = CellState.UNKNOWN

    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__, self.is_mine, self.state.value)


class Minefield:
    def __init__(self, width, height, mines):
        self.width = width
        self.height = height
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
        return self.num_mines - len([cell for cell in self.cells if cell.state == CellState.FLAG])

    def get_cell(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.rows[y][x]
        else:
            raise IndexError

    def neighbors(self, x, y):
        for offset_x, offset_y in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
            try:
                yield self.get_cell(x + offset_x, y + offset_y)
            except IndexError:
                continue

    def reveal_cell(self, x, y):
        target = self.get_cell(x, y)

        if target.state != CellState.UNKNOWN:
            return

        if target.is_mine:
            target.state = CellState.EXPLODED
            
            for cell in self.cells:
                if cell.state == CellState.UNKNOWN and cell.is_mine:
                    cell.state = CellState.EXPLODED
                        
            self.state = GameState.LOST
        else:
            neighbor_mines = len([cell for cell in self.neighbors(x, y) if cell.is_mine])

            if neighbor_mines == 0:
                target.state = CellState.SAFE

                for offset_x, offset_y in ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)):
                    try:
                        self.reveal_cell(x + offset_x, y + offset_y)
                    except IndexError:
                        continue
            else:
                target.state = CellState(str(neighbor_mines))
                
    def flag_cell(self, x, y):
        target = self.get_cell(x, y)

        if target.state == CellState.FLAG:
            target.state = CellState.UNKNOWN
            return
        elif target.state != CellState.UNKNOWN or self.flags_remaining == 0:
            return

        target.state = CellState.FLAG

        for cell in self.cells:
            if cell.is_mine and cell.state != CellState.FLAG:
                return
            elif not cell.is_mine and cell.state == CellState.FLAG:
                return

        self.state = GameState.WON


def random_minefield(num_mines, width, height):
    mines = set()

    while len(mines) != num_mines:
        mines.add("{},{}".format(randint(0, width - 1), randint(0, height - 1)))

    return Minefield(width, height, mines)
