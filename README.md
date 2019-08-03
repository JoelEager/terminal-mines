# terminal-mines
A command-line clone of Minesweeper in Python.

Supports Linux, Mac, and Windows on Python 3.4 or newer. Can be played in most terminal emulators that support colors. 
Includes options for custom difficulties and user-specified mine placements.

To install use pip:
```
pip install terminal-mines
```

Once installed, use the `mines` command to start a new game.

**For help, controls, and usage run `mines --help` after installing.**

If you'd like to set `terminal-mines` up for local development run these commands:
```
git clone https://github.com/JoelEager/terminal-mines.git
cd terminal-mines
pip install --editable .
```

After doing that the `mines` command will point to your cloned copy.

`terminal-mines` is based on [Click](https://click.palletsprojects.com).
