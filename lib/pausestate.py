from lib2d.gamestate import GameState
from lib2d.vec import Vec2d
from lib2d.tilemap import BigMap, View
from lib2d.world import World
from renderer import Camera
import lib2d.sheetloader

from lib2d import gfx

guy = lib2d.sheetloader.load_actor("Hero")


class PauseState(GameState):
    """
    This is for when the game is paused while the player is in the
    world state.
    """

    def __init__(self, driver, worldmap):
        GameState.__init__(self, driver)

    def activate(self):
        pass

    # when focus is given again
    def reactivate(self):
        pass

    # when losing focus
    def deactivate(self):
        pass

    def draw(self, surface):
        self.world.draw(surface)

    # time is ms since last call
    def update(self, time):

    def handle_event(self, event):
        self.world.handle(event)

