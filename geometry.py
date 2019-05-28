"""Collection of useful geometric function"""

# Helpers for geometrical stuff

from math import sqrt, sin, cos, acos, asin, pi


class Point:
    """A point in 2D-space"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, v):
        return Point(self.x + v.x, self.y + v.y)

    def copy(self):
        return Point(self.x, self.y)
    
    def __str__(self):
        return "[{},{}]".format(self.x, self.y)


class Vector:
    """A vector in 2D-Space"""
     
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def norm(self):
        """Return ||V||, the norm of this vector"""
        return sqrt(self.x*self.x + self.y*self.y)

    def __add__(self, v):
        return Vector(self.x + v.x, self.y + v.y)

    def __mul__(self, k):
        return Vector(self.x*k, self.y*k)
    
    def __div__(self, k):
        return self*(1/k)
    
    def copy(self):
        return Vector(self.x, self.y)
    
    def dot(self, v):
        """Dot product"""
        return self.x*v.x + self.y*v.y

    def normalize(self):
        """Make this vector have length 1"""
        self.scaleTo(1)
        return self

    def scaleTo(self, l):
        """Make this vector have length l"""
        d = l/self.norm()
        self.x *= d
        self.y *= d
        return self
    
    def angle(self, v):
        """Return angle between self and v (will be within [0,pi])"""
        return acos(self.dot(v)/(self.norm()*v.norm()))
        
    
    def __str__(self):
        return "({},{})".format(self.x, self.y)


def vectorPP(p1, p2):
    """Return a vector from Point p1 to Point p2"""
    return Vector(p2.x - p1.x, p2.y - p1.y)


class Rect:
    """A rectangle, yes, really"""
    
    def __init__(self, x1, y1, x2, y2):
        self.xmin = x1
        self.ymin = y1
        self.xmax = x2
        self.ymax = y2

    def __contains__(self, p):
        """Returns true if Point p is within this rectangle, else false"""
        return p.x >= self.xmin and p.x <= self.xmax \
                and p.y >= self.ymin and p.y <= self.ymax
                
    def copy(self):
        return Rect(self.xmin, self.ymin, self.xmax, self.ymax)
                
    def width(self): 
        return self.xmax - self.xmin
    
    def height(self): 
        return self.ymax - self.ymin
    

def rectPP(p1, p2):
    """Return a rectangle with diagonally opposite Points p1 and p2"""
    if p1.x < p2.x:
        x1 = p1.x
        x2 = p2.x
    else:
        x1 = p2.x
        x2 = p1.x
    if p1.y < p2.y:
        y1 = p1.y
        y2 = p2.y
    else:
        y1 = p2.y
        y2 = p1.y
    return Rect(x1, y1, x2, y2)
    

class Circle:
    """A round thing"""
    
    def __init__(self, center, r):
        self.center = center
        self.radius = r
        
    def __contains__(self, p):
        return distancePP(self.center, p) <= self.radius
    
    def pointAt(self, angle):
        return Point(self.center.x + cos(angle)*self.radius,
                     self.center.y + sin(angle)*self.radius)
    
    

def distance2d(x1, y1, x2, y2):
    dx = x2-x1
    dy = y2-y1
    return sqrt(dx*dx + dy*dy)

def distancePP(p1, p2):
    return distance2d(p1.x, p1.y, p2.x, p2.y)

    