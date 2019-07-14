import random
import numpy as np

from .geometry import Point


def log(who, what):
    """Always need minimal logging"""
    print('{}: {}'.format(who, what))


def updateExisting(d, *dicts, **kwds):
    """Update existing entries of dict d with entries from dicts and kwds

    It is an error if o contains keys not present in d
    """

    dicts = list(dicts)
    dicts.append(kwds)
    if all(k in d for k in dict for dict in dicts):
        for dict in dicts:
            d.update(dict)
        return d
    else:
        for dict in dicts:
            for k in dict:
                if k not in d:
                    raise ValueError('Key not in dict: ' + k)
        raise Exception('Something weird has happended')


def updateDefaults(d, *dicts, **kwds):
    """Return a new dictionary with defaults from d and updates from o"""

    return updateExisting(d.copy(), *dicts, **kwds)


def randomFloat(a, b):
    """Return a random floating point number a <= x <= b"""

    return random.uniform(a, b)


def randomPointRect(rect):
    """Return a random point within the given rectangle"""

    return Point(rect.xmin + random.random() * rect.width(),
                 rect.ymin + random.random() * rect.height())


def randomPointCircle(circle):
    """Return a random point within the given circle"""

    angle = random.uniform(0, 2*np.pi)
    d = random.uniform(0, circle.radius)
    return Point(np.cos(angle)*d, np.sin(angle)*d)


def expScalingFunction(base):
        """Return a scaling function

        @base    base value, must be > 1

        A common problem is to have some "sensible" positive value,
        that should be adjustable, within a "sensible" (positive) range.

        This provides a function, that can be called with (value, scale),
        where
            @value    is the defined (sensible) value
            @scale    is the scaling factor, should be within [-s, s]

        The function will return a value that
            - is always positive (never zero)
            - is unchanged for s = 0
            - will be larger for larger values of scale
            - will be smalller for smaller values of scale
        """
        def scale(value, scale, b=base):
            return value*pow(b, scale)

        return scale


class Interval:
    """Interval for floating point values

        @start    start value (inclusive)
        @end      end value (inclusive)
    """

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __contains__(self, v):
        return self.start <= v <= self.end

    def random(self):
        return randomFloat(self.start, self.end)


class Color:
    """Simple color class

        @r      Red component (0-255)
        @g      Green component (0-255)
        @b      Blue component (0-255)
    """

    def __init__(self, r, g, b):
        self.r = r
        self.g = g
        self.b = b

    def tkString(self):
        """Translate RGB-components into a valid tk color string"""
        # Make sure values are within range
        r = int(self.r) & 0xff
        g = int(self.g) & 0xff
        b = int(self.b) & 0xff
        return '#{:0>2x}{:0>2x}{:0>2x}'.format(r, g, b)

    def __add__(self, col):
        return Color(self.r + col.r, self.g + col.g, self.b + col.b)

    def __mul__(self, k):
        return Color(self.r*k, self.g*k, self.b*k)

    def add(self, red=0, green=0, blue=0):
        return Color(self.r + red, self.g + green, self.b + blue)
