"""Collection of classes and functions for the physical model

We model the universe as a vector field, where each point in space
has an associated vector, representing the total gravitational force
of all bodies combined at this point.

"""
import math

from math import sqrt, pow as fpow # use this for floating point numbers
from geometry import Point, Vector, distance2d, vectorPP, distancePP


# Newton's constant
GRAV_KONST = 6.67408E-11    # in m^3/kg*s^2


class Body:
    """ Body - generic object in the game universe
    
    @pos         position (Point)
    @radius      radius of object
    @rotation    angular velocity of body
                 in radians  / time unit
                  0: no rotation
                 >0: clockwise
                 <0: counterclockwise
    """
    def __init__(self, type, pos, radius, rotation, density):
        self.id = None # will be set later
        self.type = type
        self.pos = pos.copy()
        self.radius = radius
        self.rotation = rotation
        self.density = density
        self.mass = planetMass(radius, density)
    
    def __contains__(self, pos):
        return distance2d(self.pos.x, self.pos.y, pos.x, pos.y) <= self.radius

    def angle(self, t):
        """Returns angle at time t"""
        return self.rotation * t
    
    def orbitPoint(self, angle):
        """Return the point on the orbit at the given angle"""
        return Point(self.pos.x + self.radius*math.cos(angle), 
                     self.pos.y + self.radius*math.sin(angle))
        
   


def planetMass(radius, density):
    """Calculate mass of object for given density"""
    return math.pi*fpow(radius, 3)*4/3


def gForce(mass, distance):
    """Return gravitational force at distance from center of mass"""
    return GRAV_KONST*mass/(distance*distance)


def gravVector(center, mass, point):
    v = Vector(point, center)
    v.scaleTo(gForce(mass, v.norm()))
    
    

class Universe:
    """Game universe

        @bodies     list of bodies,
                    the first two must be start and target planets
    
    """
    def __init__(self, bodies):
        self.bodies = bodies
        
    def gVector(self, pos):
        """Return the gravitational force vector at a given position"""
        # TODO what if pos is inside a planet?
        gv = Vector(0, 0)
        for body in self.bodies:
            gv += gravVector(body.pos, body.mass, pos)
        return gv
    
    
def calculateTrajectory(pos,
                        velocity,
                        universe, 
                        rect,
                        max_time,
                        max_length,
                        timeDelta,
                        mError,
                        min_dt,
                        max_dt):
    """Calculate the trajectory of a particle in space
    
        @pos          initial position of particle
        @velocity     velocity vector
        @universe 
        @rect         rectangle we should stay in
        @max_time      maximum flight time
        @max_length    maximum flight distance
        @timeDelta    initial time interval
        @mError       error margin: lower value = higher accuracy
        @min_dt       minimal resolution
        @max_dt       maximum resolution
        
        @returns      a list of (time, pos, length, velocity) tuples
    
    So how does this work?
    *) We approximate the curve of the tracejtory by a polygon. At each point,
            we add the gravity vector to the current velocity and multiply
            the result by a small amount (dt)
    *) So how do we choose dt?
         1) We could use a fixed value.
            This is simple but not very efficient.
         2) We can adapt dt to the curvature of the trajectory.
    
    """
    
    bodies = universe.bodies
    dt = timeDelta
    hit = None
    trajectory = [(0, pos.copy(), 0, velocity.copy())]

    while hit is None:
        time, pos, length, velocity = trajectory[-1]

        gv1 = universe.gVector(pos) # gravity at current position
        gv2 = None                  # gravity at next position
        gv12 = None                 # average gravity current and next position
        tries = 1
        while True:
            d_gv1 = gv1*dt
            gv2 = universe.gVector(pos + d_gv1)
            gv12 = (gv1 + gv2)/2
            if dt < min_dt:
                dt = min_dt
                break
            d_v = velocity*dt
            d_gv12 = gv12*dt
            if distancePP(d_gv12, d_v) < mError:
                break
            dt *= 0.66
            tries += 1
        
        n_velocity = gv12 + velocity
        n_pos = pos + n_velocity*dt
        n_time = time + dt
        
        if n_time > max_time:
            break
        
        if n_pos not in rect:
            break
        
        n_length = length + distancePP(pos, n_pos)
        if n_length > max_length:
            break
        
        for body in bodies:
            if n_pos in body:
                n_pos = calculate_landing_spot(pos, n_pos, body)
                hit = body
                break
        
        if tries == 1:
            dt *= 1.5
        trajectory.append((n_time, n_pos, n_length, n_velocity))

    return (hit, trajectory)
        

# TODO: make this less stupid
def calculate_landing_spot(pos, n_pos, body):
    v = vectorPP(n_pos, pos)
    w = vectorPP(n_pos, body.pos)
    dv1 = v.dot(w)/v.norm()
    q = n_pos + v.copy().scaleTo(dv1)
    dm = distancePP(q, body.pos)
    r = body.radius
    dv2 = sqrt(r*r - dm*dm)
    return n_pos + v.scaleTo(dv1 + dv2)
    
