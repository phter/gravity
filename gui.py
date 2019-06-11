"""Graphical user interface"""

import time
import tkinter as tk
from util import log
from config import Config
from game import Game
from geometry import Point, Circle, Rect



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
    desc['length'] = Config.sliderWidth
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
            label.grid(row=i, column=0)
            slider.grid(row=i, column=1)


class ControlArea(Container):
    """Area for widgets controling the ship

        @parent      parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.frame.configure(borderwidth=2, pady=10)
        self.launchButton = tk.Button(self.frame,
                                      text='Launch',
                                      command=self.app.cmd_launchShip,
                                      bg=Config.colors['launchButton'].tkString())
        self.thrustSliderRow = sliderRow(
                self.frame,
                variable=self.app.s_shipThrust,
                from_=-Config.thrustScale,
                to=Config.thrustScale,
                text='Thrust',
                resolution=0.1)
        self.animationSliderRow = sliderRow(
                self.frame,
                variable=self.app.s_animationSpeed,
                text='Animation speed',
                from_=-Config.timeScale,
                to=Config.timeScale,
                resolution=0.1,
                command=self.updateAnimationSpeed)

    def updateAnimationSpeed(self, s):
        ns = Config.scaleFunc(Config.timeFactor, float(s))
        self.app.gameTimeFactor = ns
        # log('Control', 'Changed animation speed to ' + str(ns))

    def layout(self):
        label, slider = self.animationSliderRow
        label.grid(row=0, column=0)
        slider.grid(row=0, column=1)
        label, slider = self.thrustSliderRow
        label.grid(row=1, column=0)
        slider.grid(row=1, column=1)
        self.launchButton.grid(row=2, column=0, columnspan=2)


class Buttons(Container):
    """Buttons area

        @parent     parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.quitButton = tk.Button(self.frame, text='Quit', command=self.app.quit)
        self.playButton = tk.Button(self.frame, text='New Game', command=self.app.startGame)

    def layout(self):
        self.playButton.grid(row=1,column=0)
        self.quitButton.grid(row=1,column=1)


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
        self.launcher = ControlArea(self)
        self.buttons = Buttons(self)

    def layout(self):
        self.sliders.position(0, 0)
        self.launcher.position(1, 0)
        self.buttons.position(2, 0)


class Display(Container):
    """Universe display

        @parent     parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)

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
        self.bodyViews = []
        self.shipView = None

    def uni2canvas(self, up, cp):
        cp.x = up.x*self.u2c
        cp.y = self.cHeight - up.y*self.u2c
        return cp

    def canvas2uni(self, cp, up):
        up.x = cp.x*self.c2u
        up.y = (self.cHeight - cp.y)*self.c2u
        return up

    def reset(self, bodies):
        for id in self.canvas.find_all():
            self.canvas.delete(id)

        self.bodyViews = []
        self.shipView = None
        self.createViews()

    def createViews(self):
        self.createBodyViews()
        self.createShipView()

    def createBodyViews(self):
        bodies = self.app.game.universe.bodies

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

    def update(self, gt):
        self.shipView.update(self.canvas, gt)
        for bv in self.bodyViews:
            bv.update(self.canvas, gt)


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
        rp = c.pointAtAngle(0)
        self.rotID = canvas.create_line(c.center.x,
                                        c.center.y,
                                        rp.x,
                                        rp.y,
                                        width=2,
                                        fill=Config.colors['planetRotor'].tkString())

    def update(self, canvas, gt):
        a = self.body.bodyAngleAt(gt)
        c = self.circle
        p = c.pointAtAngle(a)
        p.y = 2*c.center.y - p.y  # because we use screen coordinates
        canvas.coords(self.rotID,
                      c.center.x,
                      c.center.y,
                      p.x,
                      p.y)


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

    def getRect(self, gt):
        p = self.u2c(self.ship.positionAt(gt), self.bufPoint)
        return Rect(p.x - self.offset,
                    p.y - self.offset,
                    p.x + self.offset,
                    p.y + self.offset)

    def draw(self, canvas):
        r = self.getRect(0)
        self.id = canvas.create_oval(r.xmin,
                                     r.ymin,
                                     r.xmax,
                                     r.ymax,
                                     fill=Config.colors['ship'].tkString(),
                                     outline=Config.colors['shipOutline'].tkString())

    def update(self, canvas, gt):
        r = self.getRect(gt)
        canvas.coords(self.id,
                      r.xmin,
                      r.ymin,
                      r.xmax,
                      r.ymax)


class MainFrame(Container):
    """Main area containing the universe display

        @parent     parent container
    """

    def __init__(self, parent):
        Container.__init__(self, parent)
        self.display = Display(self)

    def layout(self):
        self.display.position(0, 0)


class SideFrame(Container):
    """Side frame containing controls etc.

        @parent     parent container
    """
    def __init__(self, parent):
        Container.__init__(self, parent)
        self.clock = Clock(self)
        self.controls = Controls(self, self)

    def layout(self):
        self.clock.position(0, 0)
        self.controls.position(1, 0)


class App(Container):
    """Main application

        @settings       app settings object
    """

    def __init__(self, settings):
        Container.__init__(self, None)
        self.settings = settings
        self.app = self
        self.game = None
        self.frame.master.title(Config.windowTitle)
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

        for k, var in self.settingVariables.items():
            var.set(settings.get(k))

        # Game control variables
        self.s_shipThrust = tk.DoubleVar()
        self.s_shipThrust.set(0)
        self.s_animationSpeed = tk.DoubleVar()
        self.s_animationSpeed.set(0)

        # Widgets
        self.mainFrame = MainFrame(self)
        self.sideFrame = SideFrame(self)
        self.position(0, 0)
        self.animating = False

        self.updateDisplay = self.mainFrame.display.update
        self.updateClock = self.sideFrame.clock.update

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
        self.game = Game(self.settings)
        self.game.build()
        self.mainFrame.display.reset(self.game.universe.bodies)
        self.lastGameTime = 0
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
            self.updateDisplay(gt)

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
        planet = self.game.ship.planet
        # Check if the ship is landed on a planet
        if planet is None:
            return
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











