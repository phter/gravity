"""Graphical user interface"""

from concurrent.futures import ThreadPoolExecutor
import time
import tkinter as tk
from tkinter import filedialog
import numpy as np
import json

from .util import log
from .config import Config
from .game import Game
from .spaceview import SpaceView
from .tkutil import Container


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
                  'text': 'Num. small planets',
                  'from_': s.nSmallPlanetsRange.start,
                  'to': s.nSmallPlanetsRange.end,
                  'resolution': 1
                 },
                 {'variable': var['nNormalPlanets'],
                  'text': 'Num. normal planets',
                  'from_': s.nNormalPlanetsRange.start,
                  'to': s.nNormalPlanetsRange.end,
                  'resolution': 1
                 },
                 {'variable': var['nLargePlanets'],
                  'text': 'Num. large planets',
                  'from_': s.nLargePlanetsRange.start,
                  'to': s.nLargePlanetsRange.end,
                  'resolution': 1
                 },
                 {'variable': var['nBlackPlanets'],
                  'text': 'Num. black holes',
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
            label.grid(row=i, column=0, pady=20, sticky=tk.E)
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
        self.saveButton = tk.Button(self.frame, text='Save', command=self.app.saveGame)
        self.loadButton = tk.Button(self.frame, text='Load', command=self.app.loadGame)
        self.resetButton = tk.Button(self.frame, text='Reset', command=self.app.resetSettings)

    def layout(self):
        self.restartButton.grid(row=0, column=0, pady=30, sticky=tk.W+tk.E)
        self.playButton.grid(row=0, column=1, padx=5, sticky=tk.W+tk.E)
        self.resetButton.grid(row=0, column=2, padx=5, sticky=tk.W+tk.E)

        self.saveButton.grid(row=1, column=0, padx=5, sticky=tk.W+tk.E)
        self.loadButton.grid(row=1, column=1, padx=5, sticky=tk.W+tk.E)
        self.quitButton.grid(row=1, column=2, padx=10, sticky=tk.W+tk.E)



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
        self.hideGravButton.grid(row=0, column=2, rowspan=2, padx=5)

        self.showVectorsLabel.grid(row=2, column=0, rowspan=2, sticky=tk.E)
        self.showVectorsButton.grid(row=2, column=1, rowspan=2)
        self.hideVectorsButton.grid(row=2, column=2, rowspan=2, padx=5)

        self.usedFuelText.grid(row=0, column=3)
        self.usedFuelLabel.grid(row=0, column=4, padx=5)
        self.launchesText.grid(row=1, column=3)
        self.launchesLabel.grid(row=1, column=4, padx=5)
        self.flightLengthText.grid(row=2, column=3)
        self.flightLengthLabel.grid(row=2, column=4, padx=5)
        self.lostText.grid(row=3, column=3)
        self.lostLabel.grid(row=3, column=4, padx=5)

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
        self.display = SpaceView(self)
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

        self.updateSpaceView = self.components.SpaceView.update
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
        self.components.SpaceView.reset(game)
        self.runGame(game)

    def restartGame(self):
        game = self.game
        self.game = None
        game.restart()
        self.components.SpaceView.reset(game)
        self.runGame(game)

    def runGame(self, game):
        self.resetGameCounters()
        self.resetTextVariables()
        self.animating = True
        self.game = game

    def loadGame(self):
        path = filedialog.askopenfilename()
        if len(path) == 0:
            return

        d = None
        try:
            with open(path) as f:
                d = json.load(f)
        except: pass

        if d is not None:
            for k, v in d.items():
                self.settingVariables[k].set(v)

    def saveGame(self):
        path = filedialog.asksaveasfilename()
        if len(path) == 0:
            return

        d = {k: v.get() for k, v in self.settingVariables.items()}
        try:
            with open(path, 'w') as f:
                json.dump(d, f)
        except: pass

    def resetSettings(self):
        for k, var in self.settingVariables.items():
            var.set(self.settings.get(k))

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
            self.updateSpaceView(gt, poleVecs)
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
