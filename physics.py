"""Collection of classes and functions for the physical model

We model the universe as a vector field, where each point in space
has an associated vector, representing the total gravitational force
of all bodies combined at this point.

"""

import numpy as np
from geometry import Point, Vector, Circle
from config import Config
from util import log
import phylib



class Body(Circle):
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
        Circle.__init__(self, pos, radius)
        self.id = None # will be set later
        self.type = type
        self.pos = self.center
        self.rotation = rotation
        self.density = density
        self.mass = density*np.pi*np.power(radius, 3)*4/3
        self.poleOrbit = self.orbit(0, 0)
    
    def polePointAt(self, t):
        """Return pole point at time t"""
        return self.pointAtAngle(self.bodyAngleAt(t))
    
    def bodyAngleAt(self, t):
        """Return angle of center-pole line relative to y-axis"""
        return self.rotation * t
    
    def yAngleTo(self, P):
        """Return angle between y-axis and center-P line"""
        return self.polarAngleTo(P)
    
    def poleAnglePointAt(self, P, t):
        """Return angle between pole line and center-P line"""
        return self.yAngleTo(P) - self.bodyAngleAt(t)
    
    def orbit(self, t, yAngle):
        """Return an orbit starting at the given angle (rel. to y-axis)"""
        
        return SurfaceOrbit(t, self, yAngle - self.bodyAngleAt(t))
    
    def escapeSpeed(self, gravity, radius=None):
        if radius is None:
            radius = self.radius
        return phylib.escapeSpeed(self.mass, radius, gravity)
    
    
class Universe:
    """Game universe

        @bodies     list of bodies,
                    the first two must be start and target planets
        @rect       The visible universe
        @gravity    gravitational constant
    
    """
    def __init__(self, bodies, rect, gravity):
        self.rect = rect
        self.bodies = bodies
        self.gravity = gravity
        self.createArrays()
        
    def createArrays(self):
        nBodies = len(self.bodies)
        # Data arrays
        self.bodyPos = np.array([[body.pos.x, body.pos.y] for body in self.bodies])
        self.aMassG = np.array([body.mass*self.gravity for body in self.bodies])
        self.aRes = np.zeros(2)
        # Buffers
        self.aVec = np.copy(self.bodyPos)
        self.aBuf = np.zeros(nBodies)
        # Views
        self.aVecX = self.aVec[:,0]
        self.aVecY = self.aVec[:,1]
       
    def gravityVector(self, pos, gv):
        """Return the gravitational force vector at a given position
        
            @pos    Point in Universe
            @gv     Vector to store result in
            
        Note: This is done in numpy-style mainly as an excercise.
        We do not have many bodies, so this is only 10-15% faster than
        doing it in pure python.
        """
        aRes = self.aRes
        aVec = self.aVec
        aBuf = self.aBuf
        
        np.copyto(aVec, self.bodyPos)
        aRes[0] = pos.x
        aRes[1] = pos.y
        # Create Vectors from position to body center
        aVec -= aRes
        # The gravitational force f = GM/d**2
        # We want to scale each vector to a length of f, so we need to 
        # first normalize it, then multiply by f, thus we get
        #    v_f = v/|v| * GM/d**2
        #        = v/d * GM/d**2
        #        = v * GM/d**3
        np.hypot(self.aVecX, self.aVecY, out=aBuf)
        aBuf **= 3
        np.divide(self.aMassG, aBuf, out=aBuf)
        aVec *= aBuf[:, np.newaxis]
        # Now we just need to sum all gravitational forces into one vector.
        aVec.sum(axis=0, out=aRes)
        gv.x = aRes[0]
        gv.y = aRes[1]
        return gv

    
class ObjectPath:
    """Base class for orbits and trajectories"""
    
    def __init__(self, startTime):
        self.startTime = startTime
        self.endTime = np.Inf
    
    def positionAt(self, t):
        """Return position of object at time t"""
        raise NotImplementedError()
    
    def length(self):
        """Return total length of path"""
        raise NotImplementedError()
    
    def duration(self):
        """Return total time object moved"""
        return self.endTime - self.startTime
    
    def logState(self, t):
        log('log', str(self))
    
    
class SurfaceOrbit(ObjectPath):
    """Path of an object on the surface of a body
    
        @startTime        time at which object enters orbit
        @body             body at center of orbit
        @pAngle           angle relative to body's pole
    """
    
    def __init__(self, startTime, body, pAngle):
        ObjectPath.__init__(self, startTime)
        # Orbit should be a little bit above ground (which makes sense anyway).
        # This is important, because if an orbit point is inside
        # the body, we get an error when launching a ship
        self.circle = body
        self.body = body
        self.center = body.pos
        # Angle relative to y-axis
        self.pAngle = pAngle
        
    def positionAt(self, t):
        return self.circle.pointAtAngle(self.yAngleAt(t))
    
    def yAngleAt(self, t):
        return self.body.bodyAngleAt(t) + self.pAngle
    
    def posVelocity(self, t):
        pos = self.positionAt(t)
        v = self.center.vector(pos)
        # Create a normal vector by rotating v clockwise by 90 degrees
        v.x, v.y = v.y, -v.x
        # Scale vector to tangential speed
        # Note that if rotation is negative (body rotating counterclockwise)
        # then the vector will point in the opposite direction, ie
        # this will do the right thing.
        v.scaleTo(self.body.rotation*self.circle.radius)
        return (pos, v)
    
    def length(self):
        # This is correct: we measure rotation speed in radians / time unit
        # Thus, in 2*pi time units an object on the surface travels
        # 2*r*pi length units, ie. the full circumference. So dividing
        # by 2*pi gives us r length units per time unit.
        return self.duration()*self.body.radius
    
    def __str__(self):
        return 'Orbit(x={x},y={y},r={r},a={a})'.format(
                x=self.circle.center.x,
                y=self.circle.center.y,
                r=self.circle.radius,
                a=self.pAngle)
        
        
    
class TrajectoryState:
    """Helper class for calculating trajectories"""
    def __init__(self, time, seg):
        self.fill(time, seg)
        
    def fill(self, time, seg):
        self.time = time
        self.pos = Point(seg[0], seg[1])
        self.velocity = Vector(seg[2], seg[3])
        self.length = seg[4]
        
    def segment(self):
        return (self.pos.x, self.pos.y, self.velocity.x, self.velocity.y, self.length)
        

class Trajectory(ObjectPath):
    """Tracectory of a particle in the universe
    
        @t               start time
        @pos             initial position
        @velocity        velocity vector
        @universe        the universe we move in
        @max_len         maximum length of trajectory
        @max_err         maximum error of trajectory
        
    So how does this work?
        
    *) We approximate the curve of the trajectory by a polygon. At each point,
       we add the combined gravity vector of all objects in the universe
       to the current velocity: this is our new velocity vector.
       Then we multiply that vector by a small amount (dt), which gives us
       the next point of the trajectory. And so on, until we hit a planet
       or move outside the universe frame.
           
    *) How do we choose dt?
       1) We could use a fixed value.
          This is simple but not very efficient / accurate.
              
       2) We can adapt dt to the curvature of the trajectory.
          This is what we try to do here.
    """
    
    def __init__(self,
                 t,
                 pos,
                 velocity,
                 universe,
                 onHit,
                 onOutOfRect,
                 max_len=Config.maxTrajectoryLength,
                 max_err=Config.maxTrajectoryError):
        
        ObjectPath.__init__(self, t)
        self.universe = universe
        self.startPos = pos.copy()
        self.max_len = max_len
        self.max_err = max_err
        self.onOutOfRect = onOutOfRect
        self.onHit = onHit
        self.min_seg_len = Config.minPolySegmentLength
        self.max_seg_len = Config.maxPolySegmentLength
        
        # min_seg_len is the different to min_seg_calc:
        # one is the minimum segment length, we (eventually)
        # store in the array.
        # the other (min_seg_calc) is the the minimum segment, we use
        # to calculate the trajectory.
        self.min_seg_calc = self.min_seg_len/10
        
        # Cumulative error
        self.cumError = 0
  
        # some little extra to take rounding errors into account
        arrSize = int(self.max_len/self.min_seg_len * 1.05)
        
        # The first array contains the time values, 
        # the second one contains the the positions, veocities and path lengths
        # Why two arrays?
        # Because np.searchSorted() only works on 1-dimensional arrays.
        self.timeBuffer = np.zeros(arrSize, dtype=np.double)
        self.segBuffer = np.zeros((arrSize, 5), dtype=np.double)
        
        self.timeBuffer[0] = t
        # (xPos, yPos, xVel, yVel, path length)
        self.segBuffer[0] = (pos.x, pos.y, velocity.x, velocity.y, 0)

        # Time and segment arrays
        # Note that numpy slices are *views* for the underlying array,
        # no data is copied here.
        self.segments = self.segBuffer[:1]
        self.time = self.timeBuffer[:1]
        
        self.state = TrajectoryState(t, self.segments[0])
        self.state2 = TrajectoryState(t, self.segments[0])
        
        self.orbits = [body.poleOrbit for body in self.universe.bodies]
        
        self.calculatedSegments = 0
        
        # Buffers to reduce amount of allocated Vector objects
        self.tmpVec1 = Vector(0, 0)
        self.tmpVec2 = Vector(0, 0)
        self.tmpVec3 = Vector(0, 0)
        self.tmpVec4 = Vector(0, 0)
        
    def __len__(self):
        return len(self.time)
    
    def __str__(self):
        seg = self.segments[-1]
        return 'Trajectory(t={t},pos=({px},{py}),vel=({vx},{vy}))'.format(
                t=self.time[-1],
                px=seg[0],
                py=seg[1],
                vx=seg[2],
                vy=seg[3])
        
    def logTrajectory(self):
        s = """Start time: {st}
        End time: {et}
        Total segments calculated: {ts}
        Segments stored: {ss}
        Average error: {ae}""".format(
                st=self.startTime,
                et=self.endTime,
                ts=self.calculatedSegments,
                ss=len(self.time),
                ae=self.cumError/self.calculatedSegments)
        
        log('Trajectory',s)
    
    def addState(self, s):
        """Add another segment point at the end of the array"""
        index = len(self.segments)
        self.timeBuffer[index] = s.time
        self.segBuffer[index] = s.segment()
        # Resize views
        self.time = self.timeBuffer[:index + 1]
        self.segments = self.segBuffer[:index + 1]
        
    def update(self, t):
        if self.time[-1] > t:
            return
        self.calculate(t)
        
    def positionAt(self, t):
        if t < self.startTime or t > self.endTime:
            return None
        last = len(self.time) - 1
        if self.time[last] < t:
            return None
        if last < 1:
            return None
        
        # Try this first, because this will be most often true
        if t >= self.time[last - 1]:
            return self.segmentPoint(last - 1, t)
        
        i = self.getSegmentIndex(t)
        return self.segmentPoint(i, t)
        
    def getSegmentIndex(self, t):
        """Return segment index such that segStart <= t <= segEnd"""
        i = self.time.searchsorted(t, side='right') - 1
        assert 0 <= i < len(self.time) - 1
        return i
        
    def segmentPoint(self, index, t):
        """Return position at time t, when segStart <= time <= segEnd"""
        assert self.time[index] <= t <= self.time[index + 1]
        # Since v1*d + v2*(1-d) gives a point between v1 and v2
        # for 0 <= d <= 1, we just need to find d:
        d1 = t - self.time[index]
        d2 = self.time[index + 1] - t
        d = d1/(d1 + d2)
        seg = self.segments
        return Point(seg[index, 0] * (1 - d) + seg[index + 1, 0] * d,
                     seg[index, 1] * (1 - d) + seg[index + 1, 1] * d)
        
    def calculate(self, targetTime):
        """Calculate trajectory segments until targetTime
        
        When this function returns, it is not guaranteed that the time 
        of the last segment point is exaclty targetTime. Nor is it guaranteed,
        that the last time is bigger than targetTime.
        Possible outcomes ("time" is time of last segment point)
            *) time >= targetTime
               In this case, targetTime will be between start and end of
               the last segment
            *) time < targetTime
               Multiple possibilities:
                   *) We hit a planet
                   *) We moved outside of the universe frame
                   *) Buffer size / configuration limits have been exceeded
        Return value:
            True - target time within last segment
            False - otherwise
        """

        state = self.state
        state.fill(self.time[-1], self.segments[-1])
        lState = self.state2
        lState.fill(state.time, state.segment()) # copy of state

        while state.time < targetTime:
            # run out of buffer space?
            if len(self.time) == len(self.timeBuffer):
                return False
            
            seg_err = self.calculate_segment(state)
            
            # moved out of universe frame?
            if  state.pos not in self.universe.rect:
                self.logTrajectory()
                self.onOutOfRect(state.time, state.pos)
                return False
            
            # Reached trajectory limit?
            if state.length > self.max_len:
                return False
            
            for orbit in self.orbits:
                if state.pos in orbit.circle:
                    circ = orbit.circle
                    # Note the order here: the first point has to lie
                    # within the circle
                    m = circ.intersectFrom(state.pos, lState.pos)
                    yAngle = circ.polarAngleTo(m)
                    # adjust values for landing spot
                    d = lState.pos.distance(m)/lState.pos.distance(state.pos)
                    state.time = lState.time + (state.time - lState.time)*d
                    state.pos = lState.pos*(1 - d) + state.pos*d
                    # Since we landed, velocity is zero
                    state.velocity = Vector(0, 0)
                    state.length = lState.length + (state.length - lState.length)*d
                    self.addState(state)
                    self.cumError += seg_err*d
                    self.endTime = state.time
                    self.logTrajectory()
                    self.onHit(state.time, orbit.body, yAngle)
                    return True if state.time > targetTime else False
            
            self.addState(state)
            self.cumError += seg_err
            state, lState = lState, state
             
        return True
        
    def vError(self, force, velocity):
        """Calculates the area of the parallelogram spanned by the two vectors"""
        return np.abs(force.x*velocity.y - force.y*velocity.x)
        
    def calculate_segment(self, state):
        """Calculate one segment of the trajectory
        
            @state       Trajectory state
            
            @returns     estimated error
        
        Given time, position and velocity of a particle in the universe,
        compute new position and velocity after a small amount of time.
        
        Here we combine two strategies:
        1) Instead of adding the gravitational acceleration to the 
           velocity directly, we guess a value for the time delta (dt) and
           compute the gravitation at the point where the particle
           would be after that time. Then we take the average of the
           current and the would-be gravitational force, multiply it
           by dt and add it to the velocity vector.
           
           This is known as a "predictor-corrector method" for
           numerically integrating a set of differential equations.
           Another option would be to use the "Runge-Kutta" method,
           which is more accurate but slightly more complex.

           
        2) We use an adaptive algorithm for determining the value of dt.
           The more the trajectory is curved, the smaller dt needs to be.
           A good error measure is the area of the triangle that is
           created by the velocity and gravity vectors: if the vectors are
           parallel, the area (error) is zero and if they are
           perpendicular, the area (error) is at its maximum.
           Also, this is especially easy to compute.
        
        """
        gravityAt = self.universe.gravityVector
        seg_len = 0
        seg_err = 0
        
        # Take a first guess for a sensible dt value
        dt = self.min_seg_calc/state.velocity.norm()
        gv = self.tmpVec1
        aGrav = self.tmpVec2
        nPos = self.tmpVec3
        dVel = self.tmpVec4
        while seg_len < self.min_seg_len:
            gravityAt(state.pos, gv)
            #log('calculate_segment', '({s.x},{s.y}): gravity ({g.x}, {g.y}), v = {v}'.format(s=state.pos, g=gv, v=gv.norm()))
            
            # Need to be initialized here
            # aGrav = None    # average gravity current, next point
            # dGrav = None    # gravitational acceleration
            # dMove = None    # movement of particle
            ndt = dt
            dmx = 0
            dmy = 0
            dml = 0
            err = 0
            
            # Adjust ndt to reduce approximation error
            while True:
                self.calculatedSegments += 1
                # aGrav = (gv + gravityAt(state.pos + (gv + state.velocity)*ndt))/2
                nPos.x = state.pos.x + (gv.x + state.velocity.x)*ndt
                nPos.y = state.pos.y + (gv.y + state.velocity.y)*ndt
                
                #gravityAt(state.pos + (gv + state.velocity)*ndt, aGrav)
                gravityAt(nPos, aGrav)
                aGrav.x = (aGrav.x + gv.x)/2 * ndt
                aGrav.y = (aGrav.y + gv.y)/2 * ndt
                # dGrav = aGrav*ndt
                # dVel = state.velocity*ndt
                dVel.x = state.velocity.x*ndt
                dVel.y = state.velocity.y*ndt
                dmx = aGrav.x + dVel.x
                dmy = aGrav.y + dVel.y
                err = self.vError(aGrav, dVel)
                if err < self.max_err:
                    break
                #if dMove.norm() < self.min_seg_calc:
                dml = np.hypot(dmx, dmy)
                if dml < self.min_seg_calc:
                    break
                ndt *= 0.66
            
            state.velocity.x += aGrav.x
            state.velocity.y += aGrav.y
            #state.pos += dMove
            state.pos.x += dmx
            state.pos.y += dmy
            state.time += ndt
            # seg_len += dMove.norm()
            seg_len += dml
            seg_err += err
            
            if seg_len > self.max_seg_len:
                break
            # Try to increase time delta only if it hasn't just been decreased
            if dt == ndt:
                dt *= 1.5
            else:
                dt = ndt
                
        state.length += seg_len
        return err
    
    
    
