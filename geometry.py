"""Collection of useful geometry classes and functions"""


import numpy as np


class Point:
    """A point in 2D-space"""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, p):
        return Point(self.x + p.x, self.y + p.y)
    
    def __sub__(self, p):
        return Point(self.x - p.x, self.y - p.y)
    
    def __mul__(self, k):
        return Point(self.x*k, self.y*k)
    
    def __eq__(self, p):
        return self.x == p.x and self.y == p.y
    
    def __hash__(self):
        return hash(self.x, self.y) 

    def distance(self, p):
        """Return euclidian distance to point p"""
        return np.hypot(p.x - self.x, p.y - self.y)
    
    def vector(self, p):
        """Return a vector from Point p1 to Point p2"""
        return Vector(p.x - self.x, p.y - self.y)
    
    def rect(self, p):
        """Return a rectangle with diagonally opposite Points p1 and p2"""
        if self.x < p.x:
            x1 = self.x
            x2 = p.x
        else:
            x1 = p.x
            x2 = self.x
        if self.y < p.y:
            y1 = self.y
            y2 = p.y
        else:
            y1 = p.y
            y2 = self.y
        return Rect(x1, y1, x2, y2)
    
    def copy(self):
        return Point(self.x, self.y)
    
    def __str__(self):
        return "Point({},{})".format(self.x, self.y)


class Vector:
    """A vector in 2D-Space"""
     
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def abs(self):
        """Return |V|, the length of this vector"""
        return np.hypot(self.x, self.y)
    
    # TODO remove this
    def norm(self):
        """Return ||V||, the norm of this vector"""
        return np.sqrt(self.x*self.x + self.y*self.y)

    def __eq__(self, v):
        return self.x == v.x and self.y == v.y
    
    def __hash__(self):
        return hash(self.x, self.y)

    def __add__(self, v):
        return Vector(self.x + v.x, self.y + v.y)
    
    def __sub__(self, v):
        return Vector(self.x - v.x, self.y + v.y)

    def __mul__(self, k):
        return Vector(self.x*k, self.y*k)
    
    def __truediv__(self, k):
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
    
    def cosAngle(self, v):
        """Returns a value within [-1, 1]"""
        return self.dot(v)/np.sqrt(self.dot(self)*v.dot(v))
    
    def angle(self, v):
        """Return angle between self and v (will be within [0,pi])"""
        return np.arccos(self.cosAngle(v))
        
    def __str__(self):
        return "Vector({},{})".format(self.x, self.y)


Y_AXIS = Vector(0, 1)
X_AXIS = Vector(1, 0)

class Rect:
    """A rectangle"""
    
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
    
    def __str__(self):
        return 'Rect({},{},{},{})'.format(self.xmin,self.ymin, self.xmax, self.ymax)
    

class Circle:
    """A circle"""
    
    _2pi = np.pi*2 # silly optimization
    _pi2 = np.pi/2 # ditto
    
    def __init__(self, center, r):
        self.center = center.copy()
        self.radius = r

        
    def __contains__(self, p):
        c = self.center
        return np.hypot(p.x - c.x, p.y - c.y) <= self.radius
    
    def pointAtAngle(self, a):
        """Return point P on circle such that y-axis and MP enclose angle a
        
        a increases clockwise
        """
        
        a = self._pi2 - a
        return Point(self.center.x + np.cos(a)*self.radius,
                     self.center.y + np.sin(a)*self.radius)
        
    def polarAngleTo(self, P):
        """Return angle between y-axis and line MP
        
        a increases clockwise
        """
        
        # careful, y component comes first here
        a = np.arctan2(P.y - self.center.y, P.x - self.center.x) 
        a = self._pi2 - a
        return a if a > 0 else a + self._2pi
    
    def intersectFrom(self, I, O):
        """Return point at with the circle meets intersecting line IO.
        
            @I     point inside
            @O     point outside
            
        There are many ways to do this. The fastest way seems to be
        to simply solve the quadratic equation. (The assumption here
        is that trigonometric functions are slower to compute than
        square roots)
        """
        
        # Easier to solve if circle has center (0, 0)
        I -= self.center
        O -= self.center
        
        v = I.vector(O)
        # We solve (I.x + t*v.x)^2 + (I.y + t*v.y)^2 = r^2 for t
        a = v.x*v.x + v.y*v.y
        b = 2*(I.x*v.x + I.y*v.y)
        c = I.x*I.x + I.y*I.y - self.radius*self.radius
        
        # Note that we can ignore the second solution here, because
        # t *has* to be positive.
        tmp = b*b - 4*a*c
        assert tmp >= 0
        t = (-b + np.sqrt(tmp))/(2*a)
        # Need to add back center point
        return Point(I.x + self.center.x + t*v.x, 
                     I.y + self.center.y + t*v.y)
        
        
    def __str__(self):
        return 'Circle({},{},{})'.format(self.center.x, self.center.y, self.radius)
        
        
    


    