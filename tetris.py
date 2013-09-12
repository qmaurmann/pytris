"""This is the main file for the Pytris project. The three concrete classes
defined herein are

Board: generally controls the flow of the game, e.g. interacting with the
    classes defined in tetris_pieces.py to determine whether and how pieces
    get moved around the board. Also responsible for displaying the state of
    the board.

NextPieceDisplay: is responsible for creating and displaying the next piece.

Main: a window containing a Board, a NextPieceDisplay, and other components
    relevant to the game state. The Board actually controls what happens to
    these components during game play.

Also defines an abstract class SquarePainter (extended by both Board and
NextPieceDisplay), and a convenience function styled_set_label_text.

@author Quinn Maurmann
"""

import pygtk
pygtk.require("2.0")
import cairo
import glib
import gtk
import random

import tetris_pieces
tuple_add = tetris_pieces.tuple_add  # too useful to call by namespace

DOT_SIZE = 30
ROWS = 18
COLS = 10


class SquarePainter(gtk.DrawingArea):
    """Abstract SquarePainter class factors out the ability to paint squares
    on a grid. Extended by both the Board and NextPieceDisplay classes."""

    def paint_square(self, pos, color, cr):
        """Paints a square on the grid at a particular (int, int) position.
        Color is given as an RGB triple (of floats between 0 and 1); cr is the
        Cairo context. Used only in the expose methods of Board and
        NextPieceDisplay"""
        cr.set_source_rgb(*color)
        i, j = pos
        cr.rectangle(i*DOT_SIZE+1, j*DOT_SIZE-1, DOT_SIZE-2, DOT_SIZE-2)
        cr.fill()


class Board(SquarePainter):
    """Board is responsible for handling all game logic and displaying
    state."""

    def __init__(self, next_piece_display, level_display, lines_display,
                 score_display):
        super(Board, self).__init__()
        self.set_size_request(COLS*DOT_SIZE, ROWS*DOT_SIZE)
        self.connect("expose-event", self.expose)

        self.next_piece_display = next_piece_display
        self.level_display = level_display
        self.lines_display = lines_display
        self.score_display = score_display

        self.level = 0
        self.lines = 0
        self.score = 0
        self.over = False

        self.increment_level()  # formats label and starts timer
        self.increment_lines(0)  # formats label
        self.increment_score(0)  # formats label
        self.curr_piece = self.next_piece_display.get_piece()
        self.locked_squares = {}  # (int,int): color dictionary


    def expose(self, widget, event):
        """Paint current piece and all locked squares; should only be called
        via self.queue_draw."""
        cr = widget.window.cairo_create()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        for pos, color in self.locked_squares.iteritems():
            self.paint_square(pos, color, cr)
        for pos in self.curr_piece.occupying():
            self.paint_square(pos, self.curr_piece.color, cr)
        ### Easiest to put "GAME OVER" message here ###
        if self.over:
            cr.select_font_face('Sans', cairo.FONT_SLANT_NORMAL,
                cairo.FONT_WEIGHT_BOLD)
            ### HACK: The following doesn't scale with DOT_SIZE ###
            cr.set_font_size(41)
            cr.move_to(10, 200)
            cr.set_source_rgb(0, 0, 0)  # dark drop-shadow
            cr.show_text('GAME OVER')
            cr.move_to(12, 202)
            cr.set_source_rgb(.82, .82, .82)  # light main text
            cr.show_text('GAME OVER')
            cr.stroke()

    def on_board(self, pos):
        """Determine whether a position is actually on the board."""
        i, j = pos
        return 0 <= i < COLS and 0 <= j < ROWS

    def can_move_curr_piece(self, delta):
        hypothetical = self.curr_piece.test_move(delta)
        return all(pos not in self.locked_squares and self.on_board(pos)
                   for pos in hypothetical)

    def move_curr_piece(self, delta, point=False):
        """Check the validity of a move, and conditionally perform it.
        One point may be granted, e.g. when the player moves the piece down
        voluntarily."""
        if self.over: return
        elif self.can_move_curr_piece(delta):
            self.curr_piece.confirm_move(delta)
            if point: self.increment_score(1)
        elif delta == (0,1):  # "illegal" down move
            self.lock_curr_piece()
        self.queue_draw()

    def drop_curr_piece(self):
        """Drop (and lock) curr_piece as far as possible, granting points
        equal to the distance of the drop."""
        if self.over: return
        delta = (0, 0)  # now make this as big as possible
        while True:
            new_delta = tuple_add(delta, (0, 1))
            if self.can_move_curr_piece(new_delta):
                delta = new_delta
            else:
                break
        self.increment_score(delta[1])
        self.move_curr_piece(delta)
        self.lock_curr_piece()
        self.queue_draw()

    def rotate_curr_piece(self):
        """Check the validity of a rotation, and conditionally perform it."""
        if self.over: return
        hypothetical = self.curr_piece.test_rotate()
        if all(pos not in self.locked_squares and self.on_board(pos)
               for pos in hypothetical):
            self.curr_piece.confirm_rotate()
        self.queue_draw()

    def lock_curr_piece(self):
        """Add squares of current piece to the collection of locked squares.
        Make calls to clear full rows, generate another piece, and check
        whether the game should end."""
        for pos in self.curr_piece.occupying():
           self.locked_squares[pos] = self.curr_piece.color
        self.clear_rows()
        self.curr_piece = self.next_piece_display.get_piece()
        if any(pos in self.locked_squares
                   for pos in self.curr_piece.occupying()):
            self.game_over()

    def game_over(self):
        """End the game. (Doesn't currently have to do much, because the
        actual painting is done conditionally in expose.)"""
        self.over = True

    def clear_rows(self):
        """Clear any full rows, modifying the variables locked_squares,
        level, lines, and score as appropriate."""
        ### Previous version had a bug, in that it assumed the set of ###
        ### indices of full rows had to be a contiguous sequence! ###
        full_rows = [j for j in range(ROWS) if all(
                         (i, j) in self.locked_squares for i in range(COLS))]
        if not full_rows: return
        ### Calculate how for to drop each other row, and do it ###
        drop = {j: len([k for k in full_rows if k > j]) for j in range(ROWS)}
        self.locked_squares = {(i, j+drop[j]): color for (i, j), color in
                            self.locked_squares.items() if j not in full_rows}
        ### Now just update score, etc. ###
        d = len(full_rows)
        self.increment_lines(d)
        self.increment_score(self.level*{1: 40, 2: 100, 3: 300, 4: 1200}[d])
        if self.level < self.lines // 10 + 1:
            self.increment_level()

    def increment_lines(self, d):
        """Increment lines by d, and change the label."""
        self.lines += d
        styled_set_label_text(self.lines_display, "Lines:  "+str(self.lines))

    def increment_score(self, x=1):
        """Increment score by x, and change the label."""
        self.score += x
        styled_set_label_text(self.score_display, "Score:  "+str(self.score))

    def increment_level(self):
        """Increment level by 1, and change the label. Also call make_timer
        and hook up the resulting function with glib.timeout_add, to be
        called  every 2.0/(level+3) seconds."""
        self.level += 1
        styled_set_label_text(self.level_display, "Level:  "+str(self.level))
        glib.timeout_add(2000//(self.level+3), self.make_timer(self.level))
    
    def make_timer(self, lev):
        """Creates a callback function on_timer, which moves current piece
        down (without granting a point). If the current level moves beyond
        lev, then on_timer will stop working, and will need to be replaced."""
        def on_timer():
            if (lev == self.level) and not self.over:  # finds lev in scope
                self.move_curr_piece((0, 1))
                return True
            else:
                return False  # kills on_timer
        return on_timer



class NextPieceDisplay(SquarePainter):
    """Responsible for both creating and showing new pieces."""

    def __init__(self):
        super(NextPieceDisplay, self).__init__()
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
        self.set_size_request(8*DOT_SIZE, 4*DOT_SIZE)

        self.connect("expose-event", self.expose)
        self.next_piece = self.create_piece()

    def expose(self, widget, event):
        """Displays the next piece; should only be called via
        self.queue_draw."""
        cr = widget.window.cairo_create()
        cr.set_source_rgb(0.05, 0.05, 0.05)
        cr.paint()
        for pos in self.next_piece.occupying():
            self.paint_square(tuple_add(pos, (-1, 1)),
                              self.next_piece.color, cr)

    def create_piece(self):
        """A Piece factory."""
        p_type = random.choice(tetris_pieces.CONCRETE_TYPES)
        return p_type()

    def get_piece(self):
        """Generates a new piece and shows it; returns the old piece.
        Analogous to next() operation for iterators."""
        old = self.next_piece
        new = self.create_piece()
        self.next_piece = new
        self.queue_draw()
        return old



class Main(gtk.Window):
    """Main window. Contains a Board and other relevant display objects. Is
    not responsible for any in-game control beyond passing simple instructions
    to the Board on keystroke events."""

    def __init__(self):
        super(Main, self).__init__()

        self.set_title("Tetris")
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("destroy", gtk.main_quit)
        self.connect("key-press-event", self.on_key_down)

        ### Create and reformat labels ###
        self.next_piece_words = gtk.Label("Undefined")
        self.level_display = gtk.Label("Undefined")
        self.lines_display = gtk.Label("Undefined")
        self.score_display = gtk.Label("Undefined")
        self.next_piece_words.set_alignment(.2, .4)
        self.level_display.set_alignment(.2, 0)
        self.lines_display.set_alignment(.2, 0)
        self.score_display.set_alignment(.2, 0)
        styled_set_label_text(self.next_piece_words, "Next Piece:")
        ### Note: Board automatically fixes other three labels ###

        self.next_piece_display = NextPieceDisplay()
        self.board = Board(self.next_piece_display, self.level_display,
                           self.lines_display, self.score_display)

        self.hbox = gtk.HBox()  # split screen into 2 panels
        self.add(self.hbox)
        self.hbox.add(self.board)  # left panel is Board

        self.vbox = gtk.VBox() # right panel has everything else in a VBox

        ### Have to wrap VBox in EventBox to change BG color ###
        self.vbox_wrapper = gtk.EventBox()
        self.vbox_wrapper.add(self.vbox)
        self.vbox_wrapper.modify_bg(gtk.STATE_NORMAL,
                                    gtk.gdk.Color(0.05, 0.05, 0.05))
        self.hbox.add(self.vbox_wrapper)

        self.vbox.add(self.next_piece_words)
        self.vbox.add(self.next_piece_display)
        self.vbox.add(self.level_display)
        self.vbox.add(self.lines_display)
        self.vbox.add(self.score_display)
        
        self.show_all()

    def on_key_down(self, widget, event):
        key = event.keyval
        if key == gtk.keysyms.Left:
            self.board.move_curr_piece((-1, 0))
        elif key == gtk.keysyms.Up:
            self.board.rotate_curr_piece()
        elif key == gtk.keysyms.Right:
            self.board.move_curr_piece((1, 0))
        elif key == gtk.keysyms.Down:
            self.board.move_curr_piece((0, 1), point=True)
        elif key == gtk.keysyms.space:
            self.board.drop_curr_piece()



def styled_set_label_text(label, text):
    """Set the text of a gtk.Label with the preferred markup scheme. (Simple
    enough not to be worth extending gtk.Label just for this method.)"""
    front = "<b><span foreground='#AAAAAA' size='large'>"
    end = "</span></b>"
    label.set_markup(front+text+end)



if __name__ == "__main__":
    Main()
    gtk.main()
