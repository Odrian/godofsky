import os
from sys import exit

import pygame
from pygame.transform import scale


def load_image(path, color_key=None):
    path = os.path.join("media", path)
    if not os.path.isfile(path):
        raise FileExistsError("file not found: " + path)
    image = pygame.image.load(path)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


class Group:
    def __init__(self):
        self.sprites = []

    def add(self, sprite):
        if not isinstance(sprite, ImageSprite):
            raise Exception("not sprite: " + sprite)
        self.sprites.append(sprite)

    def update(self):
        for sprite in self.sprites:
            sprite.update()

    def draw(self):
        for sprite in self.sprites:
            rect = sprite.rect.copy()
            rect.x -= camera_x - (width - player_size[0]) / 2
            rect.y -= camera_y - (height - player_size[1]) / 2
            rect.y = height - rect.y - sprite.static_height
            screen.blit(sprite.image, rect)

    def collide(self, rect):
        collide_func = rect.colliderect
        for sprite2 in self.sprites:
            if collide_func(sprite2.rect):
                return True
        return False

    def smart_collide(self, rect):
        collide = 0b0000  # 8-up 4-down 2-right 1-left
        for sprite in self.sprites:
            collide |= self._smart_rect_collide(rect, sprite.rect)
        return collide

    def _smart_rect_collide(self, r1, r2):
        x11, y11 = r1.topleft
        w1, h1 = r1.size
        x12, y12 = x11 + w1, y11 + h1

        x21, y21 = r2.topleft
        w2, h2 = r2.size
        x22, y22 = x21 + w2, y21 + h2

        collide_x = x11 <= x22 and x12 >= x21
        collide_y = y11 <= y22 and y12 >= y21
        if not (collide_x and collide_y):
            return 0

        some_collide_x = min(abs(x12 - x21), abs(x11 - x22)) < max_collide_pixels
        some_collide_y = min(abs(y12 - y21), abs(y11 - y22)) < max_collide_pixels

        collision = 0
        if collide_x and not some_collide_y:
            if x11 >= x21 + w2 / 2:
                collision |= COLLIDE_LEFT
            else:
                collision |= COLLIDE_RIGHT
        if collide_y and not some_collide_x:
            if y11 >= y21 + h2 / 2:
                collision |= COLLIDE_DOWN
            else:
                collision |= COLLIDE_UP
        return collision


class ImageSprite(pygame.sprite.Sprite):
    def __init__(self, image):
        super().__init__()
        group_all.add(self)
        self.image = image
        self.rect = image.get_rect()
        self.static_height = self.rect.height

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def set_rect(self, wh):
        w, h = wh
        self.rect.w = w
        self.rect.h = h

    def update_animation(self):
        pass


class SimpleAnimSprite(ImageSprite):
    def __init__(self, images, rects=None):
        super().__init__(images[0])
        self.anims_rects = None
        if isinstance(rects, tuple):
            self.anims_rects = None
            self.set_rect(rects)
        elif isinstance(rects, list):
            self.anims_rects = rects
            self.set_rect(rects[0])

        self.anims = images
        self.anim_wait = 0.5
        self.reverse_wait = 2

        self.anim_i = 0
        self.anim_wait_i = 0
        self.reverse = 1
        self.reverse_wait_i = 0

    def update(self):
        if self.reverse_wait_i != 0:
            self.reverse_wait_i = max(0.0, self.reverse_wait_i - dt)
            return
        if self.reverse_wait_i == 0:
            self.anim_wait_i += dt
            if self.anim_wait_i >= self.anim_wait:
                self.anim_wait_i -= self.anim_wait
                self.next_anim()

    def next_anim(self):
        if self.reverse == 0:
            self.anim_i += 1
            self.anim_i %= len(self.anims)
        elif self.reverse == 1:
            self.anim_i += 1
            if self.anim_i == len(self.anims):
                self.reverse_wait_i = self.reverse_wait
                self.anim_i -= 1
                self.reverse = 2
        else:
            self.anim_i -= 1
            if self.anim_i == 0:
                self.reverse_wait_i = self.reverse_wait
                self.reverse = 1
        self.image = self.anims[self.anim_i]
        if self.anims_rects is not None:
            self.set_rect(self.anims_rects[self.anim_i])


class ButtonSprite(ImageSprite):
    def __init__(self, code, image):
        super().__init__(image)
        self.code = code


class PlayerSprite(ImageSprite):
    def __init__(self):
        super().__init__(scale(load_image("player.png"), player_size))
        self.x = self.rect.x
        self.y = self.rect.y
        self.vx = 0
        self.vy = 0
        self.jumps = 1
        self.jump_timeout = 0

    def update(self):
        # timeout
        if self.jump_timeout != 0:
            self.jump_timeout = max(0.0, self.jump_timeout - dt)

        # check pressed keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT]:
            self.vx = min(max_move, self.vx + move_force * dt)
        if keys[pygame.K_LEFT]:
            self.vx = max(-max_move, self.vx - move_force * dt)

        # resist
        if not (keys[pygame.K_RIGHT] or keys[pygame.K_LEFT]):
            if self.vx > 0:
                self.vx = max(0.0, self.vx - move_force * dt)
            else:
                self.vx = min(0.0, self.vx + move_force * dt)

        self.move()

        if group_spikes.collide(self.rect):
            self.set_pos(*player_start_pos)

    def move(self):
        collide = group_walls.smart_collide(self.rect)
        if collide & COLLIDE_UP:
            if self.vy > 0:
                self.vy = 0
        if collide & COLLIDE_DOWN:
            self.jumps = 1
            if self.vy < 0:
                self.vy = 0
        else:
            self.vy += gravity * dt
            self.jumps = 0
        if collide & COLLIDE_RIGHT:
            if self.vx > 0:
                self.vx = 0
        if collide & COLLIDE_LEFT:
            if self.vx < 0:
                self.vx = 0
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.x = self.x
        self.rect.y = self.y

    def jump(self):
        if self.jumps > 0 and self.jump_timeout == 0:
            self.jump_timeout = jump_timeout
            self.jumps -= 1
            self.vy = jump_force

    def set_pos(self, x, y):
        self.x = x
        self.y = y


class SpikeSprite(SimpleAnimSprite):
    def __init__(self):
        super().__init__(spike_anims, spike_sizes)
        group_spikes.add(self)


class WallSprite(ImageSprite):
    def __init__(self, *size):
        super().__init__(scale(create_rectangle(), size))
        group_walls.add(self)


class StartScene:
    def __init__(self):
        self.group_all = Group()
        self.group_buttons = Group()

    def tick(self):
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for button in self.group_buttons.sprites:
                    if button.rect.collidepoint(x, y):
                        self.button_click(button.code)
                        break

        group_all.update()

        screen.fill((100,) * 3)
        group_all.draw()
        pygame.display.flip()

    def button_click(self, code):
        pass


class GameScene:
    def __init__(self):
        self.fps_i = 0

    def tick(self):
        clock.tick(fps * fps_tick)

        self.events()

        group_all.update()
        camera_move()

        self.fps_i = (self.fps_i + 1) % fps_tick
        if self.fps_i == 0:
            screen.fill((100,) * 3)
            group_all.draw()
            pygame.display.flip()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key in [pygame.K_SPACE]:
                    player.jump()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    x, y = event.pos
                    player.x += x - width / 2
                    player.y -= y - height / 2


def create_rectangle(color=(0,) * 3):
    image = pygame.Surface((1, 1))
    image.fill(color)
    return image


def camera_move():
    global camera_x, camera_y
    dx = player.x - camera_x
    dy = player.y - camera_y
    k = 30
    camera_x += dx / k
    camera_y += dy / k


def terminate():
    pygame.quit()
    exit()


# --------------------------------------------- #
# init pygame

pygame.init()
pygame.display.set_caption("God of Sky")

size = width, height = 1400, 700
screen = pygame.display.set_mode(size, pygame.RESIZABLE)
clock = pygame.time.Clock()

# --------------------------------------------- #
# init special consts

COLLIDE_UP = 8
COLLIDE_DOWN = 4
COLLIDE_RIGHT = 2
COLLIDE_LEFT = 1

# --------------------------------------------- #
# init consts

max_collide_pixels = 5

fps = 60
fps_tick = 3
dt = round(1 / fps / fps_tick, 3)

gravity = -981

jump_force = 400.0
jump_timeout = 0.2

max_move = 200.0
move_force = max_move * 12

# --------------------------------------------- #
# init sprites values

group_all = Group()
group_walls = Group()
group_spikes = Group()

tile_w = 32
tile_s = (tile_w, ) * 2

spikes_i = 4
spike_sizes = [
    (tile_w, tile_w / 16 * 13),
    (tile_w, tile_w / 16 * 10),
    (tile_w, tile_w / 16 * 6),
    (tile_w, tile_w / 16 * 0),
]
spike_anims = [scale(load_image(f"spikes/spike_{i}.png"), tile_s) for i in range(spikes_i)]

# --------------------------------------------- #
# init sprites

player_size = (30, 60)
player_start_pos = (0, 100)
player = PlayerSprite()
player.set_pos(*player_start_pos)

camera_x, camera_y = player_start_pos

wall1 = WallSprite(1000, 20)
wall1.set_pos(-500, 0)

wall2 = WallSprite(20, 100)
wall2.set_pos(100, 100)

spike = SpikeSprite()
spike.set_pos(-100, 0)

# --------------------------------------------- #
# main loop

scene = GameScene()
while True:
    scene.tick()
