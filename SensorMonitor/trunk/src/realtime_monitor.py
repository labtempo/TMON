#coding: utf-8
'''
Created on Nov 3, 2012

@author: Giulio
'''
import pygame
from pygame.locals import *

GRID_SIZE = 64

# faces
FACE_TOP = 0
FACE_BOTTOM = 1
FACE_FRONT = 2
FACE_BACK = 3
FACE_LEFT = 4
FACE_RIGHT = 5
FACE_TO_STR = {FACE_TOP: "topo", FACE_BOTTOM: "fundo", FACE_FRONT: "frente", FACE_BACK: u"trás", FACE_LEFT: "esquerda", \
               FACE_RIGHT: "direita"}

TRANSPARENT = (255,0,255) # transparent color

'''
@note: 
    x-coordinate is positive going RIGHT
    y-coordinate is positive going FORWARD
    z-coordinate is positive going DOWN
'''

def radial(radius, startcolor, endcolor):
    """
    Draws a linear raidal gradient on a square sized surface and returns
    that surface.
    """
    bigSurf = pygame.Surface((2*radius, 2*radius)).convert_alpha()    
    bigSurf.fill((0,0,0,0))
    dd = -1.0/radius
    sr, sg, sb, sa = endcolor
    er, eg, eb, ea = startcolor
    rm = (er-sr)*dd
    gm = (eg-sg)*dd
    bm = (eb-sb)*dd
    am = (ea-sa)*dd
    
    draw_circle = pygame.draw.circle
    for rad in range(radius, 0, -1):
        draw_circle(bigSurf, (er + int(rm*rad),
                              eg + int(gm*rad),
                              eb + int(bm*rad),
                              ea + int(am*rad)), (radius, radius), rad)
    return bigSurf


def get_temp_color(temp):
    red = max(min( int(180. * (temp + 5.) / 60.) , 255), 0)
    temp_color = (red, 0, 180 - red, 255)
    return temp_color


class Object(object):
    '''
    Represents any object at the datacenter
    '''
    def __init__(self, width, length, height, pos=(0, 0, 0), parent=None, name="obj"):        
        self.width = width
        self.length = length
        self.height = height
        self.sprites = [None] * 6
        self.pos = pos
        self.parent = parent
        self.children = []
        self.name = name
    
    def set_sprite(self, sprite, face):
        '''
        @param face: TOP/BOTTOM, FRONT/BACK, LEFT/RIGHT
        '''
        self.sprites[face] = sprite
        
    def move(self, x, y, z):
        pass
    
    def get_2d_coords(self, view):
        absolute_coords = self.absolute_pos(view)
                
        if view == FACE_TOP or view == FACE_BOTTOM: # x,y        
            return (absolute_coords[0], absolute_coords[1])
        elif view == FACE_FRONT or view == FACE_BACK: # x, z            
            return (absolute_coords[0], absolute_coords[2])
        elif view == FACE_LEFT or view == FACE_RIGHT: # y, z
            return (absolute_coords[1], absolute_coords[2])
            
    def absolute_pos(self, view):
        coords = [self.pos[0], self.pos[1], self.pos[2]]
        
        pobj = self.parent        
        while pobj is not None:
            coords[0] += pobj.pos[0]
            coords[1] += pobj.pos[1]
            coords[2] += pobj.pos[2]
            pobj = pobj.parent
        
        return tuple(coords)
    
    def draw_object(self, obj, view, screen):         
        coords = obj.get_2d_coords(view)
        
        sprite = obj.sprites[view]
        if not sprite:
            if view == FACE_TOP or view == FACE_BOTTOM:
                w = obj.width
                l = obj.length
            elif view == FACE_FRONT or view == FACE_BACK: # x, z                
                w = obj.width
                l = obj.height
            elif view == FACE_LEFT or view == FACE_RIGHT: # y, z
                w = obj.length
                l = obj.height
            
            sprite = FillSprite(w, l)        
        sprite.rect.topleft = (coords[0] * GRID_SIZE, coords[1] * GRID_SIZE)
                
        screen.blit(sprite.image, sprite.rect)
        
        # render font
        if obj.name:
            font = pygame.font.Font(pygame.font.match_font('arial'), 20)        
            black_text = font.render(obj.name, True, (0, 0, 0))
            
            black_textRect = black_text.get_rect()        
            black_textRect.topleft = sprite.rect.topleft
            black_textRect.topleft = (black_textRect.topleft[0] + GRID_SIZE / 8, \
                                      black_textRect.topleft[1] + GRID_SIZE / 8)
            
            font = pygame.font.Font(pygame.font.match_font('arial'), 20)        
            color_text = font.render(obj.name, True, (0, 200, 0))
            
            color_textRect = color_text.get_rect()        
            color_textRect.centerx, color_textRect.centery = \
                black_textRect.centerx - 3, black_textRect.centery - 3
                                             
            screen.blit(black_text, black_textRect)
            screen.blit(color_text, color_textRect)
            
            
    def draw(self, view, screen, objs):
        if view == FACE_FRONT or view == FACE_BACK:
            objs = sorted(objs, key=lambda obj: obj.absolute_pos(view)[1], reverse=(view == FACE_BACK))
        elif view == FACE_TOP or view == FACE_BOTTOM:
            # Z-Coordinate is positive going down
            objs = sorted(objs, key=lambda obj: obj.absolute_pos(view)[2], reverse=(view == FACE_TOP))
        elif view == FACE_LEFT or view == FACE_RIGHT:
            objs = sorted(objs, key=lambda obj: obj.absolute_pos(view)[0], reverse=(view == FACE_LEFT))
        
        for obj in objs:
            self.draw_object(obj, view, screen)
        
        for obj in objs:
            if obj.children:
                self.draw(view, screen, obj.children)


class FillSprite(pygame.sprite.Sprite):
    def __init__(self, width, length, color=(255, 127, 127), texture=None):
        width *= GRID_SIZE
        length *= GRID_SIZE
        self.image = pygame.Surface((width, length))
        self.image.fill(color)
        if texture:
            texture_w, texture_h = texture.get_width(), texture.get_height()
            for x in xrange(0, width, texture_w):
                for y in xrange(0, length, texture_h):
                    self.image.blit(texture, (x, y))                     
        self.rect = self.image.get_rect()
        

class Tile(pygame.sprite.Sprite):    
    def __init__(self, color=(0, 0, 0), image=None):
        # All sprite classes should extend pygame.sprite.Sprite. This
        # gives you several important internal methods that you probably
        # don't need or want to write yourself. Even if you do rewrite
        # the internal methods, you should extend Sprite, so things like
        # isinstance(obj, pygame.sprite.Sprite) return true on it.
        pygame.sprite.Sprite.__init__(self)
      
        if not image:
            image = pygame.Surface((GRID_SIZE, GRID_SIZE))
            image.fill(color)
      
        # Create the image that will be displayed and fill it with the
        # right color.
        self.image = image
        
        # Make our top-left corner the passed-in location.
        self.rect = self.image.get_rect()


class FloorTile(Tile):
    ASSET = pygame.image.load("../assets/floor.jpg")
    def __init__(self):
        Tile.__init__(self, image=self.ASSET)


class WallTile(Tile):
    ASSET = pygame.image.load("../assets/wall.jpg")
    def __init__(self):
        Tile.__init__(self, image=self.ASSET)


class FloorUnit(Object):    
    def __init__(self, pos=(0, 0, 0), parent=None):
        Object.__init__(self, width=1, length=1, height=0, pos=pos, parent=parent, name="")
        sprite = FloorTile()
        self.set_sprite(sprite, FACE_TOP)
        
        self.set_sprite(sprite, FACE_LEFT)
        self.set_sprite(sprite, FACE_FRONT)
        self.set_sprite(sprite, FACE_BACK)
        self.set_sprite(sprite, FACE_TOP)


class WallUnit(Object):
    def __init__(self, pos=(0, 0, 0), parent=None):
        Object.__init__(self, width=1, length=1, height=1, pos=pos, parent=parent, name="")
        sprite = WallTile()
        self.set_sprite(sprite, FACE_RIGHT)
        self.set_sprite(sprite, FACE_LEFT)
        self.set_sprite(sprite, FACE_FRONT)
        self.set_sprite(sprite, FACE_BACK)
        self.set_sprite(sprite, FACE_TOP)


class RackUnit(Object):
    def __init__(self, width=3, length=3, height=10, pos=(0, 0, 0), parent=None, name="Rack"):
        Object.__init__(self, width=width, length=length, height=height, pos=pos, parent=parent,
                        name=name)
        
        color = (120, 120, 120)
        
        top_sprite = FillSprite(width, length, color=color)
        side_sprite = FillSprite(length, height, color=color)
        front_sprite = FillSprite(width, height, color=color)
        
        self.set_sprite(side_sprite, FACE_RIGHT)
        self.set_sprite(side_sprite, FACE_LEFT)
        self.set_sprite(front_sprite, FACE_FRONT)
        self.set_sprite(front_sprite, FACE_BACK)        
        self.set_sprite(top_sprite, FACE_TOP)


class ServerUnit(Object):
    def __init__(self, width=3, length=3, height=1, pos=(0, 0, 0), parent=None, name="Server"):
        Object.__init__(self, width=width, length=length, height=height, pos=pos, parent=parent, \
                        name=name)
        
        server_color = (200, 0, 0)
        
        top_sprite = FillSprite(width, length, color=server_color)
        side_sprite = FillSprite(length, height, color=server_color)
        front_sprite = FillSprite(width, height, color=server_color)
        
        self.set_sprite(side_sprite, FACE_RIGHT)
        self.set_sprite(side_sprite, FACE_LEFT)
        self.set_sprite(front_sprite, FACE_FRONT)
        self.set_sprite(front_sprite, FACE_BACK)        
        self.set_sprite(top_sprite, FACE_TOP)
        

class MoteUnit(Object):
    def __init__(self, width=1, length=1, height=1, pos=(0, 0, 0), parent=None, name="M"):
        Object.__init__(self, width=width, length=length, height=height, pos=pos, parent=parent, \
                        name=name)
        
        self.temperature = 20.0 # degrees
        
        sprite = FillSprite(width, length, color=(0, 0, 200))
                
        self.set_sprite(sprite, FACE_RIGHT)
        self.set_sprite(sprite, FACE_LEFT)
        self.set_sprite(sprite, FACE_FRONT)
        self.set_sprite(sprite, FACE_BACK)        
        self.set_sprite(sprite, FACE_TOP)


class Room(Object):
    ASSET_WALL = pygame.image.load("../assets/wall.jpg")
    ASSET_FLOOR = pygame.image.load("../assets/floor.jpg")
    def __init__(self, width, length, height, pos, parent):
        Object.__init__(self, width=width, length=length, height=height, pos=pos, parent=parent, \
                        name="Room")
        
        # setup wall
        wall_front_back = FillSprite(width, height, texture=self.ASSET_WALL)
        wall_left_right = FillSprite(length, height, texture=self.ASSET_WALL)        
        self.set_sprite(wall_front_back, FACE_FRONT)
        self.set_sprite(wall_front_back, FACE_BACK)
        self.set_sprite(wall_left_right, FACE_LEFT)
        self.set_sprite(wall_left_right, FACE_RIGHT)   
        
        # setup floor
        floor_sprite = FillSprite(width, length, texture=self.ASSET_FLOOR)        
        self.set_sprite(floor_sprite, FACE_TOP)
        
        self.motes = []
       
    
    def draw_temperature_layer(self, screen, view, offset):
        alpha = 100
        room_coords = self.get_2d_coords(view)
        room_rect = pygame.Rect(room_coords[0] * GRID_SIZE, room_coords[1] * GRID_SIZE, \
                                (room_coords[0] + self.width) * GRID_SIZE, \
                                (room_coords[1] + self.height) * GRID_SIZE)
        
        curr_screen_clip = screen.get_clip()
        screen.set_clip(room_rect)
        
        motes = self.motes[:]
        filter_func = None
        if view == FACE_TOP:
            filter_func = lambda m: m.absolute_pos(view)[2] > offset
        elif view == FACE_BOTTOM: 
            filter_func = lambda m: m.absolute_pos(view)[2] < offset
        elif view == FACE_FRONT:
            filter_func = lambda m: m.absolute_pos(view)[1] > offset
        elif view == FACE_BACK:
            filter_func = lambda m: m.absolute_pos(view)[1] < offset
        elif view == FACE_RIGHT:
            filter_func = lambda m: m.absolute_pos(view)[0] > offset
        elif view == FACE_LEFT:
            filter_func = lambda m: m.absolute_pos(view)[0] < offset
        motes = filter(filter_func, motes)
        
        for mote in motes:
            center_color = get_temp_color(mote.temperature)
            border_color = get_temp_color(mote.temperature - 10)
            
            coords = mote.get_2d_coords(view)
            coords = (coords[0]  * GRID_SIZE, coords[1] * GRID_SIZE)
            
            radius = 3
            surface_dim = (2 * radius + 1, 2 * radius + 1)
            
            temp_surface = pygame.Surface((surface_dim[0] * GRID_SIZE, surface_dim[1] * GRID_SIZE))            
            temp_surface.fill(TRANSPARENT)
            temp_surface.set_colorkey(TRANSPARENT)                 
            temp_surface.set_alpha(alpha)
            rect = temp_surface.get_rect()
            rect.topleft = (coords[0] - radius * GRID_SIZE, coords[1] - radius * GRID_SIZE)            
            
            radial_surface = radial(radius * GRID_SIZE + GRID_SIZE / 2, center_color, border_color)            
            temp_surface.blit(radial_surface, (0, 0))
                        
            screen.blit(temp_surface, rect)
            
        
        screen.set_clip(curr_screen_clip)


class World(Object):
    def __init__(self, width, length, height):
        '''
        @param size: size in Tile units
        '''
        Object.__init__(self, width, length, height)
        self.dimensions = (width * GRID_SIZE, length * GRID_SIZE, height * GRID_SIZE)        
        self.screen = pygame.display.set_mode((self.dimensions[0], self.dimensions[1])) # set screen size
        self.offset = 0
        self.room = None
        self.name = ""
        
    def create(self, view):
        self.draw(view, self.screen, self.children)
        
        if self.room:
            self.room.draw_temperature_layer(self.screen, view, self.offset)
        
        font = pygame.font.Font(pygame.font.match_font('Verdana'), 40)        
        text = font.render(u'Visão: %s / Nível: %d' % (FACE_TO_STR[view], self.offset), True, \
                           (255, 255, 255))
        
        textRect = text.get_rect()        
        textRect.centerx = self.screen.get_rect().centerx
        textRect.centery = GRID_SIZE
        self.screen.blit(text, textRect)


class WorldCreator(object):
    '''
    Creates a world from a given model
    '''
    def __init__(self, room):
        self.model = room
    
    def create(self):
        width, length, height  = 22, 16, 20        
        world = World(width, length, height)
                
        room = Room(width - 4, length - 4, height - 4, pos=(2, 2, 2), parent=world)
        
        # RACK 1
        rack1 = RackUnit(pos=(2, 2, (height - 4) - 10), parent=room, name="Rack 1")
        server1 = ServerUnit(pos=(0, 0, 5), parent=rack1, name="Server 1.1")
        server2 = ServerUnit(pos=(0, 0, 3), parent=rack1, name="Server 1.2")
        mote1 = MoteUnit(pos=(1, 2, 0), parent=server1, name="M001")
        mote2 = MoteUnit(pos=(1, 0, 0), parent=server2, name="M002")
        
        # RACK 2
        rack2 = RackUnit(pos=(8, 2, (height - 4) - 10), parent=room, name="Rack 2")
        server11 = ServerUnit(pos=(0, 0, 5), parent=rack2, name="Server 2.1")
        server22 = ServerUnit(pos=(0, 0, 3), parent=rack2, name="Server 2.2")
        mote3 = MoteUnit(pos=(1, 2, 0), parent=server11, name="M003")
        mote4 = MoteUnit(pos=(1, 0, 0), parent=server22, name="M004")
        
        # RACK 3
        rack3 = RackUnit(pos=(14, 1, (height - 4) - 10), width=2, length=4, parent=room, name="Rack 3")
        
        # RACK 4
        rack4 = RackUnit(pos=(14, 7, (height - 4) - 10), width=2, length=4, parent=room, name="Rack 4")
        
        room.children = [rack1, server1, server2, mote1, mote2, rack2, server11, server22, mote3, mote4, \
                         rack3, rack4]
        room.motes = [mote1, mote2, mote3, mote4]
        world.children = [room]
        world.room = room
        world.offset = 0
        
        # set temperatures
        mote1.temperature = 25.
        mote2.temperature = 30.
        mote3.temperature = 27.
        mote4.temperature = 40.
        
        return world
    

def main():
    pygame.init()
    
    world_creator = WorldCreator(None)
    world = world_creator.create()
    
    view = FACE_FRONT
    world.create(view)
    pygame.image.save(world.screen, "screenshot.png")
    
    #pygame.display.update()
    #while pygame.event.poll().type != QUIT: pygame.time.delay(10)

if __name__ == '__main__':
    main()