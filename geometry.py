"""Collection of useful geometry classes and functions"""


import numpy as np


PI_2 = np.pi/2
PI_4 = np.pi/4

def angleM2Y(a):
    """Convert mathematical angle to angle relative to Y-axis

    mathematical: starting at (1, 0), increases counterclockwise (-inf, inf)
    Y-angle:      starting at (0, 1), increases clockwise (-inf, inf)
    """
    return PI_2 - a

angleY2M = angleM2Y
"""Convert angle relative to Y-axis to mathematical angle

mathematical: starting at (1, 0), increases counterclockwise (-inf, inf)
Y-angle:      starting at (0, 1), increases clockwise (-inf, inf)
"""


class NPAView:
    def __init__(self, npa):
        self.npa = npa

    def __getitem__(self, i): return self.npa[i]
    def __setitem__(self, i, v): self.npa[i] = v

    def __add__(self, p):
        return self._make(np.add(self.npa, p.npa))

    def __sub__(self, p):
        return self._make(np.subtract(self.npa, p.npa))

    def __mul__(self, k):
        return self._make(np.multiply(self.npa, k))

    def __truediv__(self, k):
        return self._make(np.divide(self.npa, k))

    def __iadd__(self, p):
        self.npa += p.npa
        return self

    def __isub__(self, p):
        self.npa -= p.npa
        return self

    def __imul__(self, k):
        self.npa *= k
        return self

    def __itruediv__(self, k):
        self.npa /= k
        return self

    def copy(self):
        return self.__class__(self.npa.copy())

    def _make(self):
        raise NotImplementedError()


class Common2(NPAView):
    def __init__(self, x, y=None):
        if y is None:
            if type(x) is np.ndarray and len(x) == 2:
                npa = x
            elif isinstance(x, NPAView):
                npa = x.npa
            else:
                npa = np.array((x[0], x[1]), dtype=np.double)
        else:
            npa = np.array((x, y), dtype=np.double)

        NPAView.__init__(self, npa)

    @property
    def x(self): return self.npa[0]
    @x.setter
    def x(self, v): self.npa[0] = v

    @property
    def y(self): return self.npa[1]
    @y.setter
    def y(self, v): self.npa[1] = v

    def __eq__(self, p):
        return self.npa[0] == p.npa[0] and self.npa[1] == p.npa[1]

    def __hash__(self):
        return hash(self.npa[0], self.npa[1])


class Point(Common2):
    """A point in 2D-space"""

    def __init__(self, x, y=None):
        Common2.__init__(self, x, y)

    def _make(self, a):
        return Point(a)

    def distance(self, p):
        """Return euclidian distance to point p"""
        return np.hypot(p.npa[0] - self.npa[0], p.npa[1] - self.npa[1])

    def vector(self, p):
        """Return a vector from Point p1 to Point p2"""
        return Vector(p.npa - self.npa)

    def rect(self, p):
        """Return a rectangle with diagonally opposite Points p1 and p2"""
        return Rect(self, p)

    def __str__(self):
        return "Point({},{})".format(*self.npa)


class Vector(Common2):
    """A vector in 2D-Space"""

    def __init__(self, x, y=None):
        Common2.__init__(self, x, y)

    def _make(self, a):
        return Vector(a)

    def abs(self):
        """Return |V|, the length of this vector"""
        return np.hypot(self.npa[0], self.npa[1])

    def dot(self, v):
        """Dot product"""
        return np.dot(self.npa, v.npa)

    def normalize(self):
        """Make this vector have length 1"""
        self.scaleTo(1)
        return self

    # TODO this should not be inplace
    def scaleTo(self, l):
        """Make this vector have length l"""
        d = l/self.abs()
        self.npa *= d
        return self

    def cosAngle(self, v):
        """Cosine of angle between self and v

        Returns a value within [-1, 1]
        """
        ma = self.npa
        oa = v.npa
        return np.dot(ma, oa)/np.sqrt(np.dot(ma, ma)*np.dot(oa, oa))

    def angle(self, v):
        """Angle between self and v

        Returns a value within [0, pi]
        """
        return np.arccos(self.cosAngle(v))

    def __str__(self):
        return "Vector({},{})".format(*self.npa)


Y_AXIS = Vector(0, 1)
X_AXIS = Vector(1, 0)


class Rect:
    """A rectangle"""

    def __init__(self, x1, y1=None, x2=None, y2=None):
        if type(x1) is np.ndarray and len(x1) == 4:
            self.npa = x1
            x1, y1, x2, y2 = self.npa
        else:
            self.npa = np.zeros(4, dtype=np.double)
            if y1 is None:
                x1, y1, x2, y2 = x1
            elif x2 is None:
                x1, y1, x2, y2 = x1[0], x1[1], y1[0], y1[1]

        x1, x2 = (x1, x2) if x1 < x2 else (x2, x1)
        y1, y2 = (y1, y2) if y1 < y2 else (y2, y1)
        self.npa[:] = (x1, y1, x2, y2)

    @property
    def xmin(self): return self.npa[0]
    @property
    def ymin(self): return self.npa[1]
    @property
    def xmax(self): return self.npa[2]
    @property
    def ymax(self): return self.npa[3]

    def __getitem__(self, i):
        return self.npa[i]

    def __setitem__(self, i, v):
        self.npa[i] = v

    def __contains__(self, p):
        """Returns true if Point p is within this rectangle, else false"""
        r = self.npa
        return  r[0] <= p.x <= r[2] and r[1] <= p.y <= r[3]

    def copy(self):
        return Rect(*self.npa)

    def width(self):
        return self.npa[2] - self.npa[0]

    def height(self):
        return self.npa[3] - self.npa[1]

    def hwRatio(self):
        return self.height() / self.width()

    def __str__(self):
        return 'Rect({},{},{},{})'.format(*self.npa)


class Circle:
    """A circle"""

    def __init__(self, x, y=None, r=None):
        if type(x) is np.ndarray and len(x) == 3:
            self.npa = x
        else:
            if y is None:
                x, y, r = x
            elif r is None:
                x, y, r = x[0], x[1], y
            self.npa = np.array((x, y, r), dtype=np.double)

        self.center = Point(self.npa[0:2])

    @property
    def radius(self): return self.npa[2]
    @radius.setter
    def radius(self, r): self.npa[2] = r

    def __contains__(self, p):
        c = self.npa
        return np.hypot(p[0] - c[0], p[1] - c[1]) <= c[2]

    def pointAtAngle(self, a):
        """Return point P on circle such that y-axis and MP enclose angle a

        a increases clockwise
        """

        a = angleY2M(a)
        p = np.array((np.cos(a), np.sin(a)), dtype=np.double)
        p *= self.npa[2]
        p += self.npa[0:2]
        return Point(p)

    def polarAngleTo(self, p):
        """Return angle between y-axis and line MP

        a increases clockwise
        c.polarAngleTo(c.pointAtAngle(a)) == a (+ 2k Pi)
        """

        # careful, y component comes first here
        a = np.arctan2(p[1] - self.npa[1], p[0] - self.npa[0])
        return angleM2Y(a)

    def intersectFrom(self, I, O):
        """Return point at with the circle meets intersecting line IO.

            @I     point inside
            @O     point outside

        There are many ways to do this. The fastest way seems to be
        to simply solve the quadratic equation. (The assumption here
        is that trigonometric functions are slower to compute than
        square roots)
        """

        arr = self.npa
        r = arr[2]
        # Easier to solve if circle has center (0, 0)
        ix = I[0] - arr[0]
        iy = I[1] - arr[1]
        ox = O[0] - arr[0]
        oy = O[1] - arr[1]

        vx = ox - ix
        vy = oy - iy

        # We solve (I.x + t*v.x)^2 + (I.y + t*v.y)^2 = r^2 for t
        a = vx*vx + vy*vy
        b = 2*(ix*vx + iy*vy)
        c = ix*ix + iy*iy - r*r

        # Note that we can ignore the second solution here, because
        # t *has* to be positive.
        tmp = b*b - 4*a*c
        assert tmp >= 0
        t = (-b + np.sqrt(tmp))/(2*a)
        # Need to add back center point
        res = np.array((vx, vy), dtype=np.double)
        res *= t
        res += self.npa[0:2]
        res[0] += ix
        res[1] += iy
        return Point(res)

    def __str__(self):
        return 'Circle({},{},{})'.format(*self.npa)
