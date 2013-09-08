import cairo
import glib
import gtk
import random


DOT_SIZE = 30
ROWS = 18
COLS = 10

def tuple_add(s, t):
    a, b = s
    c, d = t
    return (a+c, b+d)


class SquarePainter(gtk.DrawingArea):

    def __init__(self):
        super(SquarePainter, self).__init__()

    def paint_square(self, pos, color, cr):
        cr.set_source_rgb(*color)
        i, j = pos
        cr.rectangle(i*DOT_SIZE+1, j*DOT_SIZE-1, DOT_SIZE-2, DOT_SIZE-2)
        cr.fill()


class Board(SquarePainter):

    # annoying to have to pass these params explicitly
    def __init__(self, next_piece_display, level_display, lines_display, score_display):
        super(Board, self).__init__()
        #self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0,0,0))
        self.set_size_request(COLS*DOT_SIZE, ROWS*DOT_SIZE)
        self.connect("expose-event", self.expose)
        self.runner = (4, 15)

        self.next_piece_display = next_piece_display
        self.level_display = level_display
        self.lines_display = lines_display
        self.score_display = score_display

        self.level = 1
        self.lines = 0
        self.score = 0

        self.curr_piece = self.next_piece_display.get_piece()

        self.locked_squares = {}  # empty dict

        glib.timeout_add(1000, self.on_timer)

    def expose(self, widget, event):
        #print "expose called"
        cr = widget.window.cairo_create()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        for pos in self.curr_piece.occupying():
            self.paint_square(pos, self.curr_piece.color, cr)
        for pos, color in self.locked_squares.iteritems():
            self.paint_square(pos, color, cr)

    def move_curr_piece(self, delta):
        hypothetical = self.curr_piece.test_move(delta)
        if all(pos not in self.locked_squares and self.on_board(pos)
               for pos in hypothetical):
            self.curr_piece.confirm_move(delta)
        elif delta == (0,1):  # "illegal" down move
            self.lock_curr_piece()
        self.queue_draw()

    def rotate_curr_piece(self):
        hypothetical = self.curr_piece.test_rotate()
        if all(pos not in self.locked_squares and self.on_board(pos)
               for pos in hypothetical):
            self.curr_piece.confirm_rotate()
        self.queue_draw()

    def lock_curr_piece(self):
        for pos in self.curr_piece.occupying():
           self.locked_squares[pos] = self.curr_piece.color
        self.clear_rows()

        self.curr_piece = self.next_piece_display.get_piece()
        ## TODO: check that you didn't just lose
        self.next_piece_display.queue_draw()
        ## TODO: make bevahior more realistic here:
        #self.score += 1
        #self.score_display.set_text("Score: "+str(self.score))

    def clear_rows(self):
        """modifies locked_squares, level, lines, score if need be"""
        full_rows = [j for j in range(ROWS) if all(
                         (i, j) in self.locked_squares for i in range(COLS))]
        if not full_rows: return
        lo = min(full_rows)
        hi = max(full_rows)
        d = hi-lo+1
        new_ls = {}
        for (i,j), color in self.locked_squares.iteritems():
            if j > hi:
                new_ls[(i, j)] = color
            elif j < lo:
                new_ls[(i, j+d)] = color
        self.locked_squares = new_ls
        self.increment_score(self.level*{1:40, 2:100, 3:300, 4:1200}[d])
        self.lines += d
        self.level = self.lines // 10 + 1
        self.level_display.set_text("Level: "+str(self.level))
        self.lines_display.set_text("Lines: "+str(self.lines))

    def increment_score(self, x):  # because I might call more than 1nce
        self.score += x
        self.score_display.set_text("Score: "+str(self.score))
    

    def on_timer(self):
        return False

    def on_board(self, pos):
        i, j = pos
        return 0 <= i < COLS and 0 <= j < ROWS

class NextPieceDisplay(SquarePainter):
    def __init__(self):
        super(NextPieceDisplay, self).__init__()
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
        self.set_size_request(8*DOT_SIZE, 4*DOT_SIZE)

        self.connect("expose-event", self.expose)
        self.next_piece = self.create_piece()

    def expose(self, widget, event):
        cr = widget.window.cairo_create()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        for pos in self.next_piece.occupying():  ## TODO: not quite right
            self.paint_square(pos, self.next_piece.color, cr)

    def create_piece(self):
        tp = [LPiece, JPiece, TPiece][random.randrange(3)]
        return tp()

    def get_piece(self):
        old = self.next_piece
        new = self.create_piece()
        self.next_piece = new
        self.queue_draw()
        return old


class Piece(object):
    """Abstract class"""
    # self.base
    # self.shift
    # self.color
    def occupying(self):
        return [tuple_add(pos, self.shift) for pos in self.base]

    def test_move(self, delta):
        return [tuple_add(pos, delta) for pos in self.occupying()]

    def confirm_move(self, delta):
        self.shift = tuple_add(self.shift, delta)


class CenteredPiece(Piece):
    """Abstract class"""
    def test_rotate(self):
        return [tuple_add((-y, x), self.shift) for x, y in self.base]
    def confirm_rotate(self):
        self.base = [(-y, x) for x, y in self.base] 


class LPiece(CenteredPiece):
    def __init__(self):
        self.base = [(-1, 0), (0, 0), (1, 0), (-1, 1)]
        self.shift = (4, 0)
        self.color = (0, 0, 1)

class JPiece(CenteredPiece):
    def __init__(self):
        self.base = [(-1, 0), (0, 0), (1, 0), (1, 1)]
        self.shift = (4, 0)
        self.color = (1, 0, 1)

class TPiece(CenteredPiece):
    def __init__(self):
        self.base = [(-1, 0), (0, 0), (1, 0), (0, 1)]
        self.shift = (5, 0)
        self.color = (1, 1, 0)


class Main(gtk.Window):
    def __init__(self):
        super(Main, self).__init__()

        self.next_piece_display = NextPieceDisplay()
        self.level_display = gtk.Label("Level 1")
        self.lines_display = gtk.Label("Lines: 0")
        self.score_display = gtk.Label("Score: 0")

        self.board = Board(self.next_piece_display, self.level_display,
                           self.lines_display, self.score_display)

        self.set_title("Tetris")
        self.set_size_request(COLS*DOT_SIZE+350, ROWS*DOT_SIZE)  #TODO: actual size
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("destroy", gtk.main_quit)
        self.connect("key-press-event", self.w_on_key_down)

        self.hbox = gtk.HBox()
        self.add(self.hbox)
        self.hbox.add(self.board)

        self.vbox = gtk.VBox()
        self.hbox.add(self.vbox)

        self.vbox.add(self.next_piece_display)
        self.vbox.add(self.level_display)
        self.vbox.add(self.lines_display)
        self.vbox.add(self.score_display)
        
        self.show_all()

    def w_on_key_down(self, widget, event):
        key = event.keyval
        if key == gtk.keysyms.Left:
            self.board.move_curr_piece((-1, 0))
        elif key == gtk.keysyms.Up:
            self.board.rotate_curr_piece()
        elif key == gtk.keysyms.Right:
            self.board.move_curr_piece((1, 0))
        elif key == gtk.keysyms.Down:
            self.board.move_curr_piece((0, 1))
        elif key == gtk.keysyms.space:
            print "SPACE"

if __name__ == "__main__":
    Main()
    gtk.main()
    gtk.gdk.threads_init()  # Doesn't do anything??
