# Terminal Mines
A command-line variant of Minesweeper in Python.

![Screenshot](https://raw.githubusercontent.com/JoelEager/terminal-mines/master/screenshot.png "A game in progress")

Can be played in most terminal emulators for Linux, Mac, or Windows that support colors. Includes custom difficulties 
and a simple AI that you can watch attempt to solve the generated board.

Once installed, use the `mines` command to start a new game.

**For help, controls, and usage run `mines --help`.**

## Change log
- **v2.2**: Add timer that displays on game win and chording for faster reveals.
- **v2.1**: Fix incorrect difficulties for original Minesweeper. Further improvements to the AI solver. Remove the mines file feature.
- **v2.0**: Overhaul rendering to remove flicker and preserve scrollback buffer. Smarter AI solver, bug fixes, UI improvements, and a new difficulty preset.
- **v1.5**: Bug fixes for game status message and win detection.
- **v1.4**: Use the original Minesweeper win definition and ensure that the first move is always safe. Improve game status message.
- **v1.3**: Add simple AI solver.
- **v1.2**: New difficulty mode.
- **v1.1**: Bug fix for Windows.
- **v1.0**: Initial release.

## Installation
To install use pip:
```
pip install terminal-mines
```

To set the package up for local development run these commands:
```
git clone https://github.com/JoelEager/terminal-mines.git
cd terminal-mines
pip install --editable .
```

After doing that the `mines` command will point to the cloned version.
