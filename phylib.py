"""
phylib - physics library

Units:
Unless specified otherwise, those units are used:

  meters    - for length
  seconds   - for time
  kilogram  - for mass
  radians   - for angles

These will also be used for compound units like density, etc.


NOTE:
* speed is always a scalar
* velocity is always a vector
"""

import math


# --------------------------------------------------------------------------
# Constants
# --------------------------------------------------------------------------

# Gravitational constant (Newton) in m^3/(kg*s^2))
GConst = 6.67408e-11

# Speed of light
speedLight = 299_792_458


class Planet:
    """A planet

        @radius              in m
        @density             in kg/m^3
        @angularSpeed        in radians/s
    """

    def __init__(self, radius, density, angularSpeed):
        self.radius = radius
        self.density = density
        self.angularSpeed = angularSpeed

        self.diameter = 2*self.radius
        self.circumference = 2*math.pi*self.radius
        self.volume = 4/3*math.pi*self.radius**3
        self.mass = self.volume*self.density


earth = Planet(density=551_000,
               angularSpeed=7.292_115e-5,
               radius=6371000)


# --------------------------------------------------------------------------
# functions
# --------------------------------------------------------------------------

def orbitalSpeed(mass, radius, G=GConst):
    """Return needed speed to stay in an orbit around a mass

        @mass     mass of object in center
        @radius   radius of orbit
        @G        gravitational constant
    """

    return math.sqrt(G*mass/radius)

def escapeSpeed(mass, distance, G=GConst):
    """Minimal speed needed to escape the gravitational force of mass

        @mass        mass of body
        @radius      distance of object from center of mass
        @G           gravitational constant

    Note: this is unusual, but correct, terminology!
    The usual term - escape velocity - implies a *direction*.
    However, the escape speed of an object is NOT dependant on
    the angle at which it leaves a body. So it really should be
    called speed and not velocity.

    Why is this true?
    Geometrically, this is hard to understand. But by using the law
    of energy conservation, this becomes almost trivial:
    Kinetic energy of a body is K = m*v^2/2
    Gravitational potential energy is U = -G*m*M/r
    Escape speed is the speed at which K + U = 0, which gives
        v = sqrt(2*G*M/r)
    And this is independant of direction.
    """

    return math.sqrt(2*G*mass/distance)
