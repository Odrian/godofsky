import os
from sys import exit

from random import randint
from pygame.transform import scale, rotate

from file_import import *


def sign(x):
    if x == 0:
        return 0
    if x > 0:
        return 1
    return -1


def load_image(path, color_key=None):
    path = os.path.join("images", path)
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


def screen_draw():
    scale_ = min(window_width / width, window_height / height)
    dx = (window_width - width * scale_) // 2
    dy = (window_height - height * scale_) // 2
    window.blit(scale(screen, (width * scale_, height * scale_)), (dx, dy))
    pygame.display.flip()


def convert_position(x, y):
    y = window_height - y
    scale_ = min(window_width / width, window_height / height)
    dx = (window_width - width * scale_) / 2
    dy = (window_height - height * scale_) / 2
    return (x - dx) / scale_, (y - dy) / scale_


def terminate():
    pygame.quit()
    exit()


class Group:
    def __init__(self):
        self.sprites = []

    def __iter__(self):
        return self.sprites.__iter__()

    def clear(self):
        self.sprites = []

    def add(self, sprite):
        self.sprites.append(sprite)

    def add_all(self, sprites):
        for sprite in sprites:
            self.add(sprite)

    def remove(self, sprite):
        self.sprites.remove(sprite)

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


# --------------------------------------------- #
# main sprites classes

class ImageSprite(pygame.sprite.Sprite):
    def __init__(self, scene, pos, image):
        super().__init__()
        scene.group_all.add(self)
        self.scene = scene
        self.image = image
        self.rect = image.get_rect()
        self.static_height = self.rect.height
        self.set_pos(*pos)

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
    def __init__(self, scene, pos, image):
        super().__init__(scene, pos, image)
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
    def __init__(self, scene, pos, images, rects=None):
        super().__init__(scene, pos, images[0])
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
    def __init__(self, scene, pos, image):
        super().__init__(scene, pos, image)
        self.scene.group_triggers.add(self)

    def triggered(self):
        pass


class ParticleSprite(MovableSprite):
    def __init__(self, scene, pos, color=(255, 0, 0)):
        image = pygame.Surface((5,) * 2)
        image.fill(color)
        super().__init__(scene, pos, image)
        x_max = 400
        y_max = 400
        self.vx = randint(-x_max, x_max)
        self.vy = randint(0, y_max)

    def update(self):
        if self.y < -1000:
            self.scene.group_all.remove(self)
        self.vy -= gravity * dt
        self.move()


class TextSprite(ImageSprite):
    def __init__(self, scene, pos, font, text):
        image = pygame.font.SysFont('Comic Sans MS', font).render(text, True, (0, 0, 0))
        super().__init__(scene, pos, image)


# --------------------------------------------- #
# not main sprite classes

class SpawnSprite(TriggerSprite):
    def __init__(self, scene, pos, size, spawn_pos, priority):
        super().__init__(scene, pos, scale(void_image, size))
        self.spawn_pos = spawn_pos
        self.priority = priority

    def triggered(self):
        self.scene.player.set_spawn(self.spawn_pos, self.priority)


class ButtonSprite(ImageSprite):
    def __init__(self, scene, pos, image, code):
        super().__init__(scene, pos, image)
        scene.group_buttons.add(self)
        self.code = code


def create_button(scene, pos, code):
    ButtonSprite(scene, pos, scale(load_image(f"buttons/button_{code}.png"), button_size), code)


class PlayerSprite(MovableSprite):
    def __init__(self, scene, pos):
        super().__init__(scene, pos, scale(load_image("player.png"), player_size))
        self.spawn_priority = 0
        self.spawn_position = pos
        self.keys = {}
        self.collisions = {}

        self.jump_can = True
        self.jump_pressed_w = 0
        self.jump_ground_w = 0
        self.jump_mercy = 0

        self.hooked = False
        self.hook_right = True
        self.hook_not_w = 0

        self.dash_skill = False
        self.can_dash = True
        self.dash_w = 0

    def collision_all(self, *collides):
        for collide in collides:
            if not self.collisions[collide]:
                return False
        return True

    def collision_any(self, *collides):
        for collide in collides:
            if self.collisions[collide]:
                return True
        return False

    # input functions
    def set_spawn(self, pos, priority):
        if self.spawn_priority < priority:
            self.spawn_position = pos

    def dash(self):
        if DEBUG:
            return
        if not (self.dash_skill and self.can_dash):
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
            xf, yf = (dash_force / 1.4,) * 2

        self.dash_w = dash_w
        self.jump_pressed_w = 0
        self.can_dash = False
        self.vx, self.vy = xf * xd, yf * yd

    def jump(self):
        if DEBUG:
            return
        # simple jump
        if self.jump_can:
            if self.jump_ground_w == 0:
                self.jump_can = False
                self.jump_pressed_w = jump_pressed_w
                self.vy = jump_force
                return True
        # wall jump
        elif self.collision_any(COLLIDE_RIGHT, COLLIDE_LEFT):
            # jump up
            xd = 1 if self.collisions[COLLIDE_LEFT] else -1
            self.vx = wall_jump_x * xd
            self.vy = wall_jump_y
            self.hooked = False
            self.hook_not_w = hook_not_w
            return True
        else:
            if self.jump_mercy == 0:
                self.jump_mercy = jump_mercy
        return False

    def die(self):
        self.set_pos(*self.spawn_position)
        global camera_x, camera_y
        camera_x = self.x - (width - player_size[0]) // 2
        camera_y = self.y - (height - player_size[1]) // 2
        self.vx, self.vy = 0, 0
        self.jump_mercy = 0

    # update functions
    def update(self):
        if DEBUG:
            self.debug_move()
            return

        self.check_collides()
        self.check_triggers()
        self.keys = pygame.key.get_pressed()

        # waiting
        self.jump_ground_w = approach(self.jump_ground_w, 0, dt)
        self.jump_pressed_w = approach(self.jump_pressed_w, 0, dt)
        if self.dash_w > 0:
            self.dash_w = approach(self.dash_w, 0, dt)
            if not self.dash_w > 0:
                self.vy = dash_end_y_force * sign(self.vy)
        self.hook_not_w = approach(self.hook_not_w, 0, dt)

        if self.collisions[COLLIDE_DOWN]:
            self.jump_can = True
            if self.dash_w == 0:
                self.can_dash = True
            if self.vy < 0:
                self.jump_ground_w = jump_ground_w

        # check pressed keys
        if self.keys[KEY_JUMP] and self.jump_pressed_w > 0:
            self.vy += jump_pressed_force * dt
        else:
            self.jump_pressed_w = 0

        self.check_hook()

        self.move_y()
        self.move_x()

        # mercy
        if self.jump_mercy > 0:
            if self.jump():
                self.jump_mercy = 0
            else:
                self.jump_mercy = approach(self.jump_mercy, 0, dt)

        self.check_stops()
        self.move()

        # collect coins
        for coin in self.scene.group_coins:
            if self.rect.colliderect(coin.rect):
                coin.collected()

        # spikes
        if self.scene.group_spikes.collide(self.rect):
            self.die()

    def check_triggers(self):
        collide_func = self.rect.colliderect
        for trigger in self.scene.group_triggers:
            if collide_func(trigger.rect):
                trigger.triggered()

    def debug_move(self):
        self.check_triggers()
        keys = pygame.key.get_pressed()
        f = 2
        if keys[KEY_JUMP]:
            f *= 3
        if keys[KEY_UP]:
            self.y += f
        if keys[KEY_DOWN]:
            self.y -= f
        if keys[KEY_RIGHT]:
            self.x += f
        if keys[KEY_LEFT]:
            self.x -= f
        self.move()

    def check_collides(self):
        collisions = {
            COLLIDE_UP: False,
            COLLIDE_DOWN: False,
            COLLIDE_LEFT: False,
            COLLIDE_RIGHT: False,
            COLLIDE_HOOK_UP: False,
            COLLIDE_HOOK_DOWN: False,
        }
        r1 = self.rect
        for sprite in self.scene.group_walls:
            r2 = sprite.rect

            x11, y11 = r1.topleft
            w1, h1 = r1.size
            x12, y12 = x11 + w1, y11 + h1

            x21, y21 = r2.topleft
            w2, h2 = r2.size
            x22, y22 = x21 + w2, y21 + h2

            collide_x = x11 <= x22 and x12 >= x21
            collide_y = y11 <= y22 and y12 >= y21
            if not (collide_x and collide_y):
                continue

            some_collide_x = min(abs(x12 - x21), abs(x11 - x22)) < max_collide_pixels
            some_collide_y = min(abs(y12 - y21), abs(y11 - y22)) < max_collide_pixels

            if collide_y and not some_collide_x:
                if y11 >= y21 + h2 / 2:
                    collisions[COLLIDE_DOWN] = True
                    self.y += y22 - y11
                else:
                    collisions[COLLIDE_UP] = True
                    self.y += y21 - y12
            if collide_x and not some_collide_y:
                if x11 >= x21 + w2 / 2:
                    collisions[COLLIDE_LEFT] = True
                    self.x += x22 - x11
                else:
                    collisions[COLLIDE_RIGHT] = True
                    self.x += x21 - x12
            if not y11 + h1 * 2 / 3 > y22:
                collisions[COLLIDE_HOOK_UP] = True
            if not y11 + h1 / 3 < y21:
                collisions[COLLIDE_HOOK_DOWN] = True
        self.collisions = collisions

    def check_hook(self):
        if self.dash_w != 0:
            return
        # check if you out of available space
        if self.hooked:
            if self.hook_right:
                if not self.collisions[COLLIDE_RIGHT]:
                    self.hooked = False
            else:
                if not self.collisions[COLLIDE_LEFT]:
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
                if self.hook_not_w == 0 and self.collision_any(COLLIDE_LEFT, COLLIDE_RIGHT) and \
                        self.collision_all(COLLIDE_HOOK_DOWN, COLLIDE_HOOK_UP):
                    self.hooked = True
                    self.vy = 0
                    self.hook_right = self.collisions[COLLIDE_RIGHT]

        # y move
        if self.hooked and self.hook_not_w == 0:
            if self.keys[KEY_UP]:
                self.vy = hook_move_force
            elif self.keys[KEY_DOWN]:
                self.vy = -hook_move_force
            else:
                self.vy = 0

    def move_y(self):
        if not ((self.hooked and self.hook_not_w == 0) or self.dash_w != 0):
            if not self.collisions[COLLIDE_DOWN]:
                self.vy -= gravity * dt
                if self.vy < -max_gravity:
                    self.vy = -max_gravity
                self.jump_can = False

    def move_x(self):
        if self.hooked or self.dash_w > 0:
            return

        mult = 1 if self.collisions[COLLIDE_DOWN] else friction_air

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

    def check_stops(self):
        if self.collisions[COLLIDE_UP]:
            if self.vy > 0:
                self.vy = 0
        if self.collisions[COLLIDE_DOWN]:
            if self.vy < 0:
                self.vy = 0
        if self.collisions[COLLIDE_RIGHT]:
            if self.vx > 0:
                self.vx = 0
        if self.collisions[COLLIDE_LEFT]:
            if self.vx < 0:
                self.vx = 0


class CoinSprite(ImageSprite):
    def __init__(self, scene, pos):
        super().__init__(scene, pos, coin_image)
        self.position = pos
        self.scene.group_coins.add(self)
        self.player_connect = False
        self.timer = -1

    def update(self):
        if self.timer != -1:
            self.timer -= 1
            self.image.set_alpha(self.timer)
            if self.timer == 0:
                self.scene.group_all.remove(self)

    def collected(self):
        global coins_count
        coins_count += 1
        self.timer = 255
        self.scene.group_coins.remove(self)


class SpikeSprite(ImageSprite):
    def __init__(self, scene, pos, typ, length):
        spike_image = self._choice_image(typ)
        image = self._create_image(spike_image, length, typ)
        super().__init__(scene, pos, image)
        scene.group_spikes.add(self)

    def _choice_image(self, typ):
        if typ == "l":
            return spike_image_left
        elif typ == "r":
            return spike_image_right
        elif typ == "u":
            return spike_image_up
        else:
            return spike_image_down

    def _create_image(self, spike_image, length, typ):
        k = 1 if typ in "lr" else 0
        spike_size = 13
        length //= spike_size
        size = [length * spike_size + 1, spike_size]
        if k == 1:
            size = size[::-1]
        image = scale(void_image, size)
        pos_ = [0, 0]
        for i in range(length):
            image.blit(spike_image, pos_)
            pos_[k] += spike_size
        return image


class TestSpikeSprite(SimpleAnimSprite):
    def __init__(self, scene, pos):
        super().__init__(scene, pos, test_spike_anims, test_spike_sizes)
        scene.group_spikes.add(self)


class SimpleWallSprite(ImageSprite):
    def __init__(self, scene, pos, size):
        super().__init__(scene, pos, scale(black_image, size))
        scene.group_walls.add(self)


class WallSprite(ImageSprite):
    def __init__(self, scene, pos, typ, length):
        wall_image = self._choice_image(typ)
        image = self._create_image(wall_image, length)
        super().__init__(scene, pos, image)
        scene.group_walls.add(self)

    def _choice_image(self, typ):
        if typ == "ground":
            return wall_cave_ground
        else:
            pass

    def _create_image(self, wall_image, length):
        wall_size = 28
        size = [length, wall_size]
        image = scale(void_image, size)
        pos_ = [0, 0]
        for i in range(length // wall_size + 1):
            image.blit(wall_image, pos_)
            pos_[0] += wall_size
        return image


class ShadowSprite(ImageSprite):
    def __init__(self, scene, pos, size, angle=0):
        image = rotate(scale(shadow, size), angle)
        super().__init__(scene, pos, image)


class DoorSprite(TriggerSprite):
    def __init__(self, scene, pos, level):
        super().__init__(scene, pos, scale(yellow_image, (40, 60)))
        self.level = level

    def triggered(self):
        self.scene.load_level(self.level)


class CannonSprite(ImageSprite):
    def __init__(self, scene, pos, size, angle, data):
        super().__init__(scene, pos, rotate(scale(cannon_image, size), angle))
        self.angle = angle
        pos[0] += self.rect.w / 2 - 3
        pos[1] += self.rect.h / 2 - 3
        self.pos = pos
        rate, speed, rnd, rnd0 = data
        rate = randint(rate // rnd, rate * rnd // 1)
        speed = randint(speed // rnd, speed * rnd // 1)
        self.rate = rate
        self.speed = speed
        self.tick = 0
        if rnd0:
            self.tick = randint(0, rate)

    def update(self):
        self.tick += 1
        if self.tick >= self.rate:
            BulletSprite(self.scene, self.pos, self.angle, self.speed)
            self.tick -= self.rate


def create_cannon(scene, pos, size, angle, data, xy=(1, 1)):
    for x in range(xy[0]):
        for y in range(xy[1]):
            CannonSprite(scene, [pos[0] + size[0] * x, pos[1] + size[1] * y], size, angle, data)


class BulletSprite(MovableSprite):
    def __init__(self, scene, pos, angle, speed):
        super().__init__(scene, pos, bullet_image)
        if angle == 0:
            self.vy = speed
        elif angle == 180:
            self.vy = -speed
        elif angle == 90:
            self.vx = speed
        elif angle == -90:
            self.vx = -speed

    def update(self):
        self.move()
        if self.rect.colliderect(self.scene.player.rect):
            self.scene.player.die()
        if self.scene.group_walls.collide(self.rect):
            self.scene.group_all.remove(self)


# --------------------------------------------- #
# scene classes

class ButtonsScene:
    def __init__(self):
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
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = convert_position(*event.pos)
                for button in self.group_buttons:
                    if button.rect.collidepoint(x, y):
                        # button press
                        break
            elif event.type == pygame.MOUSEBUTTONUP:
                x, y = convert_position(*event.pos)
                for button in self.group_buttons:
                    # button unpress
                    if button.rect.collidepoint(x, y):
                        self.button_click(button.code)
                        break
            elif event.type == pygame.VIDEORESIZE:
                global window_height, window_width
                window_width, window_height = (window.get_width(), window.get_height())

        self.group_all.update()

        screen.fill((20,) * 3)
        self.group_all.draw()
        screen_draw()
        clock.tick(fps)

    def button_click(self, code):
        pass


class StartScene(ButtonsScene):
    def __init__(self):
        super().__init__()

        TextSprite(self, (140, 400), 60, "My amazing game")

        create_button(self, (250, 220), "play")
        # create_button(self, (350, 220), "exit")
        # create_button(self, (450, 220), "settings")

    def button_click(self, code):
        if code == "play":
            self.running = False
        elif code == "exit":
            terminate()
        elif code == "settings":
            SettingScene().loop()


class GameScene:
    def __init__(self):
        self.running = True

        self.fps_i = 0

        self.group_all = Group()
        self.group_walls = Group()
        self.group_spikes = Group()
        self.group_coins = Group()
        self.group_triggers = Group()

        self.player = None

        self.load_level("level0")

    def load_level(self, level_name):
        if level_name == "end":
            self.running = False
            return
        level = load_data("levels/" + level_name + ".json")

        self.group_all.clear()
        self.group_walls.clear()
        self.group_spikes.clear()
        self.group_coins.clear()
        self.fps_i = 0

        player_pos = self.convert(level["start_pos"])
        self.player = PlayerSprite(self, player_pos)

        global camera_x, camera_y
        camera_x = player_pos[0] - (width - player_size[0]) // 2
        camera_y = player_pos[1] - (height - player_size[1]) // 2

        sprite_classes = {
            "black": SimpleWallSprite,
            "spikes": SpikeSprite,
            "cannons": create_cannon,
            "walls": SimpleWallSprite,
            "coins": CoinSprite,
            "shadows": ShadowSprite,
            "spawns": SpawnSprite,
            "text": TextSprite,
            "door": DoorSprite,
        }
        sprites = level["sprites"]
        for typ in sprite_classes:
            for data in sprites[typ]:
                new_data = list(map(self.convert, data[:3])) + data[3:]
                sprite_classes[typ](self, *new_data)

    def convert(self, value):
        typ = type(value)
        if typ in (list, tuple):
            return list(map(lambda x: int(x * 20), value))
        return value

    def loop(self):
        while self.running:
            self.tick()

    def tick(self):
        clock.tick(fps * fps_tick)

        self.events()

        self.group_all.update()
        self.camera_move()

        self.fps_i = (self.fps_i + 1) % fps_tick
        if self.fps_i == 0:
            screen.fill((20,) * 3)
            self.group_all.draw()
            screen_draw()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                key = event.key
                if key == KEY_JUMP:
                    self.player.jump_mercy = jump_mercy
                elif key == KEY_DASH:
                    self.player.dash()
                elif key == pygame.K_g:
                    global DEBUG
                    DEBUG = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    x, y = convert_position(*event.pos)
                    x += camera_x - player_size[0] / 2
                    y += camera_y - player_size[1] / 2
                    self.player.set_pos(x, y)
                    # pos = (camera_x + x, camera_y + y)
                    # for i in range(20):
                    #     ParticleSprite(self, pos)
            elif event.type == pygame.VIDEORESIZE:
                global window_height, window_width
                window_width, window_height = (window.get_width(), window.get_height())

    def camera_move(self):
        global camera_x, camera_y
        max_camera_dist = 50
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


class SettingScene(ButtonsScene):
    def __init__(self):
        super().__init__()

        ImageSprite(self, (0, 0), screen.copy())
        fade = pygame.Surface((width, height))
        fade.set_alpha(200)
        ImageSprite(self, (0, 0), fade)

        create_button(self, (400, 100), "yes")
        create_button(self, (500, 100), "no")

    def button_click(self, code):
        if code == "yes":
            # save
            self.running = False
        elif code == "no":
            self.running = False


class EndScene:
    def __init__(self):
        global camera_x, camera_y
        camera_x, camera_y = 0, 0
        self.running = True
        self.group_all = Group()
        TextSprite(self, [250, 350], 60, "Спасибо за игру")
        TextSprite(self, [250, 100], 30, f"Вы собрали {coins_count}/2 Пончиков")

    def loop(self):
        while True:
            self.tick()

    def tick(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.VIDEORESIZE:
                global window_height, window_width
                window_width, window_height = (window.get_width(), window.get_height())

        self.group_all.update()

        screen.fill((20,) * 3)
        self.group_all.draw()
        screen_draw()
        clock.tick(fps)


# --------------------------------------------- #
# init pygame

pygame.init()
pygame.display.set_caption("God of Sky")
pygame.font.init()

window_width, window_height = 1400, 700
window = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)

width, height = 1000, 500
screen = pygame.Surface((width, height))

clock = pygame.time.Clock()

camera_x, camera_y = 0, 0

# --------------------------------------------- #
# init special consts

COLLIDE_HOOK_UP = 6
COLLIDE_HOOK_DOWN = 5
COLLIDE_UP = 4
COLLIDE_DOWN = 3
COLLIDE_RIGHT = 2
COLLIDE_LEFT = 1

# --------------------------------------------- #
# init consts

max_collide_pixels = 5

fps = 60
fps_tick = 3
dt = 1 / fps / fps_tick

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

hook_move_force = 150

hook_up_jump = 360
hook_not_w = 0.1

wall_jump_x = 400
wall_jump_y = 400

dash_force = 700
dash_end_y_force = 300
dash_w = 0.12

# --------------------------------------------- #
# init sprites values

black_image = pygame.Surface((1, 1))
black_image.fill((0,) * 3)

yellow_image = pygame.Surface((1, 1))
yellow_image.fill((100, 100, 0))

void_image = pygame.Surface((1, 1), pygame.SRCALPHA, 32).convert_alpha()
shadow = load_image("shadow.png")

player_size = (30, 40)

button_size = (64,) * 2

tile_w = 32
tile_s = (tile_w,) * 2

test_spikes_i = 4
test_spike_sizes = [
    (tile_w, tile_w / 16 * 13),
    (tile_w, tile_w / 16 * 10),
    (tile_w, tile_w / 16 * 6),
    (tile_w, tile_w / 16 * 0),
]
test_spike_anims = [scale(load_image(f"spikes/spike_{i}.png"), tile_s) for i in range(test_spikes_i)]

coin_image = scale(load_image("coin.png"), (25,) * 2)

spike_image_down = load_image("spike.png")
spike_image_up = rotate(spike_image_down, 180)
spike_image_right = rotate(spike_image_down, 90)
spike_image_left = rotate(spike_image_down, -90)

wall_cave_ground = scale(load_image("cave_ground.png"), (28, 28))

cannon_image = scale(load_image("cannon.png"), (20, 20))
bullet_image = load_image("bullet.png")

# --------------------------------------------- #
# start game

coins_count = 0

DEBUG = False

StartScene().loop()

GameScene().loop()

EndScene().loop()
