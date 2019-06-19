"""Gravity - a simple space game

The purpose of this game is to build intuition for gravitational forces in a fun way.

The objective of the game is to manoeuvre a ship from one planet to another,
using gravitational forces of planets inbetween.

The following simplifications have been made:

   * The game universe is two-dimensional

   * Distances between planets are vastly reduced.

   * Planets have no atmosphere

   * Ships are launched vertically.
     Once launched, they can not be further controlled.

   * Ships are launched with infinite acceleration, ie. the user can determine
     the initial thrust and the ship will reach its maximum speed instantly.

   * Ships land with infinite (negative) acceleration, ie. we are not concerned
     with "soft" landings (assuming fantastic airbag technology :)

"""

from gui import App
from config import Settings

app = App(Settings())
app.run()
