import math
from config import gameConfig # TODO: this should go away
from geometry import Point, Vector, Rect, distancePP
from physics import Body, Universe
from util import randomFloat, randomPointRect, log
import time

class Planet(Body):
    """ Planet - a body where space ships can land.
    
    @radius       radius of planet
    @aVelocity    angular velocity
    @colStr       a template string for a Tkinter color, leaving one 
                  RGB-component to be filled dynamically.
    """
    
    def __init__(self, type, pos):
        if type == 'normal':
            radius = gameConfig.planetSizeNormal()
            density = gameConfig.planetDensityNormal()
        elif type == 'small':
            radius = gameConfig.planetSizeSmall()
            density = gameConfig.planetDensitySmall()
        elif type == 'large':
            radius = gameConfig.planetSizeLarge()
            density = gameConfig.planetDensityLarge()
        else:
            raise ValueError('Illegal planet type')
            
        Body.__init__(self, 
                      type,
                      pos=pos.copy(), 
                      radius=radius, 
                      rotation=gameConfig.rotationRange.random(), 
                      density=density)
        self.ship = None
        
    
class Ship:
    """Our space ship"""
    def __init__(self, body, angle):
        self.body = body
        self.angle = angle
        self.usedFuel = 0
        self.vec = Vector(0,0) # current motion vector
        self.nLaunches = 0   # how many landings on a planet
        self.nLost = 0       # how often flown outside of universe rectangle


    def speed(self):
        return math.sqrt(self.vec[0]**2 + self.vec[1]**2)
    
    def land(self, body, angle):
        self.body = body
        self.angle = angle
        
    def launch(self, vec):
        self.vec.x = vec.x
        self.vec.y = vec.y
        speed = vec.norm()
        self.usedFuel += speed
        self.nLaunches += 1
        
        
        

class Game:
    """Main class for the game"""

    def __init__(self, config):
        self.cfg = config

    def build(self):
        log('Game', 'Building new game')
        cfg = self.cfg
        pg = PlanetGenerator(cfg)
        pg.run()
        self.universe = Universe(pg.planets)
        self.startPlanet = pg.startPlanet
        self.targetPlanet = pg.targetPlanet
        self.ship = Ship(self.startPlanet, 0)
        self.nLaunches = 0
        self.startTime = 0
        
    def start(self):
        """Start a new game
            @t       start time
        """
        log('Game', 'Starting new game')
        # List of trajectories of the ship
        self.trajectories = []
        self.startTime = time.perf_counter()

    def gameTime(self):
        t = time.perf_counter()
        return (t - self.startTime)
    
    def launchShip(self, thrust):
        self.usedThrust += thrust
        pass





class PlanetGenerator:
    """Helper class to create planets
    
    There are quite a few things to consider here:
      *) the starting planet must be the leftmost planet
      *) the target planet must be the rightmost planet
      *) two planets must not be too close together
      *) planets should be (somewhat) evenly distributed (no clusters)
      *) planets should not sit right at the edge of the frame
    
         +-----+-------------------------------------+-----+
         |     |                                     |     |
         |     |                                     |     |
         |     |            planet area              |     |
         |     |                                     |     |
         |     |                                     |     |
         |     |                                     |     |
         |     |                                     |     |
         |     |                                     |     |
         |   <-----start area          target area----->   |
         |     |                                     |     |
         |     |                                     |     |
         |     |                                     |     |
         +-----+-------------------------------------+-----+
    """
    
    def __init__(self, config):
        self.cfg = config
        self.uniRect = config.uniRect
        self.wStartArea = config.startAreaWidth
        self.wTargetArea = config.targetAreaWidth
        self.relDistance = config.minPlanetDistance
        rect = self.uniRect
        self.planetRect = Rect(rect.xmin + self.wStartArea,
                               rect.ymin,
                               rect.xmax - self.wTargetArea,
                               rect.ymax)
        self.planets = None
        self.startPlanet = None
        self.targetPlanet = None
        
    def run(self):
        log('PlanetGenerator', 'Creating planets')
        self.createStartAndTarget()
        
        cfg = self.cfg
        for tries in range(5):
            self.planets = [self.startPlanet, self.targetPlanet]
            
            if not self.addPlanets('large', cfg.planetSize*1.5, cfg.nLargeP):
                continue
            if not self.addPlanets('normal', cfg.planetSize, cfg.nNormalP):
                continue
            if self.addPlanets('small', cfg.planetSize*0.66, cfg.nSmallP):
                return
        raise Exception("Failed to create planets")
        
    
    def createStartAndTarget(self):
        ur = self.uniRect
        # make sure the start planet is not right at the top or bottom 
        pos = Point(self.uniRect.xmin + self.wStartArea/2,
                    randomFloat(ur.ymin + ur.height()*0.2, 
                                ur.ymax - ur.height()*0.2))
        self.startPlanet = Planet('normal', pos)
    
        # make sure the start planet is not right at the top or bottom 
        pos = Point(ur.xmax - self.wTargetArea/2,
                    randomFloat(ur.ymin + ur.height()*0.2, 
                                ur.ymax - ur.height()*0.2))
        self.targetPlanet = Planet('normal', pos)
        
    # Helper function to find a random position for a planet
    def findPosition(self, rect, pRadius):
        for i in range(1000):
            pos = randomPointRect(rect)
            success = True
            for p in self.planets:
                if distancePP(pos, p.pos) < (pRadius + p.radius)*self.relDistance:
                    success = False
                    break
            if success:
                log('findPosition', '{} tries to find empty space'.format(i + 1))
                return pos
        return None # failed to find a position
    
    # Helper function to add planets of a given type
    def addPlanets(self, type, radius, num):
        pr = self.planetRect
        dr = radius*self.relDistance
        rect = Rect(pr.xmin + dr, pr.ymin + dr,
                    pr.xmax - dr, pr.ymax - dr)
        for n in range(num):
            pos = self.findPosition(rect, radius)
            if pos is not None:
                self.planets.append(Planet(type, pos))
                log('PlanetGenerator', 'Created {} planet at ({}, {})'.format(type, pos.x, pos.y))
            else:
                return False
        return True


            
            

                
        

    