import random
import math
from geometry import Point
from math import pi


def log(who, what):
    """Always need minimal logging"""
    print('{}: {}'.format(who, what))


def randomFloat(a, b):
    """Return a random floating point number a <= x <= b"""
    
    return random.uniform(a, b)


def randomPointRect(rect):
    """Return a random point within the given rectangle"""
    
    return Point(rect.xmin + random.random() * rect.width(),
                 rect.ymin + random.random() * rect.height())


def randomPointCircle(circle):
    """Return a random point within the given circle"""
    
    angle = random.uniform(0, 2*pi)
    d = random.uniform(0, circle.radius)
    return Point(math.cos(angle)*d, math.sin(angle)*d)
    

class Intervall:
    def __init__(self, start, end):
        self.start = start
        self.end = end
        
    def random(self):
        return randomFloat(self.start, self.end)
