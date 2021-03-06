"""
Example GameState for a top-down adventure game.
This is the client portion of the game.
"""

from renderer import AreaCamera
from rpg import GRAB, LIFT

from lib2d.client.gamestate import GameState
from lib2d.client.statedriver import driver as sd
from lib2d.client.buttons import *
from lib2d.client import gui
from lib2d.common.vec import Vec2d
from lib2d.common import res
from pytmx import tmxloader

import math, pygame

debug = 1
movt_fix = 1/math.sqrt(2)


class SoundManager(object):
    def __init__(self):
        self.sounds = {}
        self.last_played = {}

    def loadSound(self, filename):
        self.sounds[filename] = res.loadSound(filename)
        self.last_played[filename] = 0

    def play(self, filename, volume=1.0):
        now = time.time()
        if self.last_played[filename] + .05 <= now:
            self.last_played[filename] = now
            sound = self.sounds[filename]
            sound.set_volume(volume)
            sound.play()

    def unload(self):
        self.sounds = {}
        self.last_played = {}

SoundMan = SoundManager()
    

class WorldStateController(object):
    """
    Controller to manipulate the world
    """

    def __init__(self, view, model):
        self.view = view
        self.model = model


    def process(self, cmdlist):
        """
        supply a list of game events
        """

        x = 0
        y = 0

        for cls, cmd, arg in cmdlist:
            if arg == BUTTONUP:
                if cmd == P1_UP:
                    self.player_vector.x = 0
                elif cmd == P1_DOWN:
                    self.player_vector.x = 0
                elif cmd == P1_LEFT:
                    self.player_vector.y = 0
                elif cmd == P1_RIGHT:
                    self.player_vector.y = 0
                elif cmd == P1_ACTION2:
                    self.hero.ungrab()
                elif cmd == P1_ACTION3:
                    self.hero.unlift()

            # these actions will repeat as button is held down
            elif arg == BUTTONDOWN or arg == BUTTONHELD:
                if   cmd == P1_UP:      x = -1
                elif cmd == P1_DOWN:    x = 1
                elif cmd == P1_LEFT:    y = -1
                elif cmd == P1_RIGHT:   y = 1

            # these actions will not repeat if button is held
            if arg == BUTTONDOWN:
                if cmd == P1_ACTION1:
                    self.hero.attack()

                elif cmd == P1_ACTION2:
                    self.hero.grab()

                elif cmd == P1_ACTION3:
                    self.hero.lift()


        if (not x == 0) and (not y == 0):
            x *= movt_fix
            y *= movt_fix

        if (not x == 0) or (not y == 0):
            self.player_vector.y = y * self.hero.move_speed
            self.player_vector.x = x * self.hero.move_speed

            # don't rotate the player if he's grabbing something
            if not self.hero.arms == GRAB:
                self.area.setOrientation(self.hero, math.atan2(x, y))

        

class WorldState(GameState):
    """
    This state is where the player will move the hero around the map
    interacting with npcs, other players, objects, etc.

    i would really like the game to be sandboxable...set traps,
    make contraptions, etc

    controls:
        picking up objects will affect what your buttons do
        equipted items always have a dedicated button
        should have hot-swap button and drop button

    This is a VIEW in mvc.

    """

    def __init__(self, area, startPosition=None):
        GameState.__init__(self)
        self.area = area


    def activate(self):
        self.blank = True
        self.background = (203, 204, 177)
        self.foreground = (0, 0, 0)

        self.controller = WorldStateController(self, self.area)

        self.msgFont = pygame.font.Font((res.fontPath("volter.ttf")), 9)
        self.border = gui.GraphicBox("dialog2-h.png", hollow=True)
        self.borderFilled = gui.GraphicBox("dialog2.png")
        self.player_vector = Vec2d(0,0)

        # load the pygame and data assests for the area
        self.area.load()

        # get the root and the hero from it
        root = self.area.getRoot()
        self.hero = root.getChildByGUID(1)
        self.hero.move_speed = 1

        # add the hero to this map if it isn't already there
        if not self.area.hasChild(self.hero):
            self.area.add(self.hero)

        # attach a camera
        sw, sh = sd.get_size()
        mw = sw * .75
        mh = sh * .75
        self.camera = AreaCamera(self.area,(4,4, mw, mh),
                                 tmxdata=self.area.tmxdata)

        # define the borders
        self.mapBorder = pygame.Rect((0,0,mw+6,mh+6))
        self.msgBorder = pygame.Rect((0,mh,sw,sh-mh))
        self.hudBorder = pygame.Rect((mw,0,sw-mw,mh+6))

        # load sounds from area
        for filename in self.area.soundFiles:
            SoundMan.loadSound(filename)


    def deactivate(self):
        res.fadeoutMusic(1000)

        # unload the children
        for child in self.area.getChildren():
            child.unload()

        self.area.music_pos = float(pygame.mixer.music.get_pos()) / 1000
        SoundMan.unload()   

 
    def reactivate(self):
        # play music if any has been set in tiled
        try:
            pygame.mixer.music.stop()
            res.playMusic(self.area.tmxdata.music, start=self.area.music_pos)
        except AttributeError:
            res.fadeoutMusic()
            self.music_playing = False 
        else:
            self.music_playing = True   

       
    def _drawSidebar(self, surface, rect):
        # draw the static portions of the sidebar
        sx, sy, sw, sh = rect

        self.border.draw(surface, self.hudBorder)
        titleFont = pygame.font.Font(res.fontPath("northwoodhigh.ttf"), 20)
        i = titleFont.render("MH", 1, (128,128,128))
        surface.blit(i, (sw/2+sx-i.get_size()[0]/2+1, sy+3))
        i = titleFont.render("MH", 1, self.foreground)
        surface.blit(i, (sw/2+sx-i.get_size()[0]/2, sy+2))

        headFont = pygame.font.Font(res.fontPath("red_mamba.ttf"), 6)

        i = headFont.render("Left Hand", 1, self.foreground, self.background)
        surface.blit(i, (sx+ 10, sy+30))


    def draw(self, surface):
        sx, sy = surface.get_size()

        if self.blank:
            self.blank = False
            surface.fill(self.background)
            self._drawSidebar(surface, self.hudBorder)
            self.camera.center(self.area.getPosition(self.hero))

        # the main map
        self.camera.draw(surface)

        # borders
        self.borderFilled.draw(surface, self.msgBorder)
        self.border.draw(surface, self.mapBorder)

        log = "\n".join(self.area.messages[-5:])
        rect = self.msgBorder.inflate(-16,-12)
        gui.drawText(surface, log, (0,0,0), rect, self.msgFont)

        return

        originalClip = surface.get_clip()
        surface.set_clip(self.camera.rect)

        # debug stuff...may/may not work
        for obj, pos in self.area.getPositions():
            x,y,w,h = self.area.toRect(self.area.getBBox(obj))
            ox, oy = self.camera.rect.topleft
            surface.fill((128,0,64), (self.camera.toScreen((x+ox,y+oy)), (w,h)))

        for gid, param in self.area.exits.items():
            x, y, l = param[0]
            size = (16, 16)
            ox, oy = self.camera.rect.topleft
            pygame.draw.rect(surface,(128,128,255),
                            (self.camera.toScreen((x+ox,y+oy)),size))

        for rect in self.area.geoRect:
            x, y, sx, sy = rect
            ox, oy = self.camera.rect.topleft
            pygame.draw.rect(surface,
                     (255,0,128, 20),
                     (self.camera.toScreen((x+ox, y+oy)), (sy, sx)))
    
        surface.set_clip(originalClip)


    def update(self, time):
        self.area.update(time)
        self.camera.update(time)

        x, y = self.player_vector

        if x==y==0:
            if self.hero.avatar.isPlaying("walk"):
                self.hero.avatar.play("stand")
        else:
            self.area.movePosition(self.hero, (x, y, 0), True, caller=self)


    def handle_commandlist(self, cmdlist):
        self.controller.process(cmdlist)



