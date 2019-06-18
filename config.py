"""
Configuration and settings

There are two objects here:

1) Config
contains app configuration. Can not be changed by user.


2) Settings
variables that can be changed by user.
"""

from geometry import Rect
from util import Interval, Color, expScalingFunction
import phylib


class Config:
    """Global app configuration"""

    # Time (in ms) between updates of the GUI
    updateInterval = 75

    # Visible universe
    uniRect = Rect(0, 0, 4e8, 2.8e8)
    # Start and target areas
    startAreaWidth = 2e7
    targetAreaWidth = 2e7

    # Trajectory stuff
    maxTrajectoryLength = uniRect.width()*10
    maxTrajectoryError = uniRect.width()/400
    # Minimal stored segment length
    minPolySegmentLength = uniRect.width()/500
    maxPolySegmentLength = uniRect.width()/20

    # Factors for large / small planets
    fRadiusSmall = 0.66
    fRadiusLarge = 1.5
    fRadiusBlack = 0.5

    fDensitySmall = 1
    fDensityLarge = 1
    fDensityBlack = 500

    planetSize = phylib.earth.radius
    planetDensity = phylib.earth.density
    planetRotation = phylib.earth.angularSpeed
    gravityConstant = phylib.GConst

    # How many in-game seconds pass per second
    timeFactor = 500

    # sets thrust range to [ev*1.3^-5, ev*1.3^5]
    # ev being the escape velocity of a planet
    thrustScale = 2.5

    # range for animation speed scale
    timeScale = 15

    # Gives us a smooth scaling function for positive values
    # Call this function with Config.scaleFunc(value, scale), where
    # scale should be within [-s, s]
    scaleFunc = expScalingFunction(1.3)

    # Number of grid columns / rows for gravity matrix
    gravityGridCols = 100
    gravityGridRows = int(uniRect.hwRatio()*gravityGridCols)

    #
    # GUI
    #

    windowTitle = 'G.r.a.v.i.t.y'

    # Main universe display
    canvasWidth = 1024 # height depends on uniRect ratio
    canvasHeight = int(canvasWidth*uniRect.hwRatio())

    # Zoom window
    zoomWindowWidth = 200
    zoomWindowHeight = int(200*uniRect.hwRatio())
    zoomCircleLineWidth = 3
    zoomArrowShape = (8, 10, 2)
    zoomArrowWidth = 3

    # Width of control sliders
    sliderWidth = 150

    # Box size in pixels
    shipSize = 8

    colors = {
            'canvasBackground': Color(14, 0, 80),
            'zoomWindowBackground': Color(14, 0, 80),
            'zoomOutline': Color(230, 230, 230),

            'shipColor': Color(224, 224, 16),
            'shipOutlineColor': Color(224, 16, 16),

            'launchButton': Color(192, 32, 32),
            'clockBackground': Color(255, 235, 235),
            'ValueLabelBackground': Color(245, 245, 245),

            'startPlanet': Color(16, 200, 200),
            'targetPlanet': Color(16, 220, 48),
            'planet': Color(220, 16, 32),
            'blackPlanet': Color(0, 0, 0),
            'planetOutline': Color(5, 5, 5),
            'blackPlanetOutline': Color(120, 120, 40),
            'planetRotor': Color(100, 100, 100),
            'ship': Color(224, 224, 16),
            'shipOutline': Color(224, 16, 16)
            }


class Settings:
    """User adjustable settings

    Member format:
        .settingName = value
        .settingNameRange = Interval(min, max)
    """

    def set(self, k, v):
        """Only set values for already existing attributes and check range"""

        if not hasattr(self, k):
            raise Exception('No such setting: ' + k)
        interval = getattr(self, k + 'Range')
        if v not in interval:
            raise Exception('Value {v} for {n} out of range ({min}, {max})'.format(
                    v=v, n=k, min=interval.start, max=interval.end))
        setattr(self, k, v)

    def get(self, k):
        return getattr(self, k)

    @property
    def planetRadiusNormal(self):
        return self.planetSize

    @property
    def planetRadiusLarge(self):
        return self.planetSize*Config.fRadiusLarge

    @property
    def planetRadiusSmall(self):
        return self.planetSize*Config.fRadiusSmall

    @property
    def planetRadiusBlack(self):
        return self.planetSize*Config.fRadiusBlack

    @property
    def planetDensityNormal(self):
        return self.planetDensity

    @property
    def planetDensityLarge(self):
        return self.planetDensity*Config.fDensityLarge
    @property
    def planetDensitySmall(self):
        return self.planetDensity*Config.fDensitySmall

    @property
    def planetDensityBlack(self):
        d = self.planetDensity*Config.fDensityBlack
        return Config.scaleFunc(d, self.s_blackDensity)

    @property
    def planetSize(self):
        return Config.scaleFunc(Config.planetSize, self.s_planetSize)

    @property
    def planetDensity(self):
        return Config.scaleFunc(Config.planetDensity, self.s_planetDensity)

    @property
    def planetRotation(self):
        return Config.scaleFunc(Config.planetRotation, self.s_planetRotation)

    @property
    def gravityConstant(self):
        return Config.scaleFunc(Config.gravityConstant, self.s_gravityConstant)

    @property
    def animationSpeed(self):
        return Config.scaleFunc(Config.timeFactor, self.s_animationSpeed)


# For all of these, we will create two attributes:
#   1) Settings.{name}  will be set to the third value
#   2) Settings.{name}Range will be set to an interval [first, second] value.
settingVars = {
        # Scaling values
        's_planetSize': (-5, 5, 0),
        's_planetDensity': (-5, 5, 0),
        's_planetRotation': (-10, 10, 0),
        's_gravityConstant': (-5, 5, 0),
        's_animationSpeed': (-3, 3, 0),
        's_blackDensity': (-5, 5, 0),

        # Absolute values
        'planetSpread': (1, 4, 2),
        'nSmallPlanets': (0, 10, 5),
        'nNormalPlanets': (0, 8, 3),
        'nLargePlanets': (0, 6, 2),
        'nBlackPlanets': (0, 3, 0)
}

for name, defn in settingVars.items():
    setattr(Settings, name, defn[2])
    setattr(Settings, name + 'Range', Interval(defn[0], defn[1]))
