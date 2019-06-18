"""Graphical user interface"""

import time
from concurrent.futures import ThreadPoolExecutor, wait as waitForFuture
import tempfile
from traceback import TracebackException

import tkinter as tk
import numpy as np
from matplotlib.figure import Figure as mplFigure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import PIL
from PIL.ImageTk import PhotoImage as tkPhotoImage
import PIL.ImageEnhance

from util import log
from config import Config
from game import Game
from geometry import Point, Circle


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

    def __init__(self, parent):
        if parent is None:
            app = None
            parentFrame = None
        elif isinstance(parent, Container):
            app = parent.app
            parentFrame = parent.frame
        else:
            app = None
            parentFrame = parent

        self.app = app
        self.frame = tk.Frame(parentFrame)
        self.hasLayout = False

    def position(self, row=None, column=None, **kwds):
        if not self.hasLayout:
            self.layout()
            self.hasLayout = True

        kwds['row'] = row
        kwds['column'] = column
        self.frame.grid(**kwds)

    # Stub, must be overridden by subclasses
    def layout(self):
        raise NotImplementedError("Missing layout method in " + self.__class__.__name__)


def sliderRow(frame, **desc):
    """Return a Label, Scale widget pair"""

    text = desc.get('text', '')
    del desc['text']
    if 'length' not in desc:
        desc['length'] = Config.sliderWidth
    if 'orient' not in desc:
        desc['orient'] = tk.HORIZONTAL

    slider = tk.Scale(frame, **desc)
    label = tk.Label(frame, text=text)
    return (label, slider)


class Sliders(Container):
    """Sliders for game settings

        @parent      parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.sliders = []

        var = self.app.settingVariables
        s = self.app.settings
        sliders = [
                {'variable': var['s_planetSize'],
                 'text': 'Planet size',
                 'from_': s.s_planetSizeRange.start,
                 'to': s.s_planetSizeRange.end,
                 'resolution': 0.1
                 },
                 {'variable': var['s_planetDensity'],
                 'text': 'Planet density',
                 'from_': s.s_planetDensityRange.start,
                 'to': s.s_planetDensityRange.end,
                 'resolution': 0.1
                 },
                 {'variable': var['s_planetRotation'],
                 'text': 'Rotation speed',
                 'from_': s.s_planetRotationRange.start,
                 'to': s.s_planetRotationRange.end,
                 'resolution': 0.1
                 },
                 {'variable': var['s_gravityConstant'],
                  'text': 'Gravity',
                  'from_': s.s_gravityConstantRange.start,
                  'to': s.s_gravityConstantRange.end,
                  'resolution': 0.1
                 },
                 {'variable': var['planetSpread'],
                 'text': 'Planet distance',
                 'from_': s.planetSpreadRange.start,
                 'to': s.planetSpreadRange.end,
                 'resolution': 0.1
                 },
                 {'variable': var['nSmallPlanets'],
                  'text': 'Number of small planets',
                  'from_': s.nSmallPlanetsRange.start,
                  'to': s.nSmallPlanetsRange.end,
                  'resolution': 1
                 },
                 {'variable': var['nNormalPlanets'],
                  'text': 'Number of normal planets',
                  'from_': s.nNormalPlanetsRange.start,
                  'to': s.nNormalPlanetsRange.end,
                  'resolution': 1
                 },
                 {'variable': var['nLargePlanets'],
                  'text': 'Number of large planets',
                  'from_': s.nLargePlanetsRange.start,
                  'to': s.nLargePlanetsRange.end,
                  'resolution': 1
                 },
                 {'variable': var['nBlackPlanets'],
                  'text': 'Number of black holes',
                  'from_': s.nBlackPlanetsRange.start,
                  'to': s.nBlackPlanetsRange.end,
                  'resolution': 1
                  },
                  {'variable': var['s_blackDensity'],
                  'text': 'Black hole mass',
                  'from_': s.s_blackDensityRange.start,
                  'to': s.s_blackDensityRange.end,
                  'resolution': 0.1
                 },
                  ]

        for desc in sliders:
            row = sliderRow(self.frame, **desc)
            self.sliders.append(row)

    def layout(self):
        for i, (label, slider) in enumerate(self.sliders):
            label.grid(row=i, column=0, sticky=tk.E)
            slider.grid(row=i, column=1)


class AppButtons(Container):
    """Main control buttons for the app

        @parent     parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.quitButton = tk.Button(self.frame, text='Quit', command=self.app.quit)
        self.playButton = tk.Button(self.frame, text='New Game', command=self.app.startGame)
        self.restartButton = tk.Button(self.frame, text='Restart', command=self.app.restartGame)

    def layout(self):
        self.restartButton.grid(row=0, column=0, pady=30)
        self.playButton.grid(row=0, column=1, pady=30)
        self.quitButton.grid(row=0, column=2, pady=30, padx=20)


class Clock(Container):
    """Clock display

        @parent       parent container
    """

    fmtString = '{:02}d {:02}h {:02}m {:02}s'

    def __init__(self, parent):
        Container.__init__(self, parent)

        self.textVar = self.app.textVariables['gameTime']
        self.label = tk.Label(self.frame,
                              width=18,
                              textvariable=self.textVar,
                              bg=Config.colors['clockBackground'].tkString())
        self.app.components.Clock = self

    def layout(self):
        self.label.grid()

    def update(self, t):
        t = int(t)
        m = t // 60
        h = m // 60
        cm = m % 60
        ch = h % 24
        cd = h // 24
        self.textVar.set(self.fmtString.format(cd, ch, cm, t % 60))


class Controls(Container):
    """Game controls

        @parent      parent container
        @app         application
    """

    def __init__(self, parent, app):
        Container.__init__(self, parent)
        self.sliders = Sliders(self)
        self.buttons = AppButtons(self)

    def layout(self):
        self.sliders.position(0, 0)
        self.buttons.position(2, 0)


FGTAG = 'fg'    # tag for all objects above background images


class Display(Container):
    """Universe display

        @parent     parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)

        self.universe = None
        uniRect = Config.uniRect
        # factors to translate universe coordinates to canvas cordinates and back
        self.u2c = Config.canvasWidth / uniRect.width()
        self.c2u = 1/self.u2c
        self.cWidth = Config.canvasWidth
        self.cHeight = uniRect.height()*self.u2c
        self.cColor = Config.colors['canvasBackground'].tkString()
        self.canvas = tk.Canvas(self.frame,
                                width=self.cWidth,
                                height=self.cHeight,
                                bg=self.cColor)
        self.heatmapFile = tempfile.TemporaryFile()
        self.vectorFile = tempfile.TemporaryFile()

        self.images = {
                'gravity': None,
                'vectors': None
        }
        self.imageLoader = self.app.threadPool
        self.loadingHeatmap = None
        self.loadingVecors = None
        self.app.components.Display = self

    def uni2canvas(self, up, cp):
        cp.x = up.x*self.u2c
        cp.y = self.cHeight - up.y*self.u2c
        return cp

    def canvas2uni(self, cp, up):
        up.x = cp.x*self.c2u
        up.y = (self.cHeight - cp.y)*self.c2u
        return up

    def reset(self, game):
        for id in self.canvas.find_all():
            self.canvas.delete(id)
        self.game = game
        self.universe = game.universe
        self.bodyViews = []
        self.movingBodyViews = []
        self.shipView = None
        self.images['gravity'] = None
        self.images['vectors'] = None
        if self.loadingHeatmap is not None:
            self.loadingHeatmap.cancel()
            self.loadingVecors = None
        if self.loadingVecors is not None:
            self.loadingVecors.cancel()
            self.loadingVecors = None

        if game.universe is not None:
            log('Display', 'Creating background images')
            self.createBackgroundImages()
            log('Display', 'Creating body views')
            self.createBodyViews()
            log('Display', 'Creating ship view')
            self.createShipView(game.ship)

    def createMatplotlibAxes(self,
                             axes=None,
                             width=Config.canvasWidth,
                             height=Config.canvasHeight):
        if axes is None:
            axes = [0., 0., 1., 1.]
        # This is a bit tricky / ugly.
        # matplotlib does not allow us to specify exact pixel values.
        # So we need to use a hack here.
        fig = mplFigure(frameon=False)
        DPI = float(fig.get_dpi())

        fCanvas = FigureCanvas(fig)
        fig.set_size_inches(width/DPI, height/DPI)

        # We don't want any axes drawn, of course.
        ax = fig.add_axes(axes)
        ax.set_axis_off()
        return (ax, fCanvas, DPI)

    def createGravityHeatmap(self, gravLogValues):
        log('Display', 'Creating gravity heatmap')

        (ax, fCanvas, DPI) = self.createMatplotlibAxes()

        # cmap sets the used (predefined) colormap
        ax.matshow(gravLogValues, cmap='inferno', interpolation='bicubic')

        # Overwrite image from previous game
        self.heatmapFile.seek(0)

        # This seems to be the only way to get an exact pixel count:
        # Save the image to a file and specify dpi to use.
        fCanvas.print_figure(self.heatmapFile, dpi=DPI)
        img = PIL.Image.open(self.heatmapFile)

        # Flip image, because canvas y-coordinates increase downwards...
        img = img.transpose(PIL.Image.FLIP_TOP_BOTTOM)

        # Ths is important:
        # 1) We need to use PIL.ImageTk.PhotoImage to make Tkinter happy
        # 2) We need to keep a reference to the image, otherwise it will
        #    disappear immediately.
        self._gravityImage = tkPhotoImage(img)

        # Tkinter's default anchor is the middle of the image
        if self.app.toggleShowGravity.get() == 1:
            gravState = tk.NORMAL
        else:
            gravState = tk.HIDDEN
        img = self.canvas.create_image(self.cWidth/2,
                                 self.cHeight/2,
                                 image=self._gravityImage,
                                 state=gravState)

        self.canvas.tag_lower(img, FGTAG)
        self.images['gravity'] = img
        log('Display', 'Creating gravity heatmap ... done')

    def createVectorImage(self, gravLogVectors, gravity):
        log('Display', 'Creating Vector field image')
        sx = Config.canvasWidth
        sy = Config.canvasHeight
        zx = sx*1.1
        zy = sy*1.1
        dx = zx - sx
        dy = zy - sy

        log('Display', 'Waiting for gravity heatmap to complete...')
        # Argument has to be a tuple.
        # You'd think Python would make this clear in the documentation
        # You'd be wrong.
        waitForFuture((gravity,)) # must wait on this to get its ID

        log('Display', 'Letting matplotlib do its thing')
        (ax, fCanvas, DPI) = self.createMatplotlibAxes(width=zx, height=zy)
        ax.quiver(self.universe.gravVectorGridX,
                  self.universe.gravVectorGridY,
                  gravLogVectors[:,:,0],
                  gravLogVectors[:,:,1],
                  angles='xy',
                  facecolor=Config.colors['canvasBackground'].tkString(),
                  antialiased=True)
        log('Display', 'Matplotlib ... done.')

        self.vectorFile.seek(0)
        fCanvas.print_figure(self.vectorFile,
                             dpi=DPI)
        img = PIL.Image.open(self.vectorFile)
        img = img.crop((dx/2, dy/2, zx - dx/2, zy - dy/2))
        meh = PIL.ImageEnhance.Sharpness(img)
        # Smooth out ugly pixelated arrows
        img = meh.enhance(0.4)

        # for some reason, this is exceedingly slow in this case.
        # self._vectorImage = tkPhotoImage(img)
        # It has to do with image transparency, which is not really
        # supported by Tkinter. But I'm not sure about the details.

        img = img.convert(mode='RGB')
        self._vectorImage = tkPhotoImage(img)

        if self.app.toggleShowVectors.get() == 1:
            vecState = tk.NORMAL
        else:
            vecState = tk.HIDDEN
        img = self.canvas.create_image(self.cWidth/2,
                                       self.cHeight/2,
                                       image=self._vectorImage,
                                       state=vecState)

        # Move the image just above the heatmap
        self.canvas.tag_raise(img, self.images['gravity'])
        self.images['vectors'] = img
        log('Display', 'Creating Vector field image ... done')

    def createBackgroundImages(self):
        # Use logarithmic scale here, otherwise we don't get a useful
        # picture.
        log('Display', 'Calculating numpy matrices')
        realGravMatrix = self.universe.gravityMatrix
        gravLogValues = np.log(realGravMatrix)
        d = gravLogValues / realGravMatrix
        gravLogVectors = self.universe.gravityVectorMatrix.copy()
        gravLogVectors[:,:,0] *= d
        gravLogVectors[:,:,1] *= d
        log('Display', 'Calculating numpy matrices ... done')

        self.loadingHeatmap = self.imageLoader.submit(self.createGravityHeatmap,
                                                      gravLogValues)
        self.loadingVecors = self.imageLoader.submit(self.createVectorImage,
                                                     gravLogVectors,
                                                     self.loadingHeatmap)

        def logError(future):
            if future.exception() is not None:
                tbe = TracebackException.from_exception(future.exception())
                log('Display', 'ERROR creating images.')
                log('Display', ''.join(tbe.format()))

        self.loadingHeatmap.add_done_callback(logError)
        self.loadingVecors.add_done_callback(logError)

    def createBodyViews(self):
        bodies = self.universe.bodies

        def createView(index, body, col, rotating):
            bv = BodyView(body, Config.colors[col], self.uni2canvas, self.u2c)
            bv.draw(self.canvas)
            self.bodyViews.append(bv)
            if rotating:
                self.movingBodyViews.append((index, bv))

        createView(0, bodies[0], 'startPlanet', True)
        createView(1, bodies[1], 'targetPlanet', True)
        for i, body in enumerate(bodies[2:]):
            if body.type == 'black':
                createView(i + 2, body, 'blackPlanet', False)
            else:
                createView(i + 2, body, 'planet', True)

    def createShipView(self, ship):
        sv = ShipView(ship,
                      Config.shipSize,
                      self.uni2canvas,
                      self.u2c)
        sv.draw(self.canvas)
        self.shipView = sv

    def layout(self):
        self.canvas.grid()

    def showImage(self, name):
        img = self.images[name]
        if img is not None:
            self.canvas.itemconfigure(img, state=tk.NORMAL)

    def hideImage(self, name):
        img = self.images[name]
        if img is not None:
            self.canvas.itemconfigure(img, state=tk.HIDDEN)

    def update(self, gt, polePoints):
        for i, bv in self.movingBodyViews:
            bv.update(self.canvas, polePoints[i])

        self.shipView.update(self.canvas, gt)


class BodyView:
    """View responsible for drawing (rotating) bodies

        @body        body for this view
        @color       a Color instance
        @uni2canvas  a function to translate universe coords to canvas coords
        @scale       scale factor  (canvas width / universe width)
    """

    def __init__(self, body, color, uni2canvas, scale):
        self.id = None # filled later
        self.rotID = None # filled later
        self.u2c = uni2canvas
        self.scale = scale
        self.circle = Circle(self.u2c(body.pos, Point(0, 0)), body.radius*scale)
        self.body = body
        self.col = color



    def drawCircle(self, canvas, r, fill, outline):
        c = self.circle
        m = c.center
        id = canvas.create_oval(m.x - r,
                                m.y - r,
                                m.x + r,
                                m.y + r,
                                fill=fill,
                                outline=outline,
                                tags=FGTAG)
        return id

    def drawBody(self, canvas):
        if self.body.type == 'black':
            outline = 'blackPlanetOutline'
        else:
            outline = 'planetOutline'
        self.id = self.drawCircle(canvas,
                                  self.circle.radius,
                                  self.col.tkString(),
                                  Config.colors[outline].tkString())

    def drawRotor(self, canvas):
         c = self.circle.center
         r = self.circle.radius
         col = Config.colors['planetRotor'].tkString()
         self.rotID = canvas.create_line(c.x,
                                         c.y,
                                         c.x,
                                         c.y - r,
                                         width=2,
                                         fill=col,
                                         tags=FGTAG)

    def draw(self, canvas):
        self.drawBody(canvas)
        if self.body.type != 'black':
            self.drawRotor(canvas)

    def update(self, canvas, polePoint):
        c = self.circle.center
        r = self.circle.radius
        canvas.coords(self.rotID,
                      c.x,
                      c.y,
                      c.x + r*polePoint[0],
                      c.y - r*polePoint[1])


class ShipView:
    """View responsible for drawing the ship

        @ship          the ship to display
        @size          size of square around ship display
        @uni2canvas    a function to translate universe coords to canvas coords
        @scale         scale factor  (canvas width / universe width)
    """

    def __init__(self, ship, size, uni2canvas, scale):
        self.id = None # filled later
        self.ship = ship
        self.u2c = uni2canvas
        self.scale = scale
        self.size = size
        self.offset = size/2
        self.bufPoint = Point(0, 0)

    def draw(self, canvas):
        p = self.u2c(self.ship.positionAt(0), self.bufPoint)
        off = self.offset
        self.id = canvas.create_oval(p.x - off,
                                     p.y - off,
                                     p.x + off,
                                     p.y + off,
                                     fill=Config.colors['ship'].tkString(),
                                     outline=Config.colors['shipOutline'].tkString(),
                                     tags=FGTAG)

    def update(self, canvas, gt):
        p = self.u2c(self.ship.positionAt(gt), self.bufPoint)
        off = self.offset
        canvas.coords(self.id,
                      p.x - off,
                      p.y - off,
                      p.x + off,
                      p.y + off)


class BottomFrame(Container):
    """Bottom area under universe display"""

    def __init__(self, parent, display):
        Container.__init__(self, parent)

        self.display = display
        self.clock = Clock(self)
        self.showGravLabel = tk.Label(self.frame, text='Show gravity')
        self.showVectorsLabel = tk.Label(self.frame, text='Show vectors')

        self.showGravButton = self.radioButton(self.app.toggleShowGravity,
                                               1,
                                               'On',
                                               self.onShowGravity)
        self.hideGravButton = self.radioButton(self.app.toggleShowGravity,
                                              0,
                                              'Off',
                                              self.onHideGravity)
        self.showVectorsButton = self.radioButton(self.app.toggleShowVectors,
                                               1,
                                               'On',
                                               self.onShowVectors)
        self.hideVectorsButton = self.radioButton(self.app.toggleShowVectors,
                                              0,
                                              'Off',
                                              self.onHideVectors)

        self.launchButton = tk.Button(self.frame,
                                      text='Launch',
                                      command=self.app.cmd_launchShip,
                                      bg=Config.colors['launchButton'].tkString())

        (self.thrustSliderLabel, self.thrustSlider) = sliderRow(
                self.frame,
                variable=self.app.s_shipThrust,
                from_=-Config.thrustScale,
                to=Config.thrustScale,
                text='Thrust',
                resolution=0.1,
                length=Config.sliderWidth*1.5)

        (self.animationSliderLabel, self.animationSlider) = sliderRow(
                self.frame,
                variable=self.app.s_animationSpeed,
                text='Animation speed',
                from_=-Config.timeScale,
                to=Config.timeScale,
                resolution=0.1,
                command=self.updateAnimationSpeed,
                length=Config.sliderWidth*1.5)

        self.usedFuelText = self.makeTextLabel('Used fuel')
        self.usedFuelLabel = self.makeValueLabel('usedFuel')

        self.launchesText = self.makeTextLabel('Launches')
        self.launchesLabel = self.makeValueLabel('nLaunches')

        self.lostText = self.makeTextLabel('Lost ships')
        self.lostLabel = self.makeValueLabel('nLostShips')

        self.flightLengthText = self.makeTextLabel('Flight length')
        self.flightLengthLabel = self.makeValueLabel('flightLength')

        self.zoomWindowWidth = Config.zoomWindowWidth
        self.zoomWindowHeight = Config.zoomWindowHeight
        self.zoomWindow = tk.Canvas(self.frame,
                                    width=self.zoomWindowWidth,
                                    height=self.zoomWindowHeight,
                                    bg=Config.colors['zoomWindowBackground'].tkString())

        self.zoomCenterX = int(self.zoomWindowWidth/2)
        self.zoomCenterY = int(self.zoomWindowHeight/2)
        self.zoomArrowLen = self.zoomWindowHeight*0.45

        r = self.zoomWindowHeight*0.35
        self.zoomPlanet = self.zoomWindow.create_oval(
                self.zoomCenterX - r,
                self.zoomCenterY - r,
                self.zoomCenterX + r,
                self.zoomCenterY + r,
                width=Config.zoomCircleLineWidth,
                outline=Config.colors['zoomOutline'].tkString())

        self.zoomArrow = self.zoomWindow.create_line(
                self.zoomCenterX,
                self.zoomCenterY,
                self.zoomCenterX,
                self.zoomCenterY - self.zoomArrowLen,
                arrow=tk.LAST,
                arrowshape=Config.zoomArrowShape,
                width=Config.zoomArrowWidth,
                fill=Config.colors['zoomArrow'].tkString())

        self.showZoom = True
        self.zoomIsHidden = False

        self.app.components.updateZoom = self.update

    def makeTextLabel(self, text):
        return tk.Label(self.frame, text=text)

    def makeValueLabel(self, variable):
        return tk.Label(self.frame, width=12,
                        textvariable=self.app.textVariables[variable],
                        bg=Config.colors['ValueLabelBackground'].tkString())

    def radioButton(self, var, value, text, cmd):
        return tk.Radiobutton(self.frame,
                              indicatoron=0,
                              value=value,
                              variable=var,
                              text=text,
                              width=4,
                              height=2,
                              command=cmd)

    def layout(self):
        self.showGravLabel.grid(row=0, column=0, rowspan=2, sticky=tk.E)
        self.showGravButton.grid(row=0, column=1, rowspan=2)
        self.hideGravButton.grid(row=0, column=2, rowspan=2)

        self.showVectorsLabel.grid(row=2, column=0, rowspan=2, sticky=tk.E)
        self.showVectorsButton.grid(row=2, column=1, rowspan=2)
        self.hideVectorsButton.grid(row=2, column=2, rowspan=2)

        self.usedFuelText.grid(row=0, column=3)
        self.usedFuelLabel.grid(row=0, column=4)
        self.launchesText.grid(row=1, column=3)
        self.launchesLabel.grid(row=1, column=4)
        self.flightLengthText.grid(row=2, column=3)
        self.flightLengthLabel.grid(row=2, column=4)
        self.lostText.grid(row=3, column=3)
        self.lostLabel.grid(row=3, column=4)

        self.animationSliderLabel.grid(row=0, column=5, rowspan=2, sticky=tk.E)
        self.animationSlider.grid(row=0, column=6, rowspan=2, sticky=tk.W)

        self.thrustSliderLabel.grid(row=2, column=5, rowspan=2, sticky=tk.E)
        self.thrustSlider.grid(row=2, column=6, rowspan=2, sticky=tk.W)

        self.clock.position(0, 8)
        self.launchButton.grid(row=2, column=8, padx=15, rowspan=2)

        self.zoomWindow.grid(row=0, column=9, rowspan=4, sticky=tk.E)

    def onShowGravity(self): self.display.showImage('gravity')

    def onHideGravity(self): self.display.hideImage('gravity')

    def onShowVectors(self): self.display.showImage('vectors')

    def onHideVectors(self): self.display.hideImage('vectors')

    def updateAnimationSpeed(self, s):
        ns = Config.scaleFunc(Config.timeFactor, float(s))
        self.app.gameTimeFactor = ns

    def update(self, gt, orbit):
        if orbit is None:
            if not self.zoomIsHidden:
                for id in self.zoomWindow.find_all():
                    self.zoomWindow.itemconfigure(id, state=tk.HIDDEN)
                self.zoomIsHidden = True
            return

        angle = orbit.yAngleAt(gt)
        angle = np.pi/2 - angle
        nx = np.cos(angle) * self.zoomArrowLen
        ny = np.sin(angle) * self.zoomArrowLen
        self.zoomWindow.coords(self.zoomArrow,
                               self.zoomCenterX,
                               self.zoomCenterY,
                               self.zoomCenterX + nx,
                               self.zoomCenterY - ny)
        if self.zoomIsHidden:
            for id in self.zoomWindow.find_all():
                self.zoomWindow.itemconfigure(id, state=tk.NORMAL)
        self.zoomIsHidden = False


class MainFrame(Container):
    """Main area containing the universe display

        @parent     parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.display = Display(self)
        self.bottomFrame = BottomFrame(self, self.display)

    def layout(self):
        self.display.position(0, 0)
        self.bottomFrame.position(1, 0)


class SideFrame(Container):
    """Side frame containing controls etc.

        @parent     parent container
    """
    def __init__(self, parent):
        Container.__init__(self, parent)
        self.controls = Controls(self, self)

    def layout(self):
        self.controls.position(1, 0)


class GameVariables:
    """Acts as an interface between app and game classes"""

    def __init__(self, app, game):
        self.app = app
        self.game = game
        self.text = app.textVariables

    @property
    def usedFuel(self): return self.game.ship.usedFuel
    @usedFuel.setter
    def usedFuel(self, v): self.text['usedFuel'].set('{:.2f}'.format(v/1000))

    @property
    def nLaunches(self): return self.game.ship.nLaunches
    @nLaunches.setter
    def nLaunches(self, v): self.text['nLaunches'].set(str(v))

    @property
    def nLostShips(self): return self.game.ship.nLost
    @nLostShips.setter
    def nLostShips(self, v): self.text['nLostShips'].set(str(v))

    @property
    def flightLength(self): return self.game.ship.flightLength()
    @flightLength.setter
    def flightLength(self, v): self.text['flightLength'].set('{:.2f}'.format(v/1000))


# Dummy class
class Components:
    pass


class App(Container):
    """Main application

        @settings       app settings object
    """

    def __init__(self, settings):
        Container.__init__(self, None)
        self.settings = settings
        self.app = self
        self.game = None
        self.gameVariables = None
        self.frame.master.title(Config.windowTitle)

        # Simple registry for widgets / containers
        self.components = Components()

        self.settingVariables = {
                's_planetSize': tk.DoubleVar(),
                's_planetDensity': tk.DoubleVar(),
                's_planetRotation': tk.DoubleVar(),
                's_gravityConstant': tk.DoubleVar(),
                'planetSpread': tk.DoubleVar(),
                'nSmallPlanets': tk.IntVar(),
                'nNormalPlanets': tk.IntVar(),
                'nLargePlanets': tk.IntVar(),
                'nBlackPlanets': tk.IntVar(),
                's_blackDensity': tk.DoubleVar()
                }

        self.textVariables = {
                'usedFuel': tk.StringVar(),
                'nLaunches': tk.StringVar(),
                'nLostShips': tk.StringVar(),
                'gameTime': tk.StringVar(),
                'flightLength': tk.StringVar()
                }

        for k, var in self.settingVariables.items():
            var.set(settings.get(k))

        # TODO make container for this so it's clearer
        # Game control variables
        self.s_shipThrust = tk.DoubleVar()
        self.s_shipThrust.set(0)
        self.s_animationSpeed = tk.DoubleVar()
        self.s_animationSpeed.set(0)

        self.toggleShowGravity = tk.IntVar()
        self.toggleShowGravity.set(0)

        self.toggleShowVectors = tk.IntVar()
        self.toggleShowVectors.set(0)


        # Needed to create images asynchronously
        self.threadPool = ThreadPoolExecutor(max_workers=5)

        # Widgets
        self.mainFrame = MainFrame(self)
        self.sideFrame = SideFrame(self)
        self.position(0, 0)
        self.animating = False

        self.updateDisplay = self.components.Display.update
        self.updateClock = self.components.Clock.update
        self.updateZoom = self.components.updateZoom
        self.realTime = time.perf_counter

        self.shouldUpdate = Config.updateInterval          # in ms
        self.atLeastUpdate = self.shouldUpdate*1.15 / 1000 # in s

        # How many game seconds pass in one real second
        self.gameTimeFactor = Config.timeFactor

        self.resetGameCounters()
        # Should be last
        self.tick()

    def resetGameCounters(self):
        currentTime = self.realTime()
        self.lastTime = currentTime             # last real time exact
        self.lastSecond = int(currentTime)      # last real time second
        self.lastGameTime = 0                   # in-game time, exact
        self.lag = 0

    def gameTime(self, t):
        gt = self.lastGameTime + (t - self.lastTime)*self.gameTimeFactor
        self.lastGameTime = gt
        return gt

    def layout(self):
        self.mainFrame.position(0, 0)
        self.sideFrame.position(0, 1)

    def resetTextVariables(self):
        self.textVariables['nLostShips'].set('0')
        self.textVariables['nLaunches'].set('0')
        self.textVariables['flightLength'].set('0')
        self.textVariables['usedFuel'].set('0')
        self.textVariables['gameTime'].set('00d 00h 00m 00s')

    def buildGame(self):
        log('App', 'Creating new game')
        for k, var in self.settingVariables.items():
            log('App', 'Setting {} to {}'.format(k, var.get()))
            self.settings.set(k, var.get())

        log('App', 'Building new game')
        game = Game(self.settings)
        self.gameVariables = GameVariables(self, game)
        game.build(self.gameVariables)
        # don't assign this until the game is fully initialized
        return game

    def startGame(self):
        self.game = None
        game = self.buildGame()
        game.start()
        self.components.Display.reset(game)
        self.runGame(game)

    def restartGame(self):
        game = self.game
        self.game = None
        game.restart()
        self.components.Display.reset(game)
        self.runGame(game)

    def runGame(self, game):
        self.resetGameCounters()
        self.resetTextVariables()
        self.animating = True
        self.game = game

    def tick(self):
        t = self.realTime()
        diff = t - self.lastTime
        if diff > self.atLeastUpdate:
            self.lag += (diff - self.atLeastUpdate)

        game = self.game
        if game is not None and self.animating:
            gt = self.gameTime(t)
            ts = int(t)
            if ts != self.lastSecond:
                self.updateSec(gt, diff)
                self.lastSecond = ts

            poleVecs = game.update(gt)
            self.updateDisplay(gt, poleVecs)
            orbit = game.ship.orbit()
            if orbit is not None:
                self.updateZoom(gt, orbit)

        self.lastTime = t
        self.frame.after(self.shouldUpdate, self.tick)

    def updateSec(self, gt, diff):
        """Update running game
            @gt      game time
            @diff    exact time since last call
        """
        dl = self.lag/diff
        if dl > 0.1:
            log('App', 'Relative lag: {}'.format(dl))
        self.updateClock(gt)
        self.lag = 0

    def cmd_launchShip(self):
        orbit = self.game.ship.orbit()
        # Check if the ship is landed on a planet
        if orbit is None:
            return
        planet = orbit.body
        t = self.realTime()
        gt = self.gameTime(t)
        ev = planet.escapeSpeed(self.game.universe.gravity)
        self.game.launchShip(gt, Config.scaleFunc(ev, self.s_shipThrust.get()))

    def logState(self, t):
        self.game.logState(t)

    def run(self):
        self.frame.mainloop()

    def quit(self):
        self.frame.quit()











