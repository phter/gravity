import tkinter as tk

class Container:
    """Container for widgets / other containers

        @parent     parent container

    Helper class to simplify layout generation:
    Tkinter doesn't like it, if a parent's .grid() method is called
    before .grid() has been called on all children. This class takes care
    of that:

        .layout()
            should create the layout of all widgets inside.
        .position(row, column)
            will call grid and make sure layout() gets called first,
            if it hasn't already been called.

    Generally speaking, there is no reason to call .layout() manually.
    Just call .position() as you would call .grid() on a widget.
    """

    logFmt = '{cls}: {msg}'

    def __init__(self, parent, logger=None):
        if parent is None:
            app = None
            parentFrame = None
        elif isinstance(parent, Container):
            app = parent.app
            parentFrame = parent.frame
        else:
            app = None
            parentFrame = parent

        self.logger = logger if logger is not None else print
        self.app = app
        self.frame = tk.Frame(parentFrame)
        self.hasLayout = False

    def position(self, row=None, column=None, **kwds):
        if not self.hasLayout:
            self.layout()
            self.hasLayout = True

        kwds['row'] = row if row is not None else 0
        kwds['column'] = column if column is not None else 0
        self.frame.grid(**kwds)

    # Stub, must be overridden by subclasses
    def layout(self):
        raise NotImplementedError("Missing layout method in " + self.__class__.__name__)

    def log(self, *args):
        self.logger(self.logFmt.format(cls=self.__class__.__name__,
                                       msg=' '.join(str(arg) for arg in args)))



class CanvasObject:
    """A (possibly compound) shape drawn on a canvas

        @canvas       the canvas this will be drawn to
        @pos          a numpy array with [x, y, ...]
        @tags         strings used as tags
        @kwds         additional drawing instructions
    """

    def __init__(self, canvas, pos, *tags, **kwds):
        self.canvas = canvas
        self.pos = pos[:2]  # this will be a view
        self.ids = None     # will be initialized by .create()
        self.kwds = kwds
        self.tags = dict((tag, True) for tag in tags)

    def show(self):
        for id in self.ids:
            self.canvas.itemconfigure(id, state=tk.NORMAL)

    def hide(self):
        for id in self.ids:
            self.canvas.itemconfigure(id, state=tk.HIDDEN)

    def draw(self):
        kwds = self.kwds.copy()
        kwds['tags'] = tuple(self.tags.keys())
        self.ids = tuple(self.create(**kwds))

    def create(self, **kwds):
        raise NotImplementedError('Missing create method')

    def move(self, vec):
        x, y = vec
        for id in self.ids:
            self.canvas.move(id, x, y)