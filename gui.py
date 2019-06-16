"""Graphical user interface"""

import time
import tkinter as tk
import numpy as np
import matplotlib as mpl
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import PIL
from PIL.ImageTk import PhotoImage as tkPhotoImage
import tempfile
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
        else:
            app = parent.app
            parentFrame = parent.frame

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
                 }]

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

    def layout(self):
        self.playButton.grid(row=1, column=0, pady=30)
        self.quitButton.grid(row=1, column=1, pady=30, padx=20)


class Clock(Container):
    """Clock display

        @parent       parent container
    """

    fmtString = '{:02}d {:02}h {:02}m {:02}s'

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.label = tk.Label(self.frame,
                              width=18,
                              text=self.fmtString.format(0, 0, 0, 0),
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
        self.label.config(text=self.fmtString.format(cd, ch, cm, t % 60))


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


class Display(Container):
    """Universe display

        @parent     parent container
    """

    def __init__(self, parent, universe):
        Container.__init__(self, parent)

        self.universe = universe
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

        self.reset(universe)
        self.app.components.display = self

    def uni2canvas(self, up, cp):
        cp.x = up.x*self.u2c
        cp.y = self.cHeight - up.y*self.u2c
        return cp

    def canvas2uni(self, cp, up):
        up.x = cp.x*self.c2u
        up.y = (self.cHeight - cp.y)*self.c2u
        return up

    def reset(self, universe):
        for id in self.canvas.find_all():
            self.canvas.delete(id)
        self.universe = universe
        self.bodyViews = []
        self.shipView = None

        if universe is not None:
            log('Display', 'Creating background images')
            self.createBackgroundImages()
            log('Display', 'Creating body views')
            self.createBodyViews()
            log('Display', 'Creating ship view')
            self.createShipView()

    def createMatplotlibAxes(self,
                             axes=None,
                             width=Config.canvasWidth,
                             height=Config.canvasHeight):
        if axes is None:
            axes = [0., 0., 1., 1.]
        # This is a bit tricky / ugly.
        # matplotlib does not allow us to specify exact pixel values.
        # So we need to use a hack here.
        fig = mpl.figure.Figure(frameon=False)
        DPI = float(fig.get_dpi())

        fCanvas = FigureCanvas(fig)
        fig.set_size_inches(width/DPI, height/DPI)

        # We don't want any axes drawn, of course.
        ax = fig.add_axes(axes)
        ax.set_axis_off()
        return (ax, fCanvas, DPI)

    def createBackgroundImages(self):
        log('Display', 'Creating gravity heatmap')
        # Use logarithmic scale here, otherwise we don't get a useful
        # picture.
        realGravMatrix = self.universe.gravityMatrix
        gravLogValues = np.log(realGravMatrix)
        d = gravLogValues / realGravMatrix
        gravLogVectors = self.universe.gravityVectorMatrix.copy()
        gravLogVectors[:,:,0] *= d
        gravLogVectors[:,:,1] *= d

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
        self.gravityImage = self.canvas.create_image(self.cWidth/2,
                                                self.cHeight/2,
                                                image=self._gravityImage,
                                                state=gravState)
        # Now the vector field
        log('Display', 'Creating Vector field image')
        sx = Config.canvasWidth
        sy = Config.canvasHeight
        zx = sx*1.1
        zy = sy*1.1
        dx = zx - sx
        dy = zy - sy
        (ax, fCanvas, DPI) = self.createMatplotlibAxes(width=zx, height=zy)
        ax.quiver(self.universe.gravVectorGridX,
                  self.universe.gravVectorGridY,
                  gravLogVectors[:,:,0],
                  gravLogVectors[:,:,1],
                  angles='xy',
                  color='r')
        self.vectorFile.seek(0)
        fCanvas.print_figure(self.vectorFile, dpi=DPI)
        img = PIL.Image.open(self.vectorFile)
        img = img.crop((dx/2, dy/2, zx - dx/2, zy - dy/2))
        self._vectorImage = tkPhotoImage(img)
        if self.app.toggleShowVectors.get() == 1:
            vecState = tk.NORMAL
        else:
            vecState = tk.HIDDEN
        self.vectorImage = self.canvas.create_image(self.cWidth/2,
                                                    self.cHeight/2,
                                                    image=self._vectorImage,
                                                    state=vecState)

    def createBodyViews(self):
        bodies = self.universe.bodies

        def createView(body, col):
            bv = BodyView(body, Config.colors[col], self.uni2canvas, self.u2c)
            bv.draw(self.canvas)
            self.bodyViews.append(bv)

        createView(bodies[0], 'startPlanet')
        createView(bodies[1], 'targetPlanet')
        for body in bodies[2:]:
            createView(body, 'planet')

    def createShipView(self):
        sv = ShipView(self.app.game.ship,
                      Config.shipSize,
                      self.uni2canvas,
                      self.u2c)
        sv.draw(self.canvas)
        self.shipView = sv

    def layout(self):
        self.canvas.grid()

    def update(self, gt, polePoints):
        for i, bv in enumerate(self.bodyViews):
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

    def draw(self, canvas):
        c = self.circle
        self.id = canvas.create_oval(c.center.x - c.radius,
                                     c.center.y - c.radius,
                                     c.center.x + c.radius,
                                     c.center.y + c.radius,
                                     fill=self.col.tkString(),
                                     outline=Config.colors['planetOutline'].tkString())
        c = self.circle.center
        r = self.circle.radius
        self.rotID = canvas.create_line(c.x,
                                        c.y,
                                        c.x,
                                        c.y - r,
                                        width=2,
                                        fill=Config.colors['planetRotor'].tkString())

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
                                     outline=Config.colors['shipOutline'].tkString())

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

    def __init__(self, parent):
        Container.__init__(self, parent)

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
                fill=Config.colors['zoomOutline'].tkString())

        self.showZoom = True
        self.zoomIsHidden = False
        self.app.components.BottomFrame = self

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

    def display(self): return self.app.components.display

    def onShowGravity(self):
        display = self.display()
        display.canvas.itemconfigure(display.gravityImage, state=tk.NORMAL)

    def onHideGravity(self):
        display = self.display()
        display.canvas.itemconfigure(display.gravityImage, state=tk.HIDDEN)

    def onShowVectors(self):
        display = self.display()
        display.canvas.itemconfigure(display.vectorImage, state=tk.NORMAL)

    def onHideVectors(self):
        display = self.display()
        display.canvas.itemconfigure(display.vectorImage, state=tk.HIDDEN)

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
        self.display = Display(self, None)
        self.bottomFrame = BottomFrame(self)

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
                'nLargePlanets': tk.IntVar()
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

        # Game control variables
        self.s_shipThrust = tk.DoubleVar()
        self.s_shipThrust.set(0)
        self.s_animationSpeed = tk.DoubleVar()
        self.s_animationSpeed.set(0)

        self.toggleShowGravity = tk.IntVar()
        self.toggleShowGravity.set(0)

        self.toggleShowVectors = tk.IntVar()
        self.toggleShowVectors.set(0)

        # Widgets
        self.mainFrame = MainFrame(self)
        self.sideFrame = SideFrame(self)
        self.position(0, 0)
        self.animating = False

        self.updateDisplay = self.mainFrame.display.update
        self.updateClock = self.components.Clock.update
        self.updateZoom = self.components.BottomFrame.update

        self.shouldUpdate = Config.updateIntervalFast      # in ms
        self.shouldUpdateSlow = Config.updateIntervalSlow  # in ms
        self.atLeastUpdate = self.shouldUpdate*1.15 / 1000 # in s

        currentTime = self.realTime()
        self.lastUpdate = currentTime
        self.lastGameTime = 0
        self.gameTimeFactor = Config.timeFactor

        self.nUpdateLags = 0
        self.nUpdates = 0

        self.lastUpdateSlow = currentTime

        self.totalLag = 0
        self.lastTotalLag = 0

        # Should be last
        self.updateFast()
        self.updateSlow()

    def realTime(self):
        return time.perf_counter()

    def gameTime(self, t):
        gt = self.lastGameTime + (t - self.lastUpdate)*self.gameTimeFactor
        self.lastGameTime = gt
        return gt

    def layout(self):
        self.mainFrame.position(0, 0)
        self.sideFrame.position(0, 1)

    def startGame(self):
        log('App', 'Creating new game')
        for k, var in self.settingVariables.items():
            log('App', 'Setting {} to {}'.format(k, var.get()))
            self.settings.set(k, var.get())

        log('App', 'Building new game')
        self.game = Game(self.settings)
        self.gameVariables = GameVariables(self, self.game)
        self.game.build(self.gameVariables)

        log('App', 'Creating views')
        self.mainFrame.display.reset(self.game.universe)
        self.lastGameTime = 0
        self.textVariables['nLostShips'].set('0')
        self.textVariables['nLaunches'].set('0')
        self.textVariables['flightLength'].set('0')
        self.textVariables['usedFuel'].set('0')
        self.textVariables['gameTime'].set('00d 00h 00m 00s')

        self.game.start()
        self.animating = True

    def updateFast(self):
        t = self.realTime()
        diff = t - self.lastUpdate
        if diff > self.atLeastUpdate:
            self.totalLag += diff
            self.nUpdateLags += 1

        if self.game is not None and self.animating:
            gt = self.gameTime(t)
            self.game.update(gt)
            polePoints = self.game.polePointsAt(gt)
            self.updateDisplay(gt, polePoints)
            self.components.BottomFrame.update(gt, self.game.ship.orbit())

        self.lastUpdate = t
        self.nUpdates +=1
        self.frame.after(self.shouldUpdate, self.updateFast)

    def updateSlow(self):
        t = self.realTime()

        if self.game is not None:
            diff = t - self.lastUpdateSlow
            lag = (self.totalLag - self.lastTotalLag)/diff
            if lag > 0.1:
                log('App', 'Avg lag/s: {}'.format(lag))

            gt = self.gameTime(t)
            self.updateClock(gt)

        self.lastTotalLag = self.totalLag
        self.lastUpdateSlow = t
        self.frame.after(self.shouldUpdateSlow, self.updateSlow)

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











