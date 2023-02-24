import pygame
import random
import sys
import os
import pytmx


scale = 6
game_speed = 10
walk_timer_delay = 120
pygame.init()
pygame.display.set_caption("The Legend of Zelda: Link's Awakening")
die_sound = pygame.mixer.Sound(f"data/sounds/other_sounds/enemy_die.wav")
die_sound.set_volume(0.15)
size = width, height = 16 * 10 * scale, 16 * 9 * scale
screen = pygame.display.set_mode(size)
screen_rect = (0, 0, width, height)
change_s = pygame.USEREVENT + 1
pygame.time.set_timer(change_s, 0)
change_sword_anim_timer = pygame.USEREVENT + 1
pygame.time.set_timer(change_sword_anim_timer, 0)
change_sword_anim_timer_go = False
iterations_count = 0



def load_image(name, colorkey=None, path='data', x=0, y=0, color=0):
    fullname = os.path.join(path, name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((x, y))
            if color != 0:
                colorkey = color
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


ico = load_image('triforce.png')
ico = pygame.transform.scale(ico, (32, 32))

pygame.display.set_icon(ico)


def sprite_collideany(first, group, first_rect='rect', second_rect='rect'):
    sp = []
    for second in group:
        if first_rect == 'rect' and second_rect == 'rect' and first.rect.colliderect(second.rect):
            sp.append(second)
        elif first_rect == 'hitbox' and second_rect == 'hitbox' and first.hitbox.colliderect(second.hitbox):
            sp.append(second)
        elif first_rect == 'rect' and second_rect == 'hitbox' and first.rect.colliderect(second.hitbox):
            sp.append(second)
        elif first_rect == 'hitbox' and second_rect == 'rect' and first.hitbox.colliderect(second.rect):
            sp.append(second)
    return sp


def play_sound_without_music(sound):
    pygame.mixer.music.pause()
    pygame.mixer.Sound.play(sound)


class World:
    def __init__(self, filename, free_tiles, walls):
        self.map = pytmx.load_pygame(f"maps/{filename}")
        self.height = self.map.height
        self.width = self.map.width
        self.tile_size = self.map.tilewidth * scale
        self.free_tiles = free_tiles
        self.walls = walls

    def render(self, screen):
        enemies_sp = []
        for y in range(self.height):
            for x in range(self.width):
                id = self.get_tile_id((x, y))
                if id in self.walls:
                    if id == 254:
                        Bush(x * self.tile_size, y * self.tile_size, self.map.get_tile_image(x, y, 0))
                    else:
                        Wall(x * self.tile_size, y * self.tile_size, self.map.get_tile_image(x, y, 0))
                else:
                    if id == 326:
                        PassTile(x * self.tile_size, y * self.tile_size, self.map.get_tile_image(0, 0, 0))
                        enemies_sp.append((x * self.tile_size, y * self.tile_size))
                    elif id == 230:
                        Grass(x * self.tile_size, y * self.tile_size, self.map.get_tile_image(x, y, 0))
                    else:
                        PassTile(x * self.tile_size, y * self.tile_size, self.map.get_tile_image(x, y, 0))
        for enemy_coords in enemies_sp:
            Octorok(enemy_coords[0], enemy_coords[1])

    def get_tile_id(self, position):
        return self.map.tiledgidmap[list(self.map.tiledgidmap.keys())[self.map.get_tile_gid(position[0], position[1], 0) - 1]]

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self):
        self.dx = 0
        self.dy = 0

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy
        # print(obj.rect.x, obj.rect.y)

    # позиционировать камеру на объекте target
    def update(self, x, y):
        self.dx = x
        self.dy = y


class Inventory(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(something_group)
        self.image = pygame.surface.Surface((width, 16 * scale + 16))
        self.rect = pygame.Rect(0, height - self.image.get_height() + 18, self.image.get_width(), self.image.get_height())
        self.font = pygame.font.Font("data/font/aesymatt.ttf", 54)
        self.font_color = (0, 0, 0)
        self.sprites = {}
        self.sprites_create()

    def sprites_create(self):
        for root, dirs, files in os.walk("data/inventory"):
            for filename in files:
                if 'sword' in filename:
                    img = load_image(filename, path='data/inventory', colorkey=-1)
                else:
                    img = load_image(filename, path='data/inventory', colorkey=-1)
                #print(filename, '- width:', str(img.get_width()) + ', height:', img.get_height())
                if 'sword' in filename:
                    self.sprites[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * scale,
                                                                                        img.get_height() * scale))
                else:
                    self.sprites[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))

    def update(self):
        self.image.fill(pygame.Color('#f8eba8'))
        rupees_count = self.font.render((3 - len(str(link.rupee))) * '0' + str(link.rupee), 1, self.font_color)
        self.image.blit(rupees_count, (self.rect.width // 2, self.rect.height // 2.6))
        if 'shield' in link.taken_items:
            main_inventory = 'sword_and_shield'
        else:
            main_inventory = 'sword_only'
        self.image.blit(self.sprites[main_inventory], (0, 0))
        self.image.blit(self.sprites['rupee'], (self.rect.width // 2, self.rect.height // 20))
        count = 1
        fulls = link.hp // 2
        rest = link.hp % 2 == 1
        i = 50
        for i in range(125, 75 + 50 * (fulls + 1), 50):
            self.image.blit(self.sprites['full_heart'], (self.image.get_width() * 0.5 + i,
                                                         self.image.get_height() * 0.08))
            count += 1
        if fulls == 0:
            i = 75
        if rest:
            self.image.blit(self.sprites['half_heart'], (self.image.get_width() * 0.5 + i + 50,
                                                         self.image.get_height() * 0.08))
            i += 50
            count += 1
        for i in range(i + 50, i + 50 * (5 - count), 50):
            self.image.blit(self.sprites['empty_heart'], (self.image.get_width() * 0.5 + i,
                                                         self.image.get_height() * 0.15))


class Link(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=6, speed=0.6 * game_speed):
        super().__init__(link_group)
        self.speed = speed
        self.scale = scale
        self.can_move = True
        self.sword_anim_count = 0
        self.move_timer_go = False
        self.y_speed = 0
        self.x_speed = 0
        self.change_sprite = False
        self.show_sword = False
        self.attack_btn_cliked = False
        self.run_spin_attack = False
        self.sprites_create()
        self.walk_frames = self.simple_walk_frames.copy()
        self.walk_frames_s = self.simple_walk_frames_s.copy()
        self.rect = pygame.Rect(0, 0, self.walk_frames[0].get_width(), self.walk_frames[0].get_height())
        self.hitbox = pygame.Rect(0, 0, self.walk_frames[0].get_width() * 0.3, self.walk_frames[0].get_height() * 0.6)
        self.hitbox = self.hitbox.move(self.walk_frames[0].get_width() * 0.35, self.walk_frames[0].get_height() * 0.2)
        self.cur_frame = 0
        self.image = self.simple_walk_frames[self.cur_frame]
        self.rect = self.rect.move(x, y)
        self.hitbox = self.hitbox.move(x, y)
        self.pick_item_count = 0
        self.picked_item = 0
        self.items_in_inventory = []
        self.taken_items = []
        self.l_clicked = False
        self.shield_is_active = False
        self.sword_charge_count = 0
        self.hurt_count = 0
        self.charging = False
        self.is_hurting = False
        self.sword_slashs_sounds = []
        self.get_items_sounds = {}
        self.shield_sounds = {}
        self.sounds_create()
        self.hurt_timer_count = 0
        self.hurt_animation_count = 0
        self.change_sprite_to_hurt = False
        self.y_gravity, self.x_gravity = 0, 0
        self.uncontrolled_movement = False
        self.uncontrolled_movement_count = 0
        self.sword_swinging = False
        self.hp = 6
        self.max_hp = 6
        self.rupee = 0
        self.last_sword_hit_something = True

    def sprites_create(self):
        self.simple_walk_frames = []
        self.simple_walk_frames_s = []
        img = load_image(f"walk_1.png", path='data/link/simple_walk', colorkey=-1)
        img_s = pygame.transform.flip(img, True, False)
        self.simple_walk_frames.append(img)
        self.simple_walk_frames_s.append(img_s)
        img = load_image(f"walk_2.png", path='data/link/simple_walk', colorkey=-1)
        img_s = pygame.transform.flip(img, True, False)
        self.simple_walk_frames.append(img)
        self.simple_walk_frames_s.append(img_s)
        img = load_image(f"walk_3.png", path='data/link/simple_walk', colorkey=-1)
        img_s = load_image(f"walk_4.png", path='data/link/simple_walk', colorkey=-1)
        self.simple_walk_frames.append(img)
        self.simple_walk_frames_s.append(img_s)
        self.simple_walk_frames.append(pygame.transform.flip(img, True, False))
        self.simple_walk_frames_s.append(pygame.transform.flip(img_s, True, False))
        for i in range(len(self.simple_walk_frames)):
            self.simple_walk_frames[i] = pygame.transform.scale(self.simple_walk_frames[i],
                                                                (self.simple_walk_frames[i].get_width() * self.scale,
                                                                 self.simple_walk_frames[i].get_height() * self.scale))
            self.simple_walk_frames_s[i] = pygame.transform.scale(self.simple_walk_frames_s[i],
                                                                  (
                                                                  self.simple_walk_frames_s[i].get_width() * self.scale,
                                                                  self.simple_walk_frames_s[
                                                                      i].get_height() * self.scale))
        self.sword_swing_frames = {}
        for root, dirs, files in os.walk("data\link\sword_animation"):
            for filename in files:
                img = load_image(filename, path='data\link\sword_animation', colorkey=-1)
                self.sword_swing_frames[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * self.scale,
                                                                                 img.get_height() * self.scale))
        self.sword_swing_frames['hold_right'] = pygame.transform.flip(self.sword_swing_frames['hold_left'], True, False)

        self.shield_walk_frames = []
        self.shield_walk_frames_s = []
        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data\link\shield_walk_animation', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data\link\shield_walk_animation', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.shield_walk_frames.append(img)
            self.shield_walk_frames_s.append(img_s)

        self.take_item_frames = {}
        for root, dirs, files in os.walk("data\link\\take_item_poses"):
            for filename in files:
                img = load_image(filename, path='data\link\\take_item_poses', colorkey=-1)
                self.take_item_frames[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * self.scale,
                                                                                    img.get_height() * self.scale))
        self.active_shield_walk_frames = []
        self.active_shield_walk_frames_s = []
        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data\link\shield_active_walk_animation', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data\link\shield_active_walk_animation', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.active_shield_walk_frames.append(img)
            self.active_shield_walk_frames_s.append(img_s)

        self.hurt_simple_walk_frames = []
        self.hurt_simple_walk_frames_s = []
        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data/link/hurt_simple_walk', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data/link/hurt_simple_walk', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.hurt_simple_walk_frames.append(img)
            self.hurt_simple_walk_frames_s.append(img_s)

        self.hurt_shield_walk_frames = []
        self.hurt_shield_walk_frames_s = []
        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data/link/hurt_shield_walk', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data/link/hurt_shield_walk', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.hurt_shield_walk_frames.append(img)
            self.hurt_shield_walk_frames_s.append(img_s)

        self.hurt_shield_active_walk_frames = []
        self.hurt_shield_active_walk_frames_s = []
        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data/link/hurt_shield_active_walk', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data/link/hurt_shield_active_walk', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.hurt_shield_active_walk_frames.append(img)
            self.hurt_shield_active_walk_frames_s.append(img_s)

        self.hurt_sword_swing_frames = {}
        for root, dirs, files in os.walk("data/link/hurt_sword_animation"):
            for filename in files:
                img = load_image(filename, path='data/link/hurt_sword_animation', colorkey=-1)
                self.hurt_sword_swing_frames[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * self.scale,
                                                                                      img.get_height() * self.scale))
        self.hurt_sword_swing_frames['hold_right'] = pygame.transform.flip(self.hurt_sword_swing_frames['hold_left'],
                                                                           True, False)

    def sounds_create(self):
        for num in range(1, 5):
            sound = pygame.mixer.Sound(f"data/sounds/sword_sounds/LA_Sword_Slash{num}.wav")
            sound.set_volume(0.1)
            self.sword_slashs_sounds.append(sound)
        for root, dirs, files in os.walk("data/sounds/get_item_sounds"):
            for filename in files:
                sound = pygame.mixer.Sound('data/sounds/get_item_sounds' + '/' + filename)
                sound.set_volume(0.05)
                self.get_items_sounds[filename[:-4]] = sound
        for root, dirs, files in os.walk("data/sounds/shield_sounds"):
            for filename in files:
                sound = pygame.mixer.Sound('data/sounds/shield_sounds' + '/' + filename)
                sound.set_volume(0.15)
                self.shield_sounds[filename[:-4]] = sound
        self.hurt_sound = pygame.mixer.Sound(f"data/sounds/other_sounds/link_hurt.wav")
        self.hurt_sound.set_volume(0.15)

    def is_run_into_wall(self):
        link.hitbox.y += link.y_speed
        if sprite_collideany(self, walls, first_rect='hitbox'):
            link.hitbox.y -= link.y_speed
        else:
            link.rect.y += link.y_speed
        link.hitbox.x += link.x_speed
        if sprite_collideany(self, walls, first_rect='hitbox'):
            link.hitbox.x -= link.x_speed
        else:
            link.rect.x += link.x_speed

    def down_attack(self):
        if (self.image == self.sword_swing_frames['down_left'] or self.image == self.hurt_sword_swing_frames['down_left']) and change_sword_sprite:
            self.image = self.sword_swing_frames['down']
            sword.image = sword.frames['sword_circle_botton_left']
            sword.y = self.rect.y + self.rect.height * 0.9
            sword.x = self.rect.x - self.rect.width * 0.7
            self.sword_anim_count += 1
            return
        if (self.image == self.sword_swing_frames['down'] or self.image == self.hurt_sword_swing_frames['down']) and change_sword_sprite and (self.sword_anim_count == 2
                                                                                      or self.sword_anim_count == 3
                                                                                      or self.run_spin_attack):
            sword.image = sword.frames['sword_down']
            sword.y = self.rect.y + self.rect.height
            sword.x = self.rect.x + self.rect.width * 0.55
            pygame.time.set_timer(change_sword_anim_timer, 0)
            pygame.time.set_timer(change_s, walk_timer_delay)
            if self.sword_anim_count == 3:
                self.can_move = True
                self.sword_anim_count = 0
                sword.y -= sword.rect.height * 0.2
                self.last_sword_hit_something = False
            else:
                self.sword_anim_count += 1
            return

    def up_attack(self):
        if (self.image == self.sword_swing_frames['up_right'] or self.image == self.hurt_sword_swing_frames['up_right']) and change_sword_sprite:
            self.image = self.sword_swing_frames['up']
            sword.image = sword.frames['sword_circle_up_right']
            sword.y = self.rect.y - self.rect.height * 0.8
            sword.x = self.rect.x + self.rect.width * 0.8
            self.sword_anim_count += 1
            return
        if (self.image == self.sword_swing_frames['up'] or self.image == self.hurt_sword_swing_frames['up']) and change_sword_sprite and (self.sword_anim_count == 2
                                                                                    or self.sword_anim_count == 3
                                                                                    or self.run_spin_attack):
            sword.image = sword.frames['sword_up']
            sword.y = self.rect.y - self.rect.height
            sword.x = self.rect.x
            pygame.time.set_timer(change_sword_anim_timer, 0)
            pygame.time.set_timer(change_s, walk_timer_delay)
            if self.sword_anim_count == 3:
                self.can_move = True
                self.sword_anim_count = 0
                sword.y += sword.rect.height * 0.35
                self.last_sword_hit_something = False
            else:
                self.sword_anim_count += 1
            return

    def left_attack(self):
        if (self.image == self.sword_swing_frames['up_left'] or self.image == self.hurt_sword_swing_frames['up_left']) and change_sword_sprite:
            self.image = self.sword_swing_frames['hold_left']
            sword.image = sword.frames['sword_circle_up_left']
            sword.y = self.rect.y - self.rect.height * 0.75
            sword.x = self.rect.x - self.rect.width * 0.75
            self.sword_anim_count += 1
            return
        if (self.image == self.sword_swing_frames['hold_left'] or self.image == self.hurt_sword_swing_frames['hold_left'])and change_sword_sprite and (self.sword_anim_count == 2
                                                                                           or self.sword_anim_count == 3
                                                                                           or self.run_spin_attack):
            sword.image = sword.frames['sword_left']
            sword.y = self.rect.y + self.rect.height * 0.5
            sword.x = self.rect.x - self.rect.width
            pygame.time.set_timer(change_sword_anim_timer, 0)
            pygame.time.set_timer(change_s, walk_timer_delay)
            if self.sword_anim_count == 3:
                self.can_move = True
                self.sword_anim_count = 0
                sword.x += sword.rect.width * 0.32
                self.last_sword_hit_something = False
            else:
                self.sword_anim_count += 1
            return

    def right_attack(self):
        if (self.image == self.sword_swing_frames['up_right_2'] or self.image == self.hurt_sword_swing_frames['up_right_2']) and change_sword_sprite:
            self.image = self.sword_swing_frames['hold_right']
            sword.image = sword.frames['sword_circle_up_right']
            sword.y = self.rect.y - self.rect.height * 0.75
            sword.x = self.rect.x + self.rect.width * 0.75
            self.sword_anim_count += 1
            return
        if (self.image == self.sword_swing_frames['hold_right'] or self.image == self.hurt_sword_swing_frames['hold_right']) and change_sword_sprite and (self.sword_anim_count == 2
                                                                                            or self.sword_anim_count == 3
                                                                                            or self.run_spin_attack):
            sword.image = sword.frames['sword_right']
            sword.y = self.rect.y + self.rect.height * 0.5
            sword.x = self.rect.x + self.rect.width * 0.9
            pygame.time.set_timer(change_sword_anim_timer, 0)
            pygame.time.set_timer(change_s, walk_timer_delay)
            if self.sword_anim_count == 3:
                self.can_move = True
                self.sword_anim_count = 0
                sword.x -= sword.rect.width * 0.2
                self.last_sword_hit_something = False
            else:
                self.sword_anim_count += 1
            return

    def change_simple_frame_to_hurt_and_back(self):
        if link.change_sprite_to_hurt and link.image in link.sword_swing_frames.values():
            for key in link.sword_swing_frames.keys():
                if link.sword_swing_frames[key] == link.image:
                    link.image = link.hurt_sword_swing_frames[key]
                    break
        elif not link.change_sprite_to_hurt and link.image in link.hurt_sword_swing_frames.values():
            for key in link.hurt_sword_swing_frames.keys():
                if link.hurt_sword_swing_frames[key] == link.image:
                    link.image = link.sword_swing_frames[key]
                    break

        elif link.change_sprite_to_hurt and link.image in link.simple_walk_frames:
            link.image = link.hurt_simple_walk_frames[link.cur_frame]
        elif link.change_sprite_to_hurt and link.image in link.simple_walk_frames_s:
            link.image = link.hurt_simple_walk_frames_s[link.cur_frame]
        elif not link.change_sprite_to_hurt and link.image in link.hurt_simple_walk_frames:
            link.image = link.simple_walk_frames[link.cur_frame]
        elif not link.change_sprite_to_hurt and link.image in link.hurt_simple_walk_frames_s:
            link.image = link.simple_walk_frames_s[link.cur_frame]

        elif link.change_sprite_to_hurt and link.image in link.shield_walk_frames:
            link.image = link.hurt_shield_walk_frames[link.cur_frame]
        elif link.change_sprite_to_hurt and link.image in link.shield_walk_frames_s:
            link.image = link.hurt_shield_walk_frames_s[link.cur_frame]
        elif not link.change_sprite_to_hurt and link.image in link.hurt_shield_walk_frames:
            link.image = link.shield_walk_frames[link.cur_frame]
        elif not link.change_sprite_to_hurt and link.image in link.hurt_shield_walk_frames_s:
            link.image = link.shield_walk_frames_s[link.cur_frame]

        elif link.change_sprite_to_hurt and link.image in link.active_shield_walk_frames:
            link.image = link.hurt_shield_active_walk_frames[link.cur_frame]
        elif link.change_sprite_to_hurt and link.image in link.active_shield_walk_frames_s:
            link.image = link.hurt_shield_active_walk_frames_s[link.cur_frame]
        elif not link.change_sprite_to_hurt and link.image in link.hurt_shield_active_walk_frames:
            link.image = link.active_shield_walk_frames[link.cur_frame]
        elif not link.change_sprite_to_hurt and link.image in link.hurt_shield_active_walk_frames_s:
            link.image = link.active_shield_walk_frames_s[link.cur_frame]

    def update(self, change_sprite=False):
        # self.change_sprite_to_hurt = False
        global change_sword_anim_timer_go
        if (self.image == self.take_item_frames['one_hand'] or self.image == self.take_item_frames['two_hands']
                or self.image == self.take_item_frames['ocarina']) and iterations_count - self.pick_item_count == 100:
            self.can_move = True
            self.picked_item.rect.x = -10000
            self.picked_item.rect.y = -10000
            pygame.mixer.music.unpause()
        if self.sword_charge_count >= 120 and not self.charging:
            self.charging = True
            self.sword_charge_count = iterations_count
        if self.charging and iterations_count - self.sword_charge_count == 5:
            if sword.image == sword.frames['charge_sword_down']:
                sword.image = sword.frames['sword_down']
            elif sword.image == sword.frames['sword_down']:
                sword.image = sword.frames['charge_sword_down']
            elif sword.image == sword.frames['charge_sword_up']:
                sword.image = sword.frames['sword_up']
            elif sword.image == sword.frames['sword_up']:
                sword.image = sword.frames['charge_sword_up']
            elif sword.image == sword.frames['sword_right']:
                sword.image = sword.frames['charge_sword_right']
            elif sword.image == sword.frames['charge_sword_right']:
                sword.image = sword.frames['sword_right']
            elif sword.image == sword.frames['sword_left']:
                sword.image = sword.frames['charge_sword_left']
            elif sword.image == sword.frames['charge_sword_left']:
                sword.image = sword.frames['sword_left']
            self.sword_charge_count = iterations_count

        if change_sprite and self.can_move:
            self.image = self.walk_frames_s[self.cur_frame]
        else:
            if self.can_move:
                self.image = self.walk_frames[self.cur_frame]

        keys = pygame.key.get_pressed()
        if not ((keys[pygame.K_DOWN] or keys[pygame.K_s]) or (keys[pygame.K_UP] or keys[pygame.K_w])
                or (keys[pygame.K_LEFT] or keys[pygame.K_a]) or (keys[pygame.K_RIGHT] or keys[pygame.K_d])) \
                and self.can_move:
            self.image = self.walk_frames[self.cur_frame]
            if self.move_timer_go:
                self.move_timer_go = False
                pygame.time.set_timer(change_s, 0)
        else:
            if not self.move_timer_go and self.can_move:
                self.image = self.walk_frames_s[self.cur_frame]
                pygame.time.set_timer(change_s, walk_timer_delay)
                self.move_timer_go = True
        if self.cur_frame == 0 and self.y_speed == -self.speed and not self.attack_btn_cliked and not self.uncontrolled_movement:
            self.cur_frame = 1
        if self.cur_frame == 1 and self.y_speed == self.speed and not self.attack_btn_cliked and not self.uncontrolled_movement:
            self.cur_frame = 0
        if self.cur_frame == 2 and self.x_speed == self.speed and not self.attack_btn_cliked and not self.uncontrolled_movement:
            self.cur_frame = 3
        if self.cur_frame == 3 and self.x_speed == -self.speed and not self.attack_btn_cliked and not self.uncontrolled_movement:
            self.cur_frame = 2
        if not keys[pygame.K_h] and self.attack_btn_cliked and self.sword_anim_count == 0:
            self.attack_btn_cliked = False
            link.last_sword_hit_something = True
            self.show_sword = False
            sword.x = -10000
            sword.y = 10000
            sword.update()
            self.sword_charge_count = 0
            if self.charging is True:
                self.run_spin_attack = True
            self.charging = False

        if self.is_hurting and iterations_count - self.hurt_count == 5:
            self.change_sprite_to_hurt = True if self.change_sprite_to_hurt is False else False
            self.hurt_count = iterations_count
            self.hurt_animation_count += 1

        if keys[pygame.K_h] and self.sword_anim_count == 0 and not self.attack_btn_cliked and self.can_move and self.last_sword_hit_something:
            self.attack_btn_cliked = True
            pygame.time.set_timer(change_sword_anim_timer, 0)
            pygame.time.set_timer(change_sword_anim_timer, int(walk_timer_delay * 0.5))
            change_sword_anim_timer_go = True
            self.show_sword = True
            self.can_move = False
            self.sword_charge_count = 0
            self.y_speed, self.x_speed = 0, 0
            pygame.mixer.Sound.play(random.choice(self.sword_slashs_sounds))
            # ---------------------
            if self.cur_frame == 0:
                self.image = self.sword_swing_frames['down_left']
                sword.image = sword.frames['sword_left']
                sword.y = self.rect.y + self.rect.height * 0.5
                sword.x = self.rect.x + self.rect.width * 0.05 - self.rect.width
            # ---------------------
            elif self.cur_frame == 1:
                self.image = self.sword_swing_frames['up_right']
                sword.image = sword.frames['sword_right']
                sword.y = self.rect.y
                sword.x = self.rect.x + self.rect.width * 0.9
            # ---------------------
            elif self.cur_frame == 2:
                self.image = self.sword_swing_frames['up_left']
                sword.image = sword.frames['sword_up']
                sword.y = self.rect.y - self.rect.height
                sword.x = self.rect.x + self.rect.width * 0.1
            # ---------------------
            elif self.cur_frame == 3:
                self.image = self.sword_swing_frames['up_right_2']
                sword.image = sword.frames['sword_up']
                sword.y = self.rect.y - self.rect.height
                sword.x = self.rect.x + self.rect.width * 0.6
            self.sword_anim_count += 1
            return
        # ---------------------
        self.down_attack()
        self.up_attack()
        self.left_attack()
        self.right_attack()
        if self.sword_anim_count == 3 and self.uncontrolled_movement is True:
            self.uncontrolled_movement = False
        # ---------------------
        if keys[pygame.K_l] and not self.l_clicked:
            if 'shield' in self.items_in_inventory:
                self.l_clicked = True
                if 'shield' in self.taken_items:
                    self.taken_items.remove('shield')
                    self.walk_frames = self.simple_walk_frames.copy()
                    self.walk_frames_s = self.simple_walk_frames_s.copy()
                else:
                    self.taken_items.append('shield')
                    self.walk_frames = self.shield_walk_frames.copy()
                    self.walk_frames_s = self.shield_walk_frames_s.copy()
        if not keys[pygame.K_l]:
            self.l_clicked = False
        if keys[pygame.K_j] and 'shield' in self.taken_items and not self.shield_is_active:
            self.shield_is_active = True
            self.walk_frames = self.active_shield_walk_frames.copy()
            self.walk_frames_s = self.active_shield_walk_frames_s.copy()

            pygame.mixer.Sound.play(self.shield_sounds['raise_shield'])
        elif not keys[pygame.K_j] and 'shield' in self.taken_items:
            self.shield_is_active = False
            self.walk_frames = self.shield_walk_frames.copy()
            self.walk_frames_s = self.shield_walk_frames_s.copy()

        if self.can_move and not self.uncontrolled_movement:
            # print(234)
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                if self.x_speed == 0 and not self.attack_btn_cliked:
                    self.cur_frame = 0
                self.y_speed = self.speed
            elif keys[pygame.K_UP] or keys[pygame.K_w]:
                if self.x_speed == 0 and not self.attack_btn_cliked:
                    self.cur_frame = 1
                self.y_speed = -self.speed
            else:
                self.y_speed = 0
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                if self.y_speed == 0 and not self.attack_btn_cliked:
                    self.cur_frame = 2
                self.x_speed = -self.speed
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                if self.y_speed == 0 and not self.attack_btn_cliked:
                    self.cur_frame = 3
                self.x_speed = self.speed
            else:
                self.x_speed = 0
        link.hitbox.y += link.y_speed
        if sprite_collideany(self, walls, first_rect='hitbox'):
            wall = sprite_collideany(self, walls)[0]
            link.hitbox.y -= link.y_speed
            if self.uncontrolled_movement:
                self.y_speed = 0
        else:
            link.rect.y += link.y_speed
            if self.attack_btn_cliked:
                sword.y += link.y_speed
        link.hitbox.x += link.x_speed
        if sprite_collideany(self, walls, first_rect='hitbox'):
            wall = sprite_collideany(self, walls)[0]
            link.hitbox.x -= link.x_speed
            if self.uncontrolled_movement:
                self.x_speed = 0
        else:
            link.rect.x += link.x_speed
            if self.attack_btn_cliked:
                sword.x += link.x_speed
        if ((link.rect.y + self.rect.height) > height or link.rect.y < 0) and self.uncontrolled_movement:
            link.rect.y -= self.y_speed
            link.hitbox.y -= self.y_speed
        if ((self.rect.x + self.rect.width) > width or self.rect.x < 0) and self.uncontrolled_movement:
            self.rect.x -= self.x_speed
            self.hitbox.x -= self.x_speed

        if sprite_collideany(self, take_items):
            self.picked_item = sprite_collideany(self, take_items)[0]
            self.picked_item.rect.x = self.rect.x + self.picked_item.rect.width * 0.5
            self.picked_item.rect.y = self.rect.y - self.picked_item.rect.height * 1.3
            self.image = self.take_item_frames[random.choice(['one_hand', 'two_hands'])]
            self.can_move = False
            self.pick_item_count = iterations_count
            self.items_in_inventory.append(self.picked_item.name)
            self.taken_items.append(self.picked_item.name)
            sword.x = 10000
            self.sword_charge_count = 0
            play_sound_without_music(self.get_items_sounds['fanfare_item'])
            self.walk_frames = self.shield_walk_frames.copy()
            self.walk_frames_s = self.shield_walk_frames_s.copy()
            self.y_speed = 0
            self.x_speed = 0
            if self.picked_item.name == 'shield':
                inventory.image.blit(inventory.sprites['sword_and_shield'], (2, 2))
        thing_that_means_that_link_collided_with_uncontrol_projectile = False
        if sprite_collideany(self, enemies, first_rect='hitbox'):
            if sprite_collideany(self, enemies, first_rect='hitbox')[0].enemy_type == 'projectile':
                if sprite_collideany(self, enemies, first_rect='hitbox')[0].uncontrol:
                    thing_that_means_that_link_collided_with_uncontrol_projectile = True
        if sprite_collideany(self, enemies, first_rect='hitbox') and self.is_hurting is False and not self.uncontrolled_movement \
                and not thing_that_means_that_link_collided_with_uncontrol_projectile:
            self.is_hurting = True
            if self.image in self.active_shield_walk_frames or self.image in self.active_shield_walk_frames_s:
                is_active_shield = True
            else:
                is_active_shield = False
            self.hurt_count = iterations_count
            self.hurt_timer_count = iterations_count
            self.hurt_sound.play()
            collided_enemies = sprite_collideany(self, enemies, first_rect='hitbox')
            enemy = collided_enemies[0]
            if enemy.enemy_type == 'projectile':
                projectile = True
            else:
                projectile = False
            if self.hitbox.center[1] > enemy.rect.center[1]:
                if is_active_shield and self.cur_frame == 1:
                    self.is_hurting = False
                    for collided_enemy in collided_enemies:
                        collided_enemy.collided_info = ['shield', 'bottom', self.hitbox.collidepoint(enemy.rect.bottomleft),
                                                                        self.hitbox.collidepoint(enemy.rect.bottomright),
                                                                        self.hitbox.collidepoint(enemy.rect.midbottom)]
                if not projectile:
                    self.y_speed = 8
                    if self.hitbox.collidepoint(enemy.rect.bottomleft):
                        self.x_speed = -5
                    elif self.hitbox.collidepoint(enemy.rect.bottomright):
                        self.x_speed = 5
                    elif self.hitbox.collidepoint(enemy.rect.midbottom):
                        self.x_speed = 0
            if self.hitbox.center[1] < enemy.rect.center[1]:
                if is_active_shield and self.cur_frame == 0:
                    self.is_hurting = False
                    for collided_enemy in collided_enemies:
                        collided_enemy.collided_info = ['shield', 'top', self.hitbox.collidepoint(enemy.rect.topleft),
                                                                        self.hitbox.collidepoint(enemy.rect.topright),
                                                                        self.hitbox.collidepoint(enemy.rect.midtop)]
                if not projectile:
                    self.y_speed = -8
                    if self.hitbox.collidepoint(enemy.rect.topleft):
                        self.x_speed = -5
                    elif self.hitbox.collidepoint(enemy.rect.topright):
                        self.x_speed = 5
                    elif self.hitbox.collidepoint(enemy.rect.midtop):
                        self.x_speed = 0
            if self.hitbox.center[0] > enemy.rect.center[0]:
                if is_active_shield and self.cur_frame == 2:
                    self.is_hurting = False
                    for collided_enemy in collided_enemies:
                        collided_enemy.collided_info = ['shield', 'right', self.hitbox.collidepoint(enemy.rect.topright),
                                                                        self.hitbox.collidepoint(enemy.rect.bottomright),
                                                                        self.hitbox.collidepoint(enemy.rect.midright)]
                if not projectile:
                    self.x_speed = 8
                    if self.hitbox.collidepoint(enemy.rect.topright):
                        self.y_speed = -5
                    elif self.hitbox.collidepoint(enemy.rect.bottomright):
                        self.y_speed = 5
                    elif self.hitbox.collidepoint(enemy.rect.midright):
                        self.y_speed = 0
            if self.hitbox.center[0] < enemy.rect.center[0]:
                if is_active_shield and self.cur_frame == 3:
                    self.is_hurting = False
                    for collided_enemy in collided_enemies:
                        collided_enemy.collided_info = ['shield', 'left', self.hitbox.collidepoint(enemy.rect.topleft),
                                                                        self.hitbox.collidepoint(enemy.rect.bottomleft),
                                                                        self.hitbox.collidepoint(enemy.rect.midleft)]
                if not projectile:
                    self.x_speed = -8
                    if self.hitbox.collidepoint(enemy.rect.topleft):
                        self.y_speed = -5
                    elif self.hitbox.collidepoint(enemy.rect.midleft):
                        self.y_speed = 0
                    elif self.hitbox.collidepoint(enemy.rect.bottomleft):
                        self.y_speed = 5
            if self.hitbox.collidepoint(enemy.rect.midbottom):
                if is_active_shield and self.cur_frame == 1:
                    self.is_hurting = False
                self.x_speed = 0
            if self.hitbox.collidepoint(enemy.rect.midtop):
                if is_active_shield and self.cur_frame == 0:
                    self.is_hurting = False
                self.x_speed = 0
            if self.is_hurting:
                if self.hp != 0:
                    self.hp -= 1
                if self.hp == 0:
                    global end
                    end = True

            self.uncontrolled_movement = True
            self.uncontrolled_movement_count = iterations_count

        if (self.hurt_animation_count >= 15 and self.hurt_animation_count % 2 == 0) and self.is_hurting:
            self.is_hurting = False
            self.hurt_animation_count = 0
        if self.attack_btn_cliked and not self.charging:
            self.sword_charge_count += 1

        if iterations_count - self.uncontrolled_movement_count == 15 and self.uncontrolled_movement is True:
            self.uncontrolled_movement = False
            self.y_speed = 0
            self.x_speed = 0


class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, img, scale=6):
        super().__init__(all_sprites, medium_plan, walls)
        self.scale = scale
        self.image = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.rect = self.rect.move(x, y)


class Bush(pygame.sprite.Sprite):
    def __init__(self, x, y, img, scale=6):
        super().__init__(all_sprites, medium_plan, walls)
        self.scale = scale
        self.image = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
        self.full_image = self.image.copy()
        self.width_height = (self.image.get_width(), self.image.get_height())
        self.create()
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.rect = self.rect.move(x, y)

    def create(self):
        self.full_image = self.image.copy()
        self.width_height = (self.image.get_width(), self.image.get_height())
        empty_image = load_image(f'empty_bush.png', path='data/other_sprites')
        self.empty_image = pygame.transform.scale(empty_image,
                                                  (empty_image.get_width() * self.scale,
                                                   empty_image.get_height() * self.scale))

    def update(self):
        sword_collide = False
        if sprite_collideany(self, sword_group):
            sword_collide = True
        if sword_collide and link.last_sword_hit_something:
            self.image = self.empty_image
            result = random.choice(5 * ['heart'] + 5 * ['blue_rupee'] + ['red_rupee'] + 60 * [''])
            if result == 'heart':
                coords = (self.rect.midtop[0], self.rect.center[1] - 6)
            else:
                coords = self.rect.midtop
            if result:
                TakeThing(coords[0] - self.rect.width // 4, coords[1], result)
            self.rect.width, self.rect.height = 0, 0
        if not link.uncontrolled_movement and self.rect.x > width or self.rect.x < 0 or self.rect.y > height or self.rect.y < 0:
            self.image = self.full_image
            self.rect.width, self.rect.height = self.width_height


class Grass(Bush):
    def create(self):
        empty_image = load_image(f'empty_bush.png', path='data/other_sprites')
        self.empty_image = pygame.transform.scale(empty_image,
                                                  (empty_image.get_width() * self.scale,
                                                   empty_image.get_height() * self.scale))
        walls.remove(self)




class PassTile(pygame.sprite.Sprite):
    def __init__(self, x, y, img, scale=6):
        super().__init__(all_sprites, medium_plan)
        self.scale = scale
        self.image = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.rect = self.rect.move(x, y)


class OctoroksBall(pygame.sprite.Sprite):
    def __init__(self, x, y, velocity, mother, scale=6):
        super().__init__(all_sprites, medium_plan, enemies)
        self.scale = scale
        self.enemy_type = 'projectile'
        img = load_image(f'ball.png', path='data/enemies/octorok', colorkey=-1)
        self.image = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
        self.rect = self.image.get_bounding_rect()
        self.rect = self.rect.move(x - self.rect.width, y - self.rect.height)
        self.x_speed, self.y_speed = velocity
        self.collided_count = 0
        self.uncontrol = False
        self.uncontrol_2 = False
        self.mother = mother

    def update(self):
        self.rect = self.rect.move(self.x_speed, self.y_speed)
        if (sprite_collideany(self, walls) or sprite_collideany(self, link_group, second_rect='hitbox')) and not self.uncontrol_2:
            if (sprite_collideany(self, medium_plan)[0] != self.mother
                and sprite_collideany(self, medium_plan)[0] != self) \
                    or sprite_collideany(self, link_group, second_rect='hitbox'):
                something = sprite_collideany(self, medium_plan)[0]
                self.uncontrol_2 = True
                self.collided_count = iterations_count
                self.x_speed, self.y_speed = -self.x_speed // 4, -6
        if iterations_count - self.collided_count == 10 and self.uncontrol_2:
            self.uncontrol = True
            self.x_speed = 0
            self.y_speed = 10
        if iterations_count - self.collided_count == 23 and self.uncontrol:
            self.kill()
        if self.rect.center[0] > width or self.rect.center[1] > height\
                or self.rect.center[0] < 0 or self.rect.center[1] < 0:
            self.kill()


class Octorok(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=6, speed=0.3 * game_speed):
        super().__init__(all_sprites, medium_plan, enemies)
        self.scale = scale
        self.enemy_type = 'enemy'
        self.y_speed, self.x_speed = speed, speed
        self.old_y_speed, self.old_x_speed = speed, speed
        self.cur_frame = 0
        self.walk_frames = []
        self.walk_frames_s = []
        self.hurt_walk_frames = []
        self.hurt_walk_frames_s = []
        self.walk_animation_count = iterations_count
        self.choice_about_go_count = 0
        self.sprites_create()
        self.image = self.walk_frames[0]
        self.rect = self.image.get_bounding_rect()
        self.rect = self.rect.move(x, y)
        self.old_x_y = [self.rect.x, self.rect.y]
        self.is_walking = False
        self.change_state_count = random.randint(5, 10)
        self.uncontrolled_movement = False
        self.uncontrolled_movement_count = 0
        self.collided_info = [False]
        self.hp = 1
        self.hurted_with_sword = False
        self.trajectory_dep = {'sword_circle_botton_left': (-12, 12), 'sword_circle_up_left': (-12, -12),
                               'sword_circle_up_right': (12, -12), 'sword_circle_botton_right': (12, 12)}
        self.is_hurting = False
        self.hurting_count = 0
        self.stop_hurting_count = 0
        self.hurt_image = False

    def sprites_create(self):
        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data/enemies/octorok/simple_walk', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data/enemies/octorok/simple_walk', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.walk_frames.append(img)
            self.walk_frames_s.append(img_s)

        for num in range(1, 5):
            img = load_image(f'walk_{num}.png', path='data/enemies/octorok/hurt_simple_walk', colorkey=-1)
            img = pygame.transform.scale(img, (img.get_width() * self.scale, img.get_height() * self.scale))
            img_s = load_image(f'walk_{num}_s.png', path='data/enemies/octorok/hurt_simple_walk', colorkey=-1)
            img_s = pygame.transform.scale(img_s, (img_s.get_width() * self.scale, img_s.get_height() * self.scale))
            self.hurt_walk_frames.append(img)
            self.hurt_walk_frames_s.append(img_s)

    def update(self):
        if self.rect.x < 0 or self.rect.y < 0 or self.rect.x > width or self.rect.y > height:
            self.rect.x, self.rect.y = self.old_x_y
        if self.rect.x > -2 and self.rect.y > -2 and self.rect.x < width and self.rect.y < height:
            if self.image in self.hurt_walk_frames:
                self.image = self.walk_frames[self.cur_frame]
            elif self.image in self.hurt_walk_frames_s:
                self.image = self.walk_frames_s[self.cur_frame]

            if self.collided_info[0]:
                self.uncontrolled_movement = True
                self.uncontrolled_movement_count = iterations_count
                self.is_walking = False
                if self.collided_info[0] == 'shield':
                    if self.collided_info[1] == 'bottom':
                        self.y_speed = -12
                        if self.collided_info[2]:
                            self.x_speed = 3
                        elif self.collided_info[3]:
                            self.x_speed = -3
                        elif self.collided_info[4]:
                            self.x_speed = 0
                    if self.collided_info[1] == 'top':
                        self.y_speed = 12
                        if self.collided_info[2]:
                            self.x_speed = 3
                        elif self.collided_info[3]:
                            self.x_speed = -3
                        elif self.collided_info[4]:
                            self.x_speed = 0
                    if self.collided_info[1] == 'right':
                        self.x_speed = -12
                        if self.collided_info[2]:
                            self.y_speed = 3
                        elif self.collided_info[3]:
                            self.y_speed = -3
                        elif self.collided_info[4]:
                            self.y_speed = 0
                    if self.collided_info[1] == 'left':
                        self.x_speed = 12
                        if self.collided_info[2]:
                            self.y_speed = 3
                        elif self.collided_info[3]:
                            self.y_speed = -3
                        elif self.collided_info[4]:
                            self.y_speed = 0

                elif self.collided_info[0] == 'sword' and not self.hurted_with_sword:
                    image_name = self.collided_info[1]
                    sw = self.collided_info[2]
                    if image_name == 'sword_up' or image_name == 'charge_sword_up':
                        self.y_speed = -15
                        self.x_speed = 4 if sw.rect.center[0] < self.rect.center[0] else -4
                    elif image_name == 'sword_down' or image_name == 'charge_sword_down':
                        self.y_speed = 15
                        self.x_speed = 4 if sw.rect.center[0] < self.rect.center[0] else -4
                    elif image_name == 'sword_left' or image_name == 'charge_sword_left':
                        self.y_speed = 4 if sw.rect.center[1] < self.rect.center[1] else -4
                        self.x_speed = -15
                    elif image_name == 'sword_right' or image_name == 'charge_sword_right':
                        self.y_speed = 4 if sw.rect.center[1] < self.rect.center[1] else -4
                        self.x_speed = 15
                    else:
                        self.x_speed, self.y_speed = self.trajectory_dep[image_name]
                    self.hp -= 1
                    self.is_hurting = True
                    self.hurting_count = iterations_count
                    self.stop_hurting_count = 0
                self.collided_info = [False]
                self.hurted_with_sword = True

            if iterations_count - self.uncontrolled_movement_count >= 10:
                self.uncontrolled_movement = False
                self.hurted_with_sword = False
                self.x_speed = self.old_x_speed
                self.y_speed = self.old_y_speed
            if not self.uncontrolled_movement:
                x_difference = abs(link.hitbox.center[0] - self.rect.center[0])
                y_difference = abs(link.hitbox.center[1] - self.rect.center[1])
                y_speed, x_speed = 0, 0
                where_is_link = ''
                direction_sp = []
                fire_sp = [False]
                if link.hitbox.center[0] < self.rect.center[0]:
                    if x_difference > y_difference:
                        direction_sp += [2, 2, 2, 2, 2, 1, 0]
                    else:
                        direction_sp += [2, 1, 0]
                    where_is_link = 'left'
                elif link.hitbox.center[0] > self.rect.center[0]:
                    if x_difference > y_difference:
                        direction_sp += [3, 3, 3, 3, 3, 1, 0]
                    else:
                        direction_sp += [3, 1, 0]
                    where_is_link = 'right'
                if link.hitbox.center[1] > self.rect.center[1]:
                    if y_difference > x_difference:
                        direction_sp += [0, 0, 0, 0, 0, 3, 2]
                    else:
                        direction_sp += [0, 2, 3]
                    if y_difference >= x_difference:
                        where_is_link = 'bottom'
                elif link.hitbox.center[1] < self.rect.center[1]:
                    if y_difference > x_difference:
                        direction_sp += [1, 1, 1, 1, 1,  3, 2]
                    else:
                        direction_sp += [1, 2, 3]
                    if y_difference >= x_difference:
                        where_is_link = 'top'
                if iterations_count - self.choice_about_go_count >= self.change_state_count:
                    self.is_walking = random.choice([True, True, False])
                    self.cur_frame = random.choice(direction_sp)
                    if self.cur_frame == 2 and where_is_link == 'left':
                        fire_sp += [True]
                    elif self.cur_frame == 3 and where_is_link == 'right':
                        fire_sp += [True]
                    elif self.cur_frame == 0 and where_is_link == 'bottom':
                        fire_sp += [True]
                    elif self.cur_frame == 1 and where_is_link == 'top':
                        fire_sp += [True]
                    self.fire = random.choice(fire_sp)
                    if self.fire:
                        self.is_walking = False
                    if self.fire and self.cur_frame == 0:
                        OctoroksBall(self.rect.midbottom[0], self.rect.midbottom[1], (0, 2 * self.scale), self, scale=self.scale)
                    elif self.fire and self.cur_frame == 1:
                        OctoroksBall(self.rect.midtop[0], self.rect.midtop[1], (0, -2 * self.scale), self, scale=self.scale)
                    elif self.fire and self.cur_frame == 2:
                        OctoroksBall(self.rect.midleft[0], self.rect.midleft[1], (-2 * self.scale, 0), self, scale=self.scale)
                    elif self.fire and self.cur_frame == 3:
                        OctoroksBall(self.rect.midright[0], self.rect.midright[1], (2 * self.scale, 0), self, scale=self.scale)
                    self.image = self.walk_frames[self.cur_frame]
                    self.choice_about_go_count = iterations_count
                    self.change_state_count = random.randint(40, 100)

                if self.is_walking:
                    if self.cur_frame == 0:
                        y_speed = self.y_speed
                    elif self.cur_frame == 1:
                        y_speed = -self.y_speed
                    elif self.cur_frame == 2:
                        x_speed = -self.x_speed
                    elif self.cur_frame == 3:
                        x_speed = self.x_speed

                if iterations_count - self.walk_animation_count >= 10:
                    if self.is_walking:
                        if self.image == self.walk_frames[self.cur_frame]:
                            self.image = self.walk_frames_s[self.cur_frame]
                        elif self.image == self.walk_frames_s[self.cur_frame]:
                            self.image = self.walk_frames[self.cur_frame]

                    self.walk_animation_count = iterations_count

            else:
                x_speed, y_speed = self.x_speed, self.y_speed

            self.rect = self.rect.move(x_speed, y_speed)
            if (self.rect.x + self.rect.width) > width or self.rect.x < 0 or (self.rect.y + self.rect.height) > height or self.rect.y < 0:
                self.rect = self.rect.move(-x_speed, -y_speed)
                self.is_walking = False
            if sprite_collideany(self, walls):
                wall = sprite_collideany(self, walls)[0]
                self.rect = self.rect.move(-x_speed, -y_speed)
                self.is_walking = False
                self.rect.y += y_speed
                if sprite_collideany(self, walls) and self.uncontrolled_movement:
                    self.y_speed = 0
                self.rect.y -= y_speed
                self.rect.x += x_speed
                if sprite_collideany(self, walls) and self.uncontrolled_movement:
                    self.x_speed = 0
                self.rect.x -= x_speed

            if self.stop_hurting_count >= 5 and self.stop_hurting_count % 2 == 0 and self.is_hurting:
                self.is_hurting = False
                self.stop_hurting_count = 0
                if self.hp <= 0:
                    die_sound.play()
                    result = random.choice(['heart'] + 30 * ['blue_rupee'] + 3 * ['red_rupee'] + 20 * [''])
                    if result == 'heart':
                        coords = (self.rect.midtop[0], self.rect.center[1] - 6)
                    else:
                        coords = self.rect.midtop
                    if result:
                        TakeThing(coords[0] - self.rect.width // 4, coords[1], result)
                    self.kill()
            if self.image in self.walk_frames and self.hurt_image:
                self.image = self.hurt_walk_frames[self.cur_frame]
            elif self.image in self.walk_frames_s and self.hurt_image:
                self.image = self.hurt_walk_frames_s[self.cur_frame]
            if iterations_count - self.hurting_count == 3 and self.is_hurting:
                self.hurt_image = True if self.hurt_image is False else False
                # print(self.hurt_image)
                self.hurting_count = iterations_count
                self.stop_hurting_count += 1


class TakeItem(pygame.sprite.Sprite):
    def __init__(self, x, y, path, name, name_of_item, scale=6):
        super().__init__(all_sprites, medium_plan, take_items)
        self.name = name_of_item
        img = load_image(name, path=path, colorkey=-1)
        self.image = pygame.transform.scale(img, (img.get_width() * scale, img.get_height() * scale))
        self.rect = self.image.get_bounding_rect()
        self.rect = self.rect.move(x, y)


class Sword(pygame.sprite.Sprite):
    def __init__(self, x, y, scale=6):
        super().__init__(sword_group)
        self.scale = scale
        self.x, self.y = x, y
        self.cur_frame = 0
        self.frames = {}
        for root, dirs, files in os.walk("data/sword"):
            for filename in files:
                if 'circle' in filename:
                    img = load_image(filename, path='data/sword', colorkey=-1, color=(0, 57, 115, 255))
                else:
                    img = load_image(filename, path='data/sword', colorkey=-1, color=(0, 57, 115, 255))
                if 'charge' in filename:
                    if 'down' in filename or 'up' in filename:
                        self.frames[filename[:-4]] = pygame.transform.scale(img, (6 * self.scale,
                                                                                  16 * self.scale))
                    else:
                        self.frames[filename[:-4]] = pygame.transform.scale(img, (16 * self.scale,
                                                                                  7 * self.scale))
                else:
                    self.frames[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * self.scale,
                                                                              img.get_height() * self.scale))
        self.image = self.frames[list(self.frames.keys())[0]]
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.rect = self.rect.move(self.x, self.y)
        self.bush_cut_sound = pygame.mixer.Sound(f"data/sounds/other_sounds/bush_cat.wav")
        self.bush_cut_sound.set_volume(0.1)
        self.bush_count = -5

    def get_image_name(self):
        for key in self.frames.keys():
            if self.frames[key] == self.image:
                return key

    def update(self):
        image_name = self.get_image_name()
        self.rect = pygame.Rect(0, 0, self.image.get_width(), self.image.get_height())
        self.rect = self.rect.move(self.x, self.y)
        collided_enemies = sprite_collideany(self, enemies)
        for enemy in collided_enemies:
            if enemy.enemy_type != 'projectile':
                if link.last_sword_hit_something is False:
                    link.last_sword_hit_something = True
                    # link.attack_btn_cliked = False
                    link.show_sword = False
                    sword.x = -10000
                    sword.y = 10000
                    sword.update()
                    link.sword_charge_count = 0
                    if link.charging is True:
                        link.run_spin_attack = True
                    link.charging = False
                enemy.collided_info = ['sword', image_name, self]
        if sprite_collideany(self, all_sprites) and self.bush_count == -5 and link.last_sword_hit_something:
            for sprite in sprite_collideany(self, all_sprites):
                if type(sprite).__name__ == 'Bush' or type(sprite).__name__ == 'Grass':
                    self.bush_cut_sound.play()
                    self.bush_count = 0
                    break
        if self.bush_count > -5:
            self.bush_count += 1
        if self.bush_count == 15:
            self.bush_count = -5

take_things_images = {}
for root, dirs, files in os.walk("data/take_things"):
    for filename in files:
        img = load_image(filename, path='data/take_things', colorkey=-1)
        take_things_images[filename[:-4]] = pygame.transform.scale(img, (img.get_width() * scale,
                                                                                   img.get_height() * scale))
get_rupee_sound = pygame.mixer.Sound(f"data/sounds/other_sounds/get_rupee.wav")
get_rupee_sound.set_volume(0.15)

get_item_sound = pygame.mixer.Sound(f"data/sounds/other_sounds/get_item.wav")
get_item_sound.set_volume(0.15)


class TakeThing(pygame.sprite.Sprite):
    def __init__(self, x, y, type_name, scale=6):
        super().__init__(all_sprites, medium_plan, take_things_group)
        self.scale = scale
        self.type = type_name
        self.image = take_things_images[type_name]
        self.jump_count = iterations_count
        self.is_jump = True
        self.fall_count = iterations_count
        self.is_fall = False
        self.live_count = iterations_count
        self.can_be_taken = False
        self.duration = 6
        self.is_flashing = False
        self.flash_count = iterations_count
        self.rect = self.image.get_bounding_rect()
        self.rect = self.rect.move(x, y)
        self.y_speed = -3
        self.x_speed = 0

    def update(self):
        if iterations_count - self.live_count == 10:
            self.can_be_taken = True
        if self.can_be_taken and (sprite_collideany(self, link_group) or sprite_collideany(self, sword_group)):
            if self.type == 'heart':
                link.hp += 2
                get_item_sound.play()
                if link.hp > link.max_hp:
                    link.hp = link.max_hp
            elif self.type == 'blue_rupee':
                link.rupee += 1
                get_rupee_sound.play()
            elif self.type == 'red_rupee':
                link.rupee += 20
                get_rupee_sound.play()
            if link.rupee > 999:
                link.rupee = 999
            self.kill()

        if self.is_jump and not self.is_fall:
            if iterations_count - self.jump_count == self.duration:
                self.jump_count = iterations_count
                self.is_jump = False
                if self.duration > 3:
                    self.is_fall = True
                self.y_speed = -self.y_speed
            self.rect.y += self.y_speed
        elif self.is_fall and not self.is_jump:
            if iterations_count - self.jump_count == self.duration:
                self.jump_count = iterations_count
                self.duration -= 2
                if self.duration > 3:
                    self.is_jump = True
                self.is_fall = False
                self.y_speed = -self.y_speed
            self.rect.y += self.y_speed

        if not self.is_flashing and iterations_count - self.flash_count == 400:
            self.is_flashing = True
            self.flash_count = iterations_count
        if self.is_flashing and iterations_count - self.flash_count == 4:
            if self.image == take_things_images[self.type]:
                self.image = take_things_images['empty_image']
            elif self.image == take_things_images['empty_image']:
                self.image = take_things_images[self.type]
            self.flash_count = iterations_count
        if iterations_count - self.live_count == 500:
            self.kill()
        if self.rect.center[0] > width or self.rect.center[1] > height\
                or self.rect.center[0] < 0 or self.rect.center[1] < 0:
            self.kill()


def terminate():
    pygame.quit()
    sys.exit()


def start_screen():
    pygame.mixer.music.load('data/music/Main_Theme.wav')
    pygame.mixer.music.set_volume(0.2)
    pygame.mixer.music.play(-1)
    fon = pygame.transform.scale(load_image('start_and_end_game/start_game_title.png'), (width, height))
    screen.blit(fon, (0, 0))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                return
        pygame.display.flip()
        clock.tick(60)


old_height = height
change_sword_sprite = False


def game_over_screen():
    global play
    global total_attempts
    total_attempts += 1
    try:
        pygame.mixer.music.load('data/music/Game_Over.wav')
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
    except Exception:
        return
    fon1 = pygame.transform.scale(load_image('start_and_end_game/end_game_title_continue.png'), (width, old_height))
    fon2 = pygame.transform.scale(load_image('start_and_end_game/end_game_title_quit.png'), (width, old_height))
    direction = 'continue'
    while True:
        if direction == 'continue':
            screen.blit(fon1, (0, 0))
        elif direction == 'quit':
            screen.blit(fon2, (0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if direction == 'continue':
                        return
                    elif direction == 'quit':
                        play = False
                        return
                elif event.key in [pygame.K_DOWN, pygame.K_UP, pygame.K_w, pygame.K_s]:
                    direction = 'continue' if direction == 'quit' else 'quit'
        pygame.display.flip()
        clock.tick(60)


def win_screen():
    global game_over
    global win
    global play
    global fun_mode
    global fun_mode_turned
    global went_another_screen
    global total_attempts
    # pygame.mixer.music.load('data/music/Main_Theme.wav')
    # pygame.mixer.music.set_volume(0.2)
    screen.fill((0, 0, 0))
    pygame.mixer.music.stop()
    intro_text = [f"Total attemps: {total_attempts}",
                  f"Total rupees: {link.rupee}",
                  "Press enter to play again",
                  "Press space to quit",
                  "Thanks for playing",
                  "you can always turn on or turn off hard-fun",
                  "mode just press 8.",
                  "Even when you haven't win the game",
                  "Autor: MDULMIEV",
                  "LUTSHE B NA VITU SDELAL"]
    text_size = 22
    if fun_mode is True and not fun_mode_turned and not went_another_screen:
        intro_text = ["WOOOOOOOOOOOOOW You completed",
                      "hard-fun mode",
                      "My respect and congratulations hero",
                      f"Total attemps: {total_attempts}",
                      f"Total rupees: {link.rupee}"]
        text_size = 30
    if fun_mode is True and not fun_mode_turned and not went_another_screen \
            and 'shield' not in link.items_in_inventory:
        intro_text = ["WOOOOOOOOOOOOOW You completed",
                      "hard-fun mode without shield",
                      "My respect and congratulations hero X 2",
                      f"Total attemps: {total_attempts}",
                      f"Total rupees: {link.rupee}"]
        text_size = 30
    total_attempts = 0
    img = load_image('start_and_end_game/win_screen.png')
    fon = pygame.transform.scale(img, (width, img.get_height() * scale * 0.7))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font('data/font/First_Zelda.ttf', text_size)
    text_coord = 550
    plus_y = 1900
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 5
        # plus_y += 50
        # intro_rect.y += plus_y
        intro_rect.top = text_coord
        intro_rect.x = 50
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    play = False
                    return
                elif event.key == pygame.K_RETURN:
                    game_over = True
                    win = False
                    return
        pygame.display.flip()
        clock.tick(60)


def story_and_rules_screen():
    # pygame.mixer.music.load('data/music/Main_Theme.wav')
    # pygame.mixer.music.set_volume(0.2)
    screen.fill((0, 0, 0))
    # pygame.mixer.music.stop()
    intro_text = ["Koholint Island has been",
                  "invaded by monsters",
                  "Destroy them all to ",
                  "save the inhabitants",
                  "who have taken ",
                  "refuge in their homes",
                  "",
                  "Press H to attack with a sword",
                  "Press J to use a shield",
                  "Press L to take off ",
                  "or put on shield",
                  "Press 1 or 2 to change",
                  "volume of game",
                  "Press 3 to restart",
                  "or quit the game"]
    #img = load_image('start_and_end_game/win_screen.png')
    #fon = pygame.transform.scale(img, (width, img.get_height() * scale * 0.7))
    # screen.blit(fon, (0, 0))
    font = pygame.font.Font('data/font/First_Zelda.ttf', 34)
    text_coord = 40
    plus_y = 80
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 10
        # plus_y += 50
        # intro_rect.y += plus_y
        intro_rect.top = text_coord
        intro_rect.x = 50
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN:
                return
        pygame.display.flip()
        clock.tick(60)

end = False


def spawn_mosters():
    for _ in range(20):
        while True:
            octorok = Octorok(random.randint(5, width - 100), random.randint(5, height - 100))
            if sprite_collideany(octorok, walls) or sprite_collideany(octorok, link_group):
                octorok.kill()
            else:
                break

fun_mode = False
fun_mode_turned = False
went_another_screen = False
total_attempts = 0


def start_game():
    global fun_mode
    global fun_mode_turned
    global end
    global win
    global game_over
    global old_height
    global link
    global sword
    global change_sword_sprite
    global inventory
    global change_sword_anim_timer_go
    global world
    global iterations_count
    global play
    global get_rupee_sound
    global get_item_sound
    global height
    global went_another_screen
    went_another_screen = False
    fun_mode_turned = False
    # fun_mode = False
    get_rupee_sound.set_volume(0.15)
    get_item_sound.set_volume(0.15)
    for i in all_sprites:
        i.kill()
    for i in medium_plan:
        i.kill()
    for i in walls:
        i.kill()
    for i in sword_group:
        i.kill()
    for i in link_group:
        i.kill()
    for i in take_items:
        i.kill()
    for i in enemies:
        i.kill()
    for i in something_group:
        i.kill()
    for i in take_things_group:
        i.kill()

    world = World('world_map.tmx', [100000], [202, 323, 57, 50, 51, 177, 178, 201, 254, 87, 111, 301, 325,
                                              294, 56, 6, 5, 4, 28, 29, 30, 49, 52, 1, 2, 3, 25, 26, 27, 53, 54, 55,
                                              153, 154, 7, 8, 9, 31, 32, 33, 265, 266, 267, 289, 291, 429, 430, 313,
                                              314, 315, 22, 23, 24, 46, 47, 48, 209, 163, 298, 340, 341,
                                              270, 271, 275, 276, 268, 269, 292, 293, 59])
    height = old_height

    change_s = pygame.USEREVENT + 1
    pygame.time.set_timer(change_s, 0)
    change_sword_anim_timer = pygame.USEREVENT + 1
    pygame.time.set_timer(change_sword_anim_timer, 0)
    change_sword_anim_timer_go = False
    iterations_count = 0
    world.render(screen)
    inventory = Inventory()
    height = height - inventory.rect.height
    height += 40 - (height % 40)
    camera = Camera()
    clock = pygame.time.Clock()
    can_update = True
    can_update_count = -500
    can_update_an_count = 20
    camera_where = ''
    camera.update(-2015, -1630)
    for sprite in all_sprites:
        if sprite in enemies:
            sprite.old_x_y[0] += -2015
            sprite.old_x_y[1] += -1630
        camera.apply(sprite)
    # link = Link(list(walls)[0].rect.x + 70, list(walls)[0].rect.y + 50, scale=scale, speed=0.6 * game_speed)
    link = Link(475, 490, scale=scale, speed=0.6 * game_speed)
    Octorok(link.rect.x + width // 2 + 100, link.rect.y)
    Octorok(link.rect.x + width, link.rect.y - height // 2 - 20)
    Octorok(link.rect.x + width + 290, link.rect.y - 100)
    Octorok(link.rect.x, link.rect.y - height - height // 2)
    Octorok(link.rect.x - 2 * width + 50, link.rect.y - height - 200)
    Octorok(link.rect.x - width // 3 + 35, link.rect.y + height)
    shield_item = TakeItem(link.rect.x + 10, link.rect.y - 300, 'data/items', 'shield.png', 'shield', scale=scale)
    sword = Sword(-10000, 10000, scale=scale)
    # Octorok(link.rect.x + width, link.rect.y)
    # Octorok(300, -600)
    running = True

    def change_all_game_volume(num):
        pygame.mixer.music.set_volume(pygame.mixer.music.get_volume() + num)
        die_sound.set_volume(die_sound.get_volume() + num)
        for index in range(len(link.sword_slashs_sounds)):
            link.sword_slashs_sounds[index].set_volume(link.sword_slashs_sounds[index].get_volume() + num)
        for key in link.shield_sounds.keys():
            link.shield_sounds[key].set_volume(link.shield_sounds[key].get_volume() + num)
        for key in link.get_items_sounds.keys():
            link.get_items_sounds[key].set_volume(link.get_items_sounds[key].get_volume() + num)
        sword.bush_cut_sound.set_volume(sword.bush_cut_sound.get_volume() + num)
        get_rupee_sound.set_volume(sword.bush_cut_sound.get_volume() + num)
        get_item_sound.set_volume(sword.bush_cut_sound.get_volume() + num)

    def hide_sword():
        link.attack_btn_cliked = False
        link.last_sword_hit_something = True
        link.show_sword = False
        sword.x = -10000
        sword.y = 10000
        sword.update()
        link.sword_charge_count = 0
        if link.charging is True:
            link.run_spin_attack = True
        link.charging = False

    # pygame.mixer.music.load('data/music/Overworld.wav')
    # pygame.mixer.music.set_volume(0.5)
    # pygame.mixer.music.play(-1)
    end = False
    while running:
        iterations_count += 1
        change_sword_sprite = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                play = False
                running = False
            if event.type == change_s:
                link.change_sprite = True if link.change_sprite is False else False
            if event.type == change_sword_anim_timer:
                change_sword_sprite = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    change_all_game_volume(-0.05)
                elif event.key == pygame.K_2:
                    change_all_game_volume(0.05)
                elif event.key == pygame.K_3:
                    return
                elif event.key == pygame.K_8:
                    fun_mode = True if fun_mode is False else False
                    if fun_mode is False:
                        fun_mode_turned = True
        if end:
            return
        screen.fill(pygame.Color('yellow'))
        # walls.draw(screen)
        if link.rect.x + link.rect.width > width and can_update and can_update_an_count == 20:
            camera.update(-width / 40, 0)
            can_update, can_update_count, can_update_an_count, camera_where = False, iterations_count, 0, 'right'
            link.can_move = False
            link.x_speed, link.y_speed = 0, 0
            hide_sword()
        elif link.rect.x < 0 and can_update and can_update_an_count == 20:
            camera.update(width / 40, 0)
            can_update, can_update_count, can_update_an_count, camera_where = False, iterations_count, 0, 'left'
            link.can_move = False
            link.x_speed, link.y_speed = 0, 0
            hide_sword()
        elif link.rect.y + link.rect.height - 20 > height and can_update and can_update_an_count == 20: #to fix bag 20 -> 30
            camera.update(0, -height / 40)
            can_update, can_update_count, can_update_an_count, camera_where = False, iterations_count, 0, 'down'
            link.can_move = False
            link.x_speed, link.y_speed = 0, 0
            hide_sword()
        elif link.rect.y < 0 and can_update and can_update_an_count == 20:
            camera.update(0, height / 40)
            can_update, can_update_count, can_update_an_count, camera_where = False, iterations_count, 0, 'up'
            link.can_move = False
            link.x_speed, link.y_speed = 0, 0
            hide_sword()
        if iterations_count - can_update_count == 1 and not can_update:
            for sprite in all_sprites:
                camera.apply(sprite)
            if camera_where == 'up':
                link.rect.y += height / 44
                link.hitbox.y += height / 44
            elif camera_where == 'down':
                link.rect.y -= height / 45
                link.hitbox.y -= height / 45
            elif camera_where == 'right':
                link.rect.x -= width / 46
                link.hitbox.x -= width / 46
            elif camera_where == 'left':
                link.rect.x += width / 44
                link.hitbox.x += width / 44
            # camera.apply(link)
            can_update_count = iterations_count
            can_update_an_count += 1
        if can_update_an_count == 30 and not can_update:
            for enemy in enemies:
                if type(enemy).__name__ == 'Octorok':
                    if camera_where == 'up':
                        enemy.old_x_y[1] += height
                    elif camera_where == 'down':
                        enemy.old_x_y[1] -= height
                    elif camera_where == 'left':
                        enemy.old_x_y[0] += width
                    elif camera_where == 'right':
                        enemy.old_x_y[0] -= width
        if can_update_an_count == 40 and not can_update:
            can_update = True
            link.can_move = True
            can_update_count = -500
            can_update_an_count = 20
            if fun_mode is False:
                went_another_screen = True
            if fun_mode:
                spawn_mosters()
        link.update(change_sprite=link.change_sprite)
        link.change_simple_frame_to_hurt_and_back()
        # sword_group.update()
        if can_update:
            all_sprites.update()

        # print(inventory.rect.x, inventory.rect.y)
        # all_sprites.draw(screen)
        medium_plan.draw(screen)
        if link.show_sword:
            sword_group.update()
            sword_group.draw(screen)
        link_group.draw(screen)
        something_group.update()
        something_group.draw(screen)
        # pygame.draw.rect(screen, pygame.Color('black'), link.hitbox)
        # pygame.draw.rect(screen, pygame.Color('black'), stone.rect)
        # pygame.draw.rect(screen, pygame.Color('black'), stone_2.rect)
        # pygame.draw.rect(screen, pygame.Color('black'), sword.rect)
        # pygame.draw.rect(screen, pygame.Color('black'), octorok.rect)
        pygame.display.flip()
        clock.tick(60)
        # if link.hp == 0:
            # game_over_screen()
        if len(enemies) == 0:
            game_over = False
            win = True
            return
    pygame.quit()


clock = pygame.time.Clock()
story_and_rules_screen()
start_screen()

all_sprites = pygame.sprite.Group()
medium_plan = pygame.sprite.Group()
walls = pygame.sprite.Group()
sword_group = pygame.sprite.Group()
link_group = pygame.sprite.Group()
take_items = pygame.sprite.Group()
enemies = pygame.sprite.Group()
something_group = pygame.sprite.Group()
take_things_group = pygame.sprite.Group()


play = True
game_over = True
win = False
while play:
    try:
        pygame.mixer.music.load('data/music/Overworld.wav')
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)
    except Exception:
        pass
    start_game()
    if game_over:
        game_over_screen()
    if win:
        win_screen()
# inventory = Inventory()
# camera = Camera()
# height = height - inventory.rect.height
# height += 40 - (height % 40)
# link = Link(71, 51, scale=scale, speed=0.6 * game_speed)
# sword = Sword(-10000, 10000, scale=scale)
# change_sword_sprite = False
# start_game()

#inventory.rect.height += 40 - (height % 40)
#Wall(300, 300, 'data/walls', 'stone.png', scale=scale)
#Wall(600, 500, 'data/walls', 'stone.png', scale=scale)
#Wall(200, 500, 'data/walls', 'stone.png', scale=scale)
#Wall(400, 300, 'data/walls', 'stone.png', scale=scale)
#Wall(400, 700, 'data/walls', 'stone.png', scale=scale)
#Wall(400, -300, 'data/walls', 'stone.png', scale=scale)
#Wall(400, -1300, 'data/walls', 'stone.png', scale=scale)
#Wall(400, -2300, 'data/walls', 'stone.png', scale=scale)
#stone = Wall(1200, 700, 'data/walls', 'stone.png', scale=scale)
#Wall(400, 1500, 'data/walls', 'stone.png', scale=scale)

#octorok = Octorok(400, 500)
#Octorok(100, 200)
#Octorok(300, -200)
#Octorok(300, -1200)
#for _ in range(0):
    #Octorok(random.randint(1, width - octorok.rect.width), random.randint(1, height - octorok.rect.height))
#shield_item = TakeItem(300, 100, 'data/items', 'shield.png', 'shield', scale=scale)




