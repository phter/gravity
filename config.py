#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu May 16 22:39:54 2019

@author: philipp
"""

from geometry import Rect
import util

class Config:
    def update(self, k, v):
        if hasattr(self, k):
            setattr(self, k, v)
        else:
            raise KeyError('No such config key: ' + k)

# ------------------------------------------------------------------------
# GUI configuration
# ------------------------------------------------------------------------
c = guiConfig = Config()

c.windowTitle = 'G.r.a.v.i.t.y'
c.canvasWidth = 1024 # height depends on uniRect ratio
c.canvasColor = '#100080'

# Planet colors
# the missing value in these templates depends on rotation speed
c.bodyColors = {
        'start': '#10{val}{val}',
        'target': '#10{val}30',
        'planet': '#{val}1020',
        'outline': '#{val}{val}{val}'
        }


# ------------------------------------------------------------------------
# Game configuration
# ------------------------------------------------------------------------
class GameConfig(Config):
    def planetSizeNormal(self): return self.planetSize
    def planetSizeLarge(self): return self.planetSize*1.5
    def planetSizeSmall(self): return self.planetSize*0.66
    
    def planetDensityNormal(self): return self.planetDensity
    def planetDensityLarge(self): return self.planetDensity
    def planetDensitySmall(self): return self.planetDensity
    
    
c = gameConfig = GameConfig()

c.rotationRange = util.Intervall(0.4, 1.0) # has to be within [0, 1]
c.minPlanetDistance = 2  # will be multiplied with sum of radii

c.planetSize = 70
c.planetRotation = 1
c.planetDensity = 1

# Visible universe
c.uniRect = Rect(0, 0, 2000, 1400)
# Start and target areas
c.startAreaWidth = 200
c.targetAreaWidth = 200

# Number of Planets
c.nSmallP = 5
c.nNormalP = 3
c.nLargeP = 2

# Start planet config
c.radiusStartP = 1
c.rotationStartP = 1



