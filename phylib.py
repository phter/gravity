"""
phylib - physics library

Units:
Unless specified otherwise, those units are used:
    
  meters    - for length
  seconds   - for time
  kilogram  - for mass
  radians   - for angles
  
  
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


# 
# Earth
# 

class Planet:
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

def escapeSpeed(mass, radius, G=GConst):
    """Minimal speed needed to escape the gravitational force of mass
    
    Usually called escape velocity - but, strictly speaking, that needs
    to be a vector. So here it's called speed.
    """
    return math.sqrt(2*G*mass/radius)
