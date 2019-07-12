from easy_getch import getch
from enum import Enum


class ArrowKeyMapping(Enum):
    UP = "w"
    DOWN = "s"
    LEFT = "a"
    RIGHT = "d"


def demo_handler(key):
    print("Processing {}".format(repr(key)))


def input_loop(handler_func):
    escape_pending = None   # Used to track the escape sequences created by pressing the arrow keys

    while True:
        try:
            ch = getch()
        except Exception:
            print("easy_getch failed due to unsupported environment")
            return

        if escape_pending == 27 and ch == "[":
            # Unix escape in progress, skip this character
            continue

        if 32 <= ord(ch) <= 126:
            # Only pass "regular" keys onto the handler

            if isinstance(ch, bytes):
                # Windows returns keys as bytes
                ch = ch.decode()

            if escape_pending == 27 or escape_pending == 224:
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
        elif ord(ch) == 27 or ord(ch) == 224:
            # Start of arrow key escape (Unix uses 27 and Windows uses 224)
            escape_pending = ord(ch)
            continue
        elif ord(ch) == 3 or ord(ch) == 4:
            # Respect ctrl+c and ctrl+d
            return

        escape_pending = None


if __name__ == "__main__":
    input_loop(demo_handler)
