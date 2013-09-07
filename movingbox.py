import cairo
import gtk


DOT_SIZE = 30
ROWS = 18
COLS = 10

class Board(gtk.DrawingArea):
    def __init__(self):
        super(Board, self).__init__()
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color(0, 0, 0))
        self.set_size_request(COLS*DOT_SIZE, ROWS*DOT_SIZE)
        self.connect("expose-event", self.expose)
        self.runner = (4, 15)

    def expose(self, widget, event):
        print "expose called"
        cr = widget.window.cairo_create()
        cr.set_source_rgb(0, 0, 0)
        cr.paint()
        self.paint_square(self.runner[0], self.runner[1], 1.0, 0, 0, cr)  # red runner

    def paint_square(self, i, j, r, g, b, cr):
        print "calling paint_square"
        cr.set_source_rgb(r, g, b)
        cr.rectangle(i*DOT_SIZE+1, j*DOT_SIZE-1, DOT_SIZE-2, DOT_SIZE-2)
        cr.fill()

    def move_runner(self, i, j):
        x, y = self.runner
        self.runner = (x+i, y+j)
        self.queue_draw()

class MBWindow(gtk.Window):
    def __init__(self):
        super(MBWindow, self).__init__()
        self.board = Board()

        self.set_title("Moving Box")
        self.set_size_request(COLS*DOT_SIZE, ROWS*DOT_SIZE)
        self.set_resizable(False)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect("destroy", gtk.main_quit)
        self.connect("key-press-event", self.w_on_key_down)

        self.add(self.board)
        
        self.show_all()

    def w_on_key_down(self, widget, event):
        key = event.keyval
        if key == gtk.keysyms.Left:
            self.board.move_runner(-1, 0)
        elif key == gtk.keysyms.Up:
            self.board.move_runner(0, -1)
        elif key == gtk.keysyms.Right:
            self.board.move_runner(1, 0)
        elif key == gtk.keysyms.Down:
            self.board.move_runner(0, 1)
        elif key == gtk.keysyms.space:
            print "SPACE"

MBWindow()
gtk.main()
