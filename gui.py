import tkinter as tk
from util import log
import math
import time
from config import guiConfig, gameConfig
from game import Game
from geometry import Point, Circle



# Helper class to simplify layout generation:
# Tkinter doesn't like it, if a parent's .grid() method is called
# before .grid() has been called on all children. This class takes care of that
# .layout() should create the layout of all widgets inside.
# .position(row, column) will call grid and make sure layout() gets called
# first, if it hasn't already been called.
#
# Generally speaking, there is no reason to call .layout() manually.
# Just call .position() as you would call .grid() on a widget.
class Container:
    """Container for widgets / other containers
    
        @parent     parent container
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
        


class Sliders(Container):
    def __init__(self, parent):
        Container.__init__(self, parent)
        self.sliders = []
        
        var = self.app.controlVariables
        sliders = [
                {'var': var['planetSize'], 
                 'text': 'Planet size',
                 'min': 15.0,
                 'max': 70.0,
                 'resolution': 0.1
                 },
                 {'var': var['planetDensity'], 
                 'text': 'Planet density',
                 'min': 0.1,
                 'max': 10.0,
                 'resolution': 0.1
                 },
                 {'var': var['planetRotation'], 
                 'text': 'Rotation speed',
                 'min': 1.0,
                 'max': 10.0,
                 'resolution': 0.1
                 }, 
                 {'var': var['minPlanetDistance'], 
                 'text': 'Planet distance',
                 'min': 1.0,
                 'max': 10.0,
                 'resolution': 0.1
                 }]
        
        for desc in sliders:
            slider = tk.Scale(self.frame, 
                              variable=desc['var'],
                              from_=desc['min'], 
                              to=desc['max'], 
                              label=desc['text'],
                              resolution=desc['resolution'],
                              orient=tk.HORIZONTAL)
            self.sliders.append(slider)
            
    def layout(self):
        for slider in self.sliders:
            slider.grid()
        
        
class Buttons(Container):
    def __init__(self, parent):
        Container.__init__(self, parent)
        self.quitButton = tk.Button(self.frame, text='Quit', command=self.app.quit)
        self.playButton = tk.Button(self.frame, text='New Game', command=self.app.startGame)
        self.launchButton = tk.Button(self.frame, text='Launch', command=self.app.launchShip)
        
    def layout(self):
        self.playButton.grid(row=0,column=0)
        self.quitButton.grid(row=0,column=1)


class Controls(Container):
    def __init__(self, parent, app):
        Container.__init__(self, parent)
        self.sliders = Sliders(self)
        self.buttons = Buttons(self)
        
    def layout(self):
        self.sliders.position(0, 0)
        # self.spacer = tk.Frame(self, height=50)
        # Necessary to make Tkinter respect the height given above
        # self.spacer.grid_propagate(0)
        
        self.buttons.position(1, 0)

        
        
class Clock(Container):
    def __init__(self, parent):
        Container.__init__(self, parent)
        
    def layout(self):
        pass
    
    def update(self, t):
        pass

        
class Display(Container):
    def __init__(self, parent):
        Container.__init__(self, parent)
        config = self.app.config
        
        uniRect = gameConfig.uniRect 
        # factor to translate universe coordinates to canvas cordinates
        self.u2c = config.canvasWidth / uniRect.width() 
        self.cWidth = config.canvasWidth
        self.cHeight = uniRect.height()*self.u2c
        self.cColor = config.canvasColor
        
        self.canvas = tk.Canvas(self.frame, width=self.cWidth, height=self.cHeight, bg=self.cColor)
        self.bodyViews = []

    def reset(self, bodies):
        for ob in self.canvas.find_all():
            self.canvas.delete(ob)
            
        self.createBodyViews(bodies)
        
    def createBodyViews(self, bodies):
        self.bodyViews = []
        config = self.app.config
        outlineCol = config.bodyColors['outline'].format(val='80')
        
        def createView(body, col):
            bv = BodyView(body, self.u2c, config.bodyColors[col])
            bv.id = self.canvas.create_oval(bv.x, bv.y, 
                                            bv.x + bv.d, bv.y + bv.d, 
                                            fill=bv.col, 
                                            outline=outlineCol)
            bv.rotID = self.canvas.create_line(bv.center.x, 
                                               bv.center.y,
                                               bv.center.x-bv.r,
                                               bv.center.y-bv.r, width=2)
            self.bodyViews.append(bv)
        
        createView(bodies[0], 'start')
        createView(bodies[1], 'target')
        for body in bodies[2:]:
            createView(body, 'planet')
            
    def layout(self):
        self.canvas.grid()
        
    def update(self, t):
        for bv in self.bodyViews:
            angle = bv.body.angle(t)
            pos = bv.circle.pointAt(angle)
            self.canvas.coords(bv.rotID, 
                               bv.center.x, 
                               bv.center.y,
                               pos.x,
                               pos.y)
            


class BodyView:
    def __init__(self, body, scale, colStr):
        self.id = None # filled later
        self.rotID = None # filled later
        self.body = body
        self.circle = Circle(Point(body.pos.x*scale, body.pos.y*scale),
                             body.radius*scale)
        self.scale = scale
        self.col = colStr.format(val=hex(math.floor(body.rotation*255))[2:4])
        self.center = Point(body.pos.x*scale, body.pos.y*scale)
        self.x = (body.pos.x - body.radius)*scale
        self.y = (body.pos.y - body.radius)*scale
        self.r = body.radius*scale
        self.d = self.r*2


class MainFrame(Container):
    def __init__(self, parent):
        Container.__init__(self, parent)
        self.display = Display(self)
        
    def layout(self):
        self.display.position(0, 0)
        
  
class SideFrame(Container):
    def __init__(self, parent):
        Container.__init__(self, parent)
        self.clock = Clock(self)
        self.controls = Controls(self, self)
        
    def layout(self):
        self.clock.position(0, 0)
        self.controls.position(1, 0)


class App(Container):
    def __init__(self):
        Container.__init__(self, None)
        self.config = guiConfig
        self.app = self
        self.game = None
        self.frame.master.title(self.config.windowTitle)
        self.controlVariables = {
                'planetSize': tk.DoubleVar(),
                'planetDensity': tk.DoubleVar(),
                'planetRotation': tk.DoubleVar(),
                'minPlanetDistance': tk.DoubleVar()
                }
    
        self.mainFrame = MainFrame(self)
        self.sideFrame = SideFrame(self)
        self.position(0, 0)
        self.animating = False
        
    def layout(self):
        self.mainFrame.position(0, 0)
        self.sideFrame.position(0, 1)

    def startGame(self):
        log('App', 'Creating new game')
        for k, var in self.controlVariables.items():
            log('App', 'Setting {} to {}'.format(k, var.get()))
            gameConfig.update(k, var.get())
        self.game = Game(gameConfig)
        self.game.build()
        self.mainFrame.display.reset(self.game.universe.bodies)
        self.game.start()
        
        
        self.updateDisplay = self.mainFrame.display.update
        self.updateClock = self.sideFrame.clock.update
        
        self.startAnimation()
        self.startClock()
        
    def updateFast(self):
        if self.animating:
            t = self.game.gameTime()
            self.updateDisplay(t)
            self.frame.after(75, self.updateFast)
    
    def updateSlow(self):
        t = self.game.gameTime()
        self.updateClock(t)
        self.frame.after(1000, self.updateSlow)
        
    def startAnimation(self):
        self.animating = True
        self.updateFast()
    
    def stopAnimation(self):
        self.animating = False
        
    def startClock(self):
        self.updateSlow()
        
    def launchShip(self):
        pass
    
    def run(self):
        self.frame.mainloop()
        
    def quit(self):
        self.frame.quit()
        


 
            
        
    
        
        


