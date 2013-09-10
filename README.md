Pytris
======

Tetris clone in Python 2.7.3 using GTK/Cairo (requires GTK 2.0). Tested in Ubuntu 12.04.

Play a game of Tetris by running

    python tetris.py

on the command line. Pieces are controlled with the arrow keys (up to rotate) and the space bar (to drop a piece to the bottom row).

The current piece falls one square every 2/(3+L) seconds, where L is the current level (starting at 1, increasing every 10 lines cleared).

When lines are cleared on level L, the player is awarded L times 40, 100, 300, or 1200 points, depending on whether 1, 2, 3, or 4 lines were cleared. When a player voluntarily lowers the current piece (with either down arrow or space bar), the player is awarded points equal to the distance lowered (independent of the level). This scoring scheme is taken from http://tetris.wikia.com/wiki/Scoring

Finally, if the code bears superficial similarity to the code for the Snake game at http://zetcode.com/gui/pygtk/snake/ it is because I used that Snake game as a template for interacting with GTK.
