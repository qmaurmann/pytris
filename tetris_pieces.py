"""This module defines the seven tetris piece types L, J, T, I, S, Z, and O
with various rotate and move methods; see documentation for abstract Piece
class. Two other abstract classes are defined to handle different rotation
schemes; types L, J, and T rotate clockwise with period 4 around a particular
square (so extend abstract class CenteredPiece), while types I, S, and Z
"rotate" with period 2 (so extend abstract class Period2Piece). Type O defines
its own rotation scheme, by not rotating at all.

Module also exports the useful tuple_add function, as well as a list
CONCRETE_TYPES of all seven concrete piece classes.

@author Quinn Maurmann
"""

def tuple_add(s, t):
    """Adds two length-2 tuples component-wise."""
    a, b = s
    c, d = t
    return (a+c, b+d)


class Piece(object):
    """Abstract Piece class; no constructor. Factors out the common "move"
    functionality all concrete subclasses will need. Such subclasses must
    define the following instance variables and methods:

    base: a tuple of positions (themselves as (int, int) tuples)
    shift: an (int, int) tuple saying how far we've shifted from the base
    color: an RGB 3-tuple (of floats between 0 and 1).

    test_rotate(self): return a list of all positions that would be
        occupied if piece were rotated.
    confirm_rotate(self): modify base variable to confirm a rotation; should
        only be used in conjunction with test_rotate."""
    def occupying(self):
        """Return a list of all positions currently occupied."""
        return [tuple_add(pos, self.shift) for pos in self.base]

    def test_move(self, delta):
        """Return a list of all positions that *would* be occupied if piece
        were moved by tuple delta."""
        dshift = tuple_add(self.shift, delta)
        return [tuple_add(pos, dshift) for pos in self.base]

    def confirm_move(self, delta):
        """Modify shift variable to confirm a move. Should only be used in
        conjunction with test_move."""
        self.shift = tuple_add(self.shift, delta)


class CenteredPiece(Piece):
    """Abstract base class for L, J, and T pieces; no constructor. Factors
    out the common "rotate" functionality, defining test_rotate and
    confirm_rotate in terms of clockwise rotation around base point (0, 0).

    Concrete subclasses must still initialize base, shift, and color
    variables."""
    def test_rotate(self):
        return [tuple_add((-y, x), self.shift) for x, y in self.base]

    def confirm_rotate(self):
        self.base = tuple((-y, x) for x, y in self.base)

class LPiece(CenteredPiece):
    def __init__(self):
        self.base = ((-1, 0), (0, 0), (1, 0), (-1, 1))
        self.shift = (4, 0)
        self.color = (0, 0, 1)  # blue

class JPiece(CenteredPiece):
    def __init__(self):
        self.base = ((-1, 0), (0, 0), (1, 0), (1, 1))
        self.shift = (4, 0)
        self.color = (.9, 0, 1)  # magenta

class TPiece(CenteredPiece):
    def __init__(self):
        self.base = ((-1, 0), (0, 0), (1, 0), (0, 1))
        self.shift = (4, 0)
        self.color = (1, 1, 0)  # yellow


class Period2Piece(Piece):
    """Abstract base class for S, Z, I pieces. Factors out the common "rotate"
    functionality, defining test_rotate and confirm_rotate in terms of
    switching between two possible "base" states.

    Concrete subclasses must define the two_bases instance variable (along
    with shift and color); two_bases should be a 2-tuple of base states.

    Unlike the other abstract classes for pieces, Period2Piece actually *does*
    provide an __init__ method to set defaults for instance variables parity
    and base. Because it uses the two_bases variable to do so, concrete
    subclasses will have make their super __init__ call *after* defining
    two_bases."""
    def __init__(self):
        self.parity = 0
        self.base = self.two_bases[0]

    def test_rotate(self):
        opp = 1-self.parity
        return [tuple_add(pos, self.shift) for pos in self.two_bases[opp]]

    def confirm_rotate(self):
        self.parity = 1-self.parity
        self.base = self.two_bases[self.parity]

class IPiece(Period2Piece):
    def __init__(self):
        self.two_bases = (((-1, 0), (0, 0), (1, 0), (2, 0)),
                          ((0, -1), (0, 0), (0, 1), (0, 2)))
        super(IPiece, self).__init__()  # define two_bases first
        self.shift = (4, 0)
        self.color = (1, 0.3, 0)  # orange

class SPiece(Period2Piece):
    def __init__(self):
        self.two_bases = (((0, 0), (1, 0), (-1, 1), (0, 1)),
                          ((0, -1), (0, 0), (1, 0), (1, 1)))
        super(SPiece, self).__init__()  # define two_bases first
        self.shift = (4, 0)
        self.color = (0, 1, 1)  # cyan

class ZPiece(Period2Piece):
    def __init__(self):
        self.two_bases = (((-1, 0), (0, 0), (0, 1), (1, 1)),
                          ((1, -1), (0, 0), (1, 0), (0, 1)))
        super(ZPiece, self).__init__()  # define two_bases first
        self.shift = (4, 0)
        self.color = (0, 1, 0)  # green

class OPiece(Piece):
    """The OPiece defines its own rotation, by not rotating at all."""
    def __init__(self):
        self.base = ((0, 0), (0, 1), (1, 0), (1, 1))
        self.shift = (4, 0)
        self.color = (1, 0, 0)  # red
    def test_rotate(self):
        return self.occupying()
    def confirm_rotate(self):
        pass


CONCRETE_TYPES = [LPiece, JPiece, TPiece, IPiece, SPiece, ZPiece, OPiece]
