import os
from sys import exit

from numpy import sign
from pygame.transform import scale

from file_import import *


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


def approach(value, mx, step):
    if abs(value - mx) <= step:
        return mx
    if value > mx:
        return value - step
    else:
        return value + step


class Group:
    def __init__(self):
        self.sprites = []

    def __iter__(self): return self.sprites.__iter__()

    def clear(self): self.sprites = []

    def add(self, sprite): self.sprites.append(sprite)

    def add_all(self, sprites):
        for sprite in sprites:
            self.add(sprite)

    def remove(self, sprite): self.sprites.remove(sprite)

    def update(self):
        for sprite in self:
            sprite.update()

    def draw(self):
        for sprite in self:
            rect = sprite.rect.copy()
            rect.x -= camera_x
            rect.y -= camera_y
            rect.y = height - rect.y - sprite.static_height
            screen.blit(sprite.image, rect)

    def collide(self, rect):
        collide_func = rect.colliderect
        for sprite2 in self:
            if collide_func(sprite2.rect):
                return True
        return False

    def smart_collide(self, rect):
        collide = 0b0000  # 8-up 4-down 2-right 1-left
        for sprite in self:
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
        if not y11 + h1 * 2 / 3 > y22:
            collision |= COLLIDE_HOOK_UP
        if not y11 + h1 / 3 < y21:
            collision |= COLLIDE_HOOK_DOWN
        return collision


# --------------------------------------------- #
# main sprites classes

class ImageSprite(pygame.sprite.Sprite):
    def __init__(self, scene, image):
        super().__init__()
        scene.group_all.add(self)
        self.scene = scene
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


class MovableSprite(ImageSprite):
    def __init__(self, scene, image):
        super().__init__(scene, image)
        self.x = self.rect.x
        self.y = self.rect.y
        self.vx = 0
        self.vy = 0

    def move(self):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rect.x = self.x
        self.rect.y = self.y

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y


class SimpleAnimSprite(ImageSprite):
    def __init__(self, scene, images, rects=None):
        super().__init__(scene, images[0])
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
        if self.reverse_wait_i > 0:
            self.reverse_wait_i -= dt
            return
        if self.reverse_wait_i <= 0:
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


class TriggerSprite(ImageSprite):
    def __init__(self, scene, size):
        void_image = pygame.Surface(size)
        void_image.fill((0, 0, 0, 0))
        super().__init__(scene, void_image)
        self.scene.group_ivisibles.add(self)

    def triggered(self):
        pass


# --------------------------------------------- #
# not main sprite classes

class ButtonSprite(ImageSprite):
    def __init__(self, scene, code, image):
        super().__init__(scene, image)
        scene.group_buttons.add(self)
        self.code = code


class PlayerSprite(MovableSprite):
    def __init__(self, scene):
        super().__init__(scene, scale(load_image("player.png"), player_size))
        self.group_connected_coins = Group()
        self.keys = {}
        self.collisions = 0

        self.jump_can = True
        self.jump_pressed_w = 0
        self.jump_ground_w = 0
        self.jump_mercy = 0

        self.hooked = False
        self.hook_right = True

        self.can_dash = True
        self.dash_w = 0

    def update(self):
        self.collisions = self.scene.group_walls.smart_collide(self.rect)
        self.keys = pygame.key.get_pressed()

        # waiting
        if self.jump_ground_w > 0:
            self.jump_ground_w = approach(self.jump_ground_w, 0, dt)
        if self.jump_pressed_w > 0:
            self.jump_pressed_w = approach(self.jump_pressed_w, 0, dt)
        if self.dash_w > 0:
            self.dash_w = approach(self.dash_w, 0, dt)
            if not self.dash_w > 0:
                self.vy = dash_end_y_force * sign(self.vy)

        # check pressed keys
        if self.keys[KEY_JUMP] and self.jump_pressed_w > 0:
            self.vy += jump_pressed_force * dt
        else:
            self.jump_pressed_w = 0

        # mercy
        if self.jump_mercy > 0:
            if self.jump():
                self.jump_mercy = 0
            else:
                self.jump_mercy = approach(self.jump_mercy, 0, dt)

        self.check_hook()
        if not self.hooked and self.dash_w <= 0:
            # gravity
            if not self.collisions & COLLIDE_DOWN:
                self.vy -= gravity * dt
                if self.vy < -max_gravity:
                    self.vy = -max_gravity
                self.jump_can = False

        self.move_x()

        self.check_move()
        self.move()

        # collect coins
        if self.collisions & COLLIDE_DOWN:
            for coin in self.group_connected_coins:
                coin.collected()
            self.group_connected_coins.clear()

        # spikes
        if self.scene.group_spikes.collide(self.rect):
            self.set_pos(*self.scene.player_start_pos)
            for coin in self.scene.group_coins:
                coin.player_connect = False

    def collision_all(self, *collides):
        for collide in collides:
            if not self.collisions & collide:
                return False
        return True

    def move_x(self):
        if self.hooked or self.dash_w > 0:
            return

        mult = 1 if self.collisions & COLLIDE_DOWN else friction_air

        key_x = 0
        if self.keys[KEY_RIGHT]:
            key_x = 1
        elif self.keys[KEY_LEFT]:
            key_x = -1

        if abs(self.vx) > max_move and sign(self.vx) == key_x:
            # slowdown
            self.vx = approach(self.vx, max_move * key_x, friction_reduce * mult * dt)
        else:
            # acceleration
            self.vx = approach(self.vx, max_move * key_x, friction_accel * mult * dt)

    def dash(self):
        if not self.can_dash:
            return
        xd, yd, xf, yf = 0, 0, 0, 0

        if self.keys[KEY_UP]:
            yd = 1
        elif self.keys[KEY_DOWN]:
            yd = -1

        if self.keys[KEY_RIGHT]:
            xd = 1
        elif self.keys[KEY_LEFT]:
            xd = -1

        if xd == yd == 0:
            return

        if xd == 0:
            yf = dash_force
        elif yd == 0:
            xf = dash_force
        else:
            xf, yf = (dash_force / 1.4, ) * 2

        self.dash_w = dash_w
        self.vx, self.vy = xf * xd, yf * yd
        self.can_dash = False

    def check_hook(self):
        # check if you out of available space
        if self.hooked:
            if self.hook_right:
                if not self.collisions & COLLIDE_RIGHT:
                    self.hooked = False
            else:
                if not self.collisions & COLLIDE_LEFT:
                    self.hooked = False
            if not self.collision_all(COLLIDE_HOOK_DOWN, COLLIDE_HOOK_UP):
                self.hooked = False
                if not self.vy < 0:
                    self.vy = 260

        if self.keys[KEY_HOOK] != self.hooked:
            if self.hooked:
                # if you up hook key
                self.hooked = False
            else:
                # if you try to hook
                if self.collisions & (COLLIDE_LEFT | COLLIDE_RIGHT):
                    if self.collision_all(COLLIDE_HOOK_DOWN, COLLIDE_HOOK_UP):
                        self.hooked = True
                        self.vy = 0
                        self.hook_right = self.collisions & COLLIDE_RIGHT

        # y move
        if self.hooked:
            if self.keys[KEY_UP]:
                self.vy = hook_move_force
            elif self.keys[KEY_DOWN]:
                self.vy = -hook_move_force
            else:
                self.vy = 0

    def check_move(self):
        if self.collisions & COLLIDE_UP:
            if self.vy > 0:
                self.vy = 0
        if self.collisions & COLLIDE_DOWN:
            self.jump_can = True
            self.can_dash = True
            if self.vy < 0:
                self.vy = 0
                self.jump_ground_w = jump_ground_w
        if self.collisions & COLLIDE_RIGHT:
            if self.vx > 0:
                self.vx = 0
        if self.collisions & COLLIDE_LEFT:
            if self.vx < 0:
                self.vx = 0

    def jump(self):
        if self.jump_can:
            if self.jump_ground_w == 0:
                self.jump_can = False
                self.jump_pressed_w = jump_pressed_w
                self.vy = jump_force
                return True
        elif self.collisions & (COLLIDE_RIGHT | COLLIDE_LEFT):
            self.hooked = False
            xd = 1 if self.collisions & COLLIDE_LEFT else -1
            self.vx = wall_jump_x * xd
            self.vy = wall_jump_y
        else:
            if self.jump_mercy == 0:
                self.jump_mercy = jump_mercy
        return False


class CoinSprite(MovableSprite):
    def __init__(self, scene, pos):
        super().__init__(scene, coin_image)
        self.set_pos(*pos)
        self.position = pos
        self.scene.group_coins.add(self)
        self.player_connect = False

        self.min_dist = 30
        self.k = 2

    def update(self):
        if self.player_connect:
            dx = self.scene.player.x - self.x
            self.vx = dx * self.k if abs(dx) > self.min_dist else 0

            dy = self.scene.player.y - self.y
            self.vy = dy * self.k

            self.move()
        else:
            self.set_pos(*self.position)
            if self.scene.player.rect.colliderect(self.rect):
                self.player_connect = True
                self.scene.player.group_connected_coins.add(self)

    def collected(self):
        self.scene.group_coins.remove(self)
        self.scene.group_all.remove(self)
        pass  # save that was collected


class SpikeSprite(SimpleAnimSprite):
    def __init__(self, scene, pos):
        super().__init__(scene, spike_anims, spike_sizes)
        self.set_pos(*pos)
        scene.group_spikes.add(self)


class WallSprite(ImageSprite):
    def __init__(self, scene, size, pos):
        rect = pygame.Surface((1, 1))
        rect.fill((0,) * 3)
        super().__init__(scene, scale(rect, size))
        self.set_pos(*pos)
        scene.group_walls.add(self)


# --------------------------------------------- #
# scene classes

class StartScene:
    def __init__(self):
        self.group_all = Group()
        self.group_buttons = Group()

        self.running = True

        self.game_name = pygame.font.SysFont('Comic Sans MS', 60).render("My amazing game", True, (0, 0, 0))

        bk = load_image("start_background.png")
        k = bk.get_width() / bk.get_height()
        self.background = scale(bk, (height * k, height))

        self.create_button("play", (350, 310))
        self.create_button("exit", (450, 310))
        self.create_button("settings", (550, 310))

    def create_button(self, code, pos):
        button = ButtonSprite(self, code, scale(load_image(f"buttons/button_{code}.png"), button_size))
        button.set_pos(*pos)

    def loop(self):
        while self.running:
            self.tick()

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                y = height - y
                for button in self.group_buttons:
                    if button.rect.collidepoint(x, y):
                        self.button_click(button.code)
                        break

        self.group_all.update()

        screen.blit(self.background, (0, 0))
        screen.blit(self.game_name, (100, 50))

        self.group_all.draw()
        pygame.display.flip()
        clock.tick(fps)

    def button_click(self, code):
        if code == "play":
            self.running = False
        elif code == "exit":
            terminate()
        elif code == "settings":
            SettingScene().loop()


class GameScene:
    def __init__(self):
        self.fps_i = 0

        self.group_all = Group()
        self.group_walls = Group()
        self.group_spikes = Group()
        self.group_coins = Group()

        self.player = PlayerSprite(self)
        self.player_start_pos = [0, 0]

        self.load_level()

    def load_level(self):
        level_name = "level0"
        data = load_data("levels/" + level_name + ".json")

        self.group_all.clear()
        self.group_walls.clear()
        self.group_spikes.clear()
        self.group_coins.clear()
        self.fps_i = 0
        self.group_all.add(self.player)

        self.player_start_pos = data["start_pos"]
        self.player.set_pos(*self.player_start_pos)

        sprite_classes = {
            "wall": WallSprite,
            "coin": CoinSprite,
            "spike": SpikeSprite,
        }
        for sprite in data["sprites"]:
            sprite_classes[sprite[0]](self, *sprite[1:])

    def loop(self):
        while True:
            self.tick()

    def tick(self):
        clock.tick(fps * fps_tick)

        self.events()

        self.group_all.update()
        self.camera_move()

        self.fps_i = (self.fps_i + 1) % fps_tick
        if self.fps_i == 0:
            screen.fill((100,) * 3)
            self.group_all.draw()
            pygame.display.flip()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key == KEY_JUMP:
                    self.player.jump()
                elif key == KEY_DASH:
                    self.player.dash()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    x, y = event.pos
                    y = height - y
                    self.player.x += x - width / 2
                    self.player.y += y - height / 2

    def camera_move(self):
        max_camera_dist = 50
        global camera_x, camera_y
        player_x = self.player.x - (width - player_size[0]) / 2
        player_y = self.player.y - (height - player_size[1]) / 2

        dx = player_x - camera_x
        dy = player_y - camera_y
        k = 30
        camera_x += dx / k
        camera_y += dy / k

        dx = player_x - camera_x
        dy = player_y - camera_y
        if dx > max_camera_dist:
            camera_x += dx - max_camera_dist
        elif dx < -max_camera_dist:
            camera_x += dx + max_camera_dist
        if dy > max_camera_dist:
            camera_y += dy - max_camera_dist
        elif dy < -max_camera_dist:
            camera_y += dy + max_camera_dist


class MenuScene:
    pass


class SettingScene:
    def __init__(self):
        self.background_scene = screen.copy()
        self.fade = pygame.Surface((width, height))
        self.fade.set_alpha(200)

        self.running = True

        self.group_all = Group()
        self.group_buttons = Group()

    def loop(self):
        while self.running:
            self.tick()

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = event.pos
                y = height - y
                for button in self.group_buttons:
                    if button.rect.collidepoint(x, y):
                        self.button_click(button.code)
                        break

        self.group_all.update()

        screen.blit(self.background_scene, (0, 0))
        screen.blit(self.fade, (0, 0))

        self.group_all.draw()
        pygame.display.flip()
        clock.tick(fps)

    def button_click(self, code):
        if code == "continue":
            self.running = False
        elif code == "exit":
            terminate()


# --------------------------------------------- #
# close game

def terminate():
    pygame.quit()
    exit()


# --------------------------------------------- #
# init pygame

pygame.init()
pygame.display.set_caption("God of Sky")
pygame.font.init()

size = width, height = 1400, 700
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

camera_x, camera_y = 0, 0

# --------------------------------------------- #
# init special consts

COLLIDE_HOOK_UP = 32
COLLIDE_HOOK_DOWN = 16
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

gravity = 1000
max_gravity = 600

friction_air = .65
friction_accel = 2000
friction_reduce = 1400

jump_force = 300
jump_pressed_w = 0.3
jump_pressed_force = gravity / 2
jump_ground_w = 0.05
jump_mercy = 0.3

max_move = 200
move_force = max_move * 12

hook_move_force = 100

wall_jump_x = 400
wall_jump_y = 400

dash_force = 700
dash_end_y_force = 300
dash_w = 0.12

# --------------------------------------------- #
# init sprites values

player_size = (30, 30 / 7 * 9)

button_size = (64,) * 2

tile_w = 32
tile_s = (tile_w,) * 2

spikes_i = 4
spike_sizes = [
    (tile_w, tile_w / 16 * 13),
    (tile_w, tile_w / 16 * 10),
    (tile_w, tile_w / 16 * 6),
    (tile_w, tile_w / 16 * 0),
]
spike_anims = [scale(load_image(f"spikes/spike_{i}.png"), tile_s) for i in range(spikes_i)]

coin_image = scale(load_image("coin.png"), (25,) * 2)

# --------------------------------------------- #
# start game

StartScene().loop()

GameScene().loop()
