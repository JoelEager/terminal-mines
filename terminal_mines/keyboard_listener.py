"""
An input loop based around click.getchar(). Supports arrow key escape sequences on both Unix-like platforms and Windows.

When run directly this this script will enter a test loop.
"""

from enum import Enum

import click


class ArrowKeyMapping(Enum):
    UP = "w"
    DOWN = "s"
    LEFT = "a"
    RIGHT = "d"


def input_loop(handler_func):
    """
    Loops until ESC is pressed or the program is killed. Calls handler_func each time a keystroke is received.
    """
    while True:
        try:
            ch = click.getchar()
        except (KeyboardInterrupt, EOFError):
            return

        # If it's an escape sequence grab the ascii char code
        if len(ch) > 1:
            escape_ord = ord(ch[0])
            ch = ch[-1]
        else:
            escape_ord = None

        if 32 <= ord(ch) <= 126:
            # Only pass "regular" keys onto the handler

            if escape_ord == 27 or escape_ord == 224:
                # Translate the arrow key escape sequence into the mapped letter
                if ch == "A" or ch == "H":
                    ch = ArrowKeyMapping.UP.value
                elif ch == "B" or ch == "P":
                    ch = ArrowKeyMapping.DOWN.value
                elif ch == "D" or ch == "K":
                    ch = ArrowKeyMapping.LEFT.value
                elif ch == "C" or ch == "M":
                    ch = ArrowKeyMapping.RIGHT.value

            handler_func(ch.lower())
        elif ord(ch) == 13:
            # Translate the enter key to a newline
            handler_func("\n")
        elif ord(ch) == 27:
            # Exit on ESC
            return


def demo_handler(key):
    print("Processing {}".format(repr(key)))


if __name__ == "__main__":
    input_loop(demo_handler)
