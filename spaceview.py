"""spaceview.py - a widget that displays our universe"""

import tempfile
try:
    from traceback import TracebackException
except: pass
import tkinter as tk
import numpy as np

from tkutil import Container
from visual import createHeatmap, createVectorPlot
from geometry import Point, Circle
from config import Config
from util import log


FGTAG = 'fg'    # tag for all objects above background images


class SpaceView(Container):
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

        self.images = {
                'gravity': None,
                'vectors': None
        }
        self.imageLoader = self.app.threadPool
        self.loadingHeatmap = None
        self.loadingVecors = None
        self.app.components.SpaceView = self

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
            log('SpaceView', 'Creating background images')
            self.createBackgroundImages()
            log('SpaceView', 'Creating body views')
            self.createBodyViews()
            log('SpaceView', 'Creating ship view')
            self.createShipView(game.ship)

    def createGravityHeatmap(self, gravLogValues):
        log('SpaceView', 'Creating gravity heatmap')
        self._gravityImage = createHeatmap(self.cWidth, self.cHeight, gravLogValues)

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
        log('SpaceView', 'Creating gravity heatmap ... done')

    def createVectorImage(self, gravLogVectors, gravity):
        log('SpaceView', 'Creating Vector field image')
        self._vectorImage = createVectorPlot(self.cWidth,
                                             self.cHeight,
                                             self.universe.gravVectorGridX,
                                             self.universe.gravVectorGridY,
                                             gravLogVectors,
                                             'r')

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
        log('SpaceView', 'Creating Vector field image ... done')

    def createBackgroundImages(self):
        # Use logarithmic scale here, otherwise we don't get a useful
        # picture.
        log('SpaceView', 'Calculating numpy matrices')
        realGravMatrix = self.universe.gravityMatrix
        gravLogValues = np.log(realGravMatrix)
        d = gravLogValues / realGravMatrix
        gravLogVectors = self.universe.gravityVectorMatrix.copy()
        gravLogVectors[:,:,0] *= d
        gravLogVectors[:,:,1] *= d
        log('SpaceView', 'Calculating numpy matrices ... done')

        self.loadingHeatmap = self.imageLoader.submit(self.createGravityHeatmap,
                                                      gravLogValues)
        self.loadingVecors = self.imageLoader.submit(self.createVectorImage,
                                                     gravLogVectors,
                                                     self.loadingHeatmap)

        def logError(future):
            if future.exception() is not None:
                log('SpaceView', 'ERROR creating images.')
                try:
                    tbe = TracebackException.from_exception(future.exception())
                    log('SpaceView', ''.join(tbe.format()))
                except: pass

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
