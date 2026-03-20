#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
坦克大战小游戏
===============
使用Python + Tkinter开发的经典坦克大战游戏

依赖安装：
    pip install pygame

文件结构：
    tank_battle.py          - 主程序文件
    tank_high_score.txt     - 最高分记录文件（自动创建）
    shoot.wav               - 发射子弹音效（可选）
    explosion.wav           - 击中敌人音效（可选）
    game_over.wav           - 游戏结束音效（可选）

操作说明：
    方向键 ↑↓←→  - 控制坦克移动
    空格键        - 发射子弹 / 暂停游戏
    P键          - 暂停/继续游戏

作者：AI Assistant
日期：2024
"""

import tkinter as tk
from tkinter import messagebox
import random
import math
import os

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("提示：未安装pygame模块，游戏将以静音模式运行。")
    print("安装命令：pip install pygame")


class SoundManager:
    """音效管理类 - 负责游戏音效的加载和播放"""
    
    def __init__(self):
        self.enabled = PYGAME_AVAILABLE
        self.sounds = {}
        
        if self.enabled:
            try:
                pygame.mixer.init()
                self._load_sounds()
            except Exception as e:
                print(f"音效初始化失败：{e}")
                self.enabled = False
    
    def _load_sounds(self):
        """加载所有音效文件，缺失时自动跳过"""
        sound_files = {
            'shoot': 'shoot.wav',
            'explosion': 'explosion.wav',
            'game_over': 'game_over.wav'
        }
        
        for name, filename in sound_files.items():
            filepath = os.path.join(os.path.dirname(__file__), filename)
            if os.path.exists(filepath):
                try:
                    self.sounds[name] = pygame.mixer.Sound(filepath)
                except Exception as e:
                    print(f"加载音效 {filename} 失败：{e}")
    
    def play(self, sound_name):
        """播放指定音效"""
        if self.enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass


class Tank:
    """坦克基类 - 定义坦克的基本属性和行为"""
    
    def __init__(self, canvas, x, y, color, direction='up', size=30):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = color
        self.direction = direction
        self.size = size
        self.speed = 3
        self.alive = True
        self.body_id = None
        self.turret_id = None
        self._draw()
    
    def _draw(self):
        """绘制坦克"""
        self._clear()
        half = self.size // 2
        
        if self.direction == 'up':
            points = [
                self.x - half, self.y + half,
                self.x - half // 2, self.y - half,
                self.x + half // 2, self.y - half,
                self.x + half, self.y + half
            ]
            turret_points = [
                self.x - 3, self.y,
                self.x, self.y - half - 8,
                self.x + 3, self.y
            ]
        elif self.direction == 'down':
            points = [
                self.x - half, self.y - half,
                self.x + half, self.y - half,
                self.x + half // 2, self.y + half,
                self.x - half // 2, self.y + half
            ]
            turret_points = [
                self.x - 3, self.y,
                self.x, self.y + half + 8,
                self.x + 3, self.y
            ]
        elif self.direction == 'left':
            points = [
                self.x + half, self.y - half,
                self.x + half, self.y + half,
                self.x - half, self.y + half // 2,
                self.x - half, self.y - half // 2
            ]
            turret_points = [
                self.x, self.y - 3,
                self.x - half - 8, self.y,
                self.x, self.y + 3
            ]
        else:
            points = [
                self.x - half, self.y - half,
                self.x + half, self.y - half // 2,
                self.x + half, self.y + half // 2,
                self.x - half, self.y + half
            ]
            turret_points = [
                self.x, self.y - 3,
                self.x + half + 8, self.y,
                self.x, self.y + 3
            ]
        
        self.body_id = self.canvas.create_polygon(
            points, fill=self.color, outline='black', width=2
        )
        self.turret_id = self.canvas.create_polygon(
            turret_points, fill='gray', outline='black', width=1
        )
    
    def _clear(self):
        """清除坦克图形"""
        if self.body_id:
            self.canvas.delete(self.body_id)
        if self.turret_id:
            self.canvas.delete(self.turret_id)
    
    def move(self, dx, dy):
        """移动坦克"""
        self.x += dx
        self.y += dy
        self._draw()
    
    def set_direction(self, direction):
        """设置坦克方向"""
        self.direction = direction
        self._draw()
    
    def destroy(self):
        """销毁坦克"""
        self._clear()
        self.alive = False
    
    def get_bounds(self):
        """获取坦克边界"""
        half = self.size // 2
        return (
            self.x - half,
            self.y - half,
            self.x + half,
            self.y + half
        )


class PlayerTank(Tank):
    """玩家坦克类 - 继承自Tank基类"""
    
    def __init__(self, canvas, x, y):
        self.shield_id = None
        self.lives = 3
        self.invincible = False
        self.invincible_timer = 0
        super().__init__(canvas, x, y, '#4CAF50', 'up', 32)
    
    def respawn(self, x, y):
        """重生"""
        self.x = x
        self.y = y
        self.direction = 'up'
        self.alive = True
        self.invincible = True
        self.invincible_timer = 120
        self._draw()
    
    def _draw(self):
        """重写绘制方法，添加无敌状态显示"""
        super()._draw()
        if self.invincible and self.alive:
            half = self.size // 2 + 5
            self.shield_id = self.canvas.create_oval(
                self.x - half, self.y - half,
                self.x + half, self.y + half,
                outline='cyan', width=2, dash=(4, 4)
            )
    
    def _clear(self):
        """清除护盾"""
        super()._clear()
        if self.shield_id:
            self.canvas.delete(self.shield_id)
            self.shield_id = None
    
    def update_invincibility(self):
        """更新无敌状态"""
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False


class EnemyTank(Tank):
    """敌方坦克类 - 继承自Tank基类，包含AI行为"""
    
    def __init__(self, canvas, x, y, difficulty='medium'):
        colors = {
            'easy': '#FF9800',
            'medium': '#F44336',
            'hard': '#9C27B0'
        }
        super().__init__(canvas, x, y, colors.get(difficulty, '#F44336'), random.choice(['up', 'down', 'left', 'right']), 28)
        self.difficulty = difficulty
        self.move_timer = 0
        self.shoot_timer = 0
        self._set_difficulty_params()
    
    def _set_difficulty_params(self):
        """根据难度设置参数"""
        if self.difficulty == 'easy':
            self.speed = 2
            self.move_interval = 30
            self.shoot_interval = 90
        elif self.difficulty == 'hard':
            self.speed = 4
            self.move_interval = 10
            self.shoot_interval = 40
        else:
            self.speed = 3
            self.move_interval = 20
            self.shoot_interval = 60
    
    def ai_move(self, player_x, player_y, walls):
        """AI移动逻辑"""
        self.move_timer += 1
        
        if self.move_timer >= self.move_interval:
            self.move_timer = 0
            
            if self.difficulty == 'hard':
                if random.random() < 0.6:
                    if abs(player_x - self.x) > abs(player_y - self.y):
                        self.direction = 'right' if player_x > self.x else 'left'
                    else:
                        self.direction = 'down' if player_y > self.y else 'up'
                else:
                    self.direction = random.choice(['up', 'down', 'left', 'right'])
            else:
                self.direction = random.choice(['up', 'down', 'left', 'right'])
        
        dx, dy = 0, 0
        if self.direction == 'up':
            dy = -self.speed
        elif self.direction == 'down':
            dy = self.speed
        elif self.direction == 'left':
            dx = -self.speed
        else:
            dx = self.speed
        
        new_x = self.x + dx
        new_y = self.y + dy
        
        if self._can_move(new_x, new_y, walls):
            self.move(dx, dy)
        else:
            self.direction = random.choice(['up', 'down', 'left', 'right'])
    
    def _can_move(self, new_x, new_y, walls):
        """检查是否可以移动到指定位置"""
        half = self.size // 2
        if new_x - half < 0 or new_x + half > 800:
            return False
        if new_y - half < 60 or new_y + half > 600:
            return False
        
        for wall in walls:
            if wall.collides_with(new_x, new_y, self.size):
                return False
        return True
    
    def should_shoot(self):
        """判断是否应该射击"""
        self.shoot_timer += 1
        if self.shoot_timer >= self.shoot_interval:
            self.shoot_timer = 0
            return True
        return False


class Bullet:
    """子弹类 - 定义子弹的属性和行为"""
    
    def __init__(self, canvas, x, y, direction, owner='player'):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.direction = direction
        self.owner = owner
        self.speed = 8 if owner == 'player' else 6
        self.size = 6
        self.alive = True
        self.id = None
        self._draw()
    
    def _draw(self):
        """绘制子弹"""
        color = '#FFEB3B' if self.owner == 'player' else '#FF5722'
        self.id = self.canvas.create_oval(
            self.x - self.size, self.y - self.size,
            self.x + self.size, self.y + self.size,
            fill=color, outline='black'
        )
    
    def move(self):
        """移动子弹"""
        if self.direction == 'up':
            self.y -= self.speed
        elif self.direction == 'down':
            self.y += self.speed
        elif self.direction == 'left':
            self.x -= self.speed
        else:
            self.x += self.speed
        
        self.canvas.coords(
            self.id,
            self.x - self.size, self.y - self.size,
            self.x + self.size, self.y + self.size
        )
    
    def is_out_of_bounds(self):
        """检查子弹是否出界"""
        return self.x < 0 or self.x > 800 or self.y < 60 or self.y > 600
    
    def destroy(self):
        """销毁子弹"""
        if self.id:
            self.canvas.delete(self.id)
        self.alive = False
    
    def get_bounds(self):
        """获取子弹边界"""
        return (
            self.x - self.size,
            self.y - self.size,
            self.x + self.size,
            self.y + self.size
        )


class Wall:
    """墙体类 - 定义障碍物的属性和行为"""
    
    def __init__(self, canvas, x, y, width=40, height=40, destructible=True):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.destructible = destructible
        self.alive = True
        self.id = None
        self._draw()
    
    def _draw(self):
        """绘制墙体"""
        color = '#8B4513' if self.destructible else '#696969'
        self.id = self.canvas.create_rectangle(
            self.x, self.y,
            self.x + self.width, self.y + self.height,
            fill=color, outline='black', width=2
        )
        
        if not self.destructible:
            self.canvas.create_line(
                self.x, self.y,
                self.x + self.width, self.y + self.height,
                fill='white', width=2
            )
            self.canvas.create_line(
                self.x + self.width, self.y,
                self.x, self.y + self.height,
                fill='white', width=2
            )
    
    def collides_with(self, obj_x, obj_y, obj_size):
        """检查是否与指定对象碰撞"""
        half = obj_size // 2
        return not (
            obj_x + half < self.x or
            obj_x - half > self.x + self.width or
            obj_y + half < self.y or
            obj_y - half > self.y + self.height
        )
    
    def collides_with_bullet(self, bullet):
        """检查是否与子弹碰撞"""
        b = bullet.get_bounds()
        return not (
            b[2] < self.x or
            b[0] > self.x + self.width or
            b[3] < self.y or
            b[1] > self.y + self.height
        )
    
    def destroy(self):
        """销毁墙体"""
        if self.id:
            self.canvas.delete(self.id)
        self.alive = False


class Explosion:
    """爆炸效果类 - 显示击中效果"""
    
    def __init__(self, canvas, x, y):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.timer = 15
        self.particles = []
        self._create_particles()
    
    def _create_particles(self):
        """创建爆炸粒子"""
        colors = ['#FF6B6B', '#FFE66D', '#FF8E53', '#FF5252']
        for i in range(8):
            angle = i * 45
            rad = math.radians(angle)
            particle = {
                'id': self.canvas.create_oval(
                    self.x - 5, self.y - 5,
                    self.x + 5, self.y + 5,
                    fill=random.choice(colors), outline=''
                ),
                'dx': math.cos(rad) * 3,
                'dy': math.sin(rad) * 3
            }
            self.particles.append(particle)
    
    def update(self):
        """更新爆炸动画"""
        self.timer -= 1
        for p in self.particles:
            self.canvas.move(p['id'], p['dx'], p['dy'])
        return self.timer > 0
    
    def destroy(self):
        """清除爆炸效果"""
        for p in self.particles:
            self.canvas.delete(p['id'])


class TankGame:
    """坦克大战游戏主类 - 管理游戏的所有组件和逻辑"""
    
    GAME_WIDTH = 800
    GAME_HEIGHT = 600
    CONTROL_HEIGHT = 60
    
    def __init__(self, root):
        self.root = root
        self.root.title("坦克大战")
        self.root.resizable(False, False)
        
        self.difficulty = 'medium'
        self.game_running = False
        self.game_paused = False
        self.score = 0
        self.high_score = self._load_high_score()
        
        self.sound_manager = SoundManager()
        
        self._setup_ui()
        self._init_game_state()
        self._bind_events()
    
    def _load_high_score(self):
        """从文件加载最高分"""
        filepath = os.path.join(os.path.dirname(__file__), 'tank_high_score.txt')
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return 0
    
    def _save_high_score(self):
        """保存最高分到文件"""
        filepath = os.path.join(os.path.dirname(__file__), 'tank_high_score.txt')
        try:
            with open(filepath, 'w') as f:
                f.write(str(self.high_score))
        except Exception as e:
            print(f"保存最高分失败：{e}")
    
    def _setup_ui(self):
        """设置游戏界面"""
        self.control_frame = tk.Frame(self.root, bg='#2C3E50', height=self.CONTROL_HEIGHT)
        self.control_frame.pack(fill=tk.X)
        self.control_frame.pack_propagate(False)
        
        btn_frame = tk.Frame(self.control_frame, bg='#2C3E50')
        btn_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.btn_easy = tk.Button(
            btn_frame, text="简单", width=8,
            command=lambda: self._set_difficulty('easy'),
            bg='#27AE60', fg='white', font=('Arial', 10, 'bold')
        )
        self.btn_easy.pack(side=tk.LEFT, padx=5)
        
        self.btn_medium = tk.Button(
            btn_frame, text="中等", width=8,
            command=lambda: self._set_difficulty('medium'),
            bg='#F39C12', fg='white', font=('Arial', 10, 'bold')
        )
        self.btn_medium.pack(side=tk.LEFT, padx=5)
        
        self.btn_hard = tk.Button(
            btn_frame, text="困难", width=8,
            command=lambda: self._set_difficulty('hard'),
            bg='#E74C3C', fg='white', font=('Arial', 10, 'bold')
        )
        self.btn_hard.pack(side=tk.LEFT, padx=5)
        
        self.btn_start = tk.Button(
            btn_frame, text="开始游戏", width=10,
            command=self._start_game,
            bg='#3498DB', fg='white', font=('Arial', 10, 'bold')
        )
        self.btn_start.pack(side=tk.LEFT, padx=20)
        
        self.btn_restart = tk.Button(
            btn_frame, text="重新开始", width=10,
            command=self._restart_game,
            bg='#9B59B6', fg='white', font=('Arial', 10, 'bold')
        )
        self.btn_restart.pack(side=tk.LEFT, padx=5)
        
        info_frame = tk.Frame(self.control_frame, bg='#2C3E50')
        info_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        self.score_label = tk.Label(
            info_frame, text="分数: 0", bg='#2C3E50', fg='white',
            font=('Arial', 12, 'bold')
        )
        self.score_label.pack(side=tk.LEFT, padx=10)
        
        self.lives_label = tk.Label(
            info_frame, text="生命: ❤❤❤", bg='#2C3E50', fg='#E74C3C',
            font=('Arial', 12, 'bold')
        )
        self.lives_label.pack(side=tk.LEFT, padx=10)
        
        self.high_score_label = tk.Label(
            info_frame, text=f"最高分: {self.high_score}", bg='#2C3E50', fg='#F1C40F',
            font=('Arial', 12, 'bold')
        )
        self.high_score_label.pack(side=tk.LEFT, padx=10)
        
        self.canvas = tk.Canvas(
            self.root, width=self.GAME_WIDTH, height=self.GAME_HEIGHT,
            bg='#1a1a2e', highlightthickness=0
        )
        self.canvas.pack()
        
        self._draw_background()
    
    def _draw_background(self):
        """绘制游戏背景"""
        for i in range(0, self.GAME_WIDTH, 40):
            for j in range(0, self.GAME_HEIGHT, 40):
                if (i // 40 + j // 40) % 2 == 0:
                    self.canvas.create_rectangle(
                        i, j, i + 40, j + 40,
                        fill='#16213e', outline=''
                    )
    
    def _init_game_state(self):
        """初始化游戏状态"""
        self.player = None
        self.enemies = []
        self.player_bullets = []
        self.enemy_bullets = []
        self.walls = []
        self.explosions = []
        self.keys_pressed = set()
        self.enemy_spawn_timer = 0
        self.max_enemies = {'easy': 3, 'medium': 5, 'hard': 8}
        self.spawn_interval = {'easy': 180, 'medium': 120, 'hard': 80}
    
    def _bind_events(self):
        """绑定键盘事件"""
        self.root.bind('<KeyPress>', self._on_key_press)
        self.root.bind('<KeyRelease>', self._on_key_release)
        self.root.bind('<p>', self._toggle_pause)
        self.root.bind('<P>', self._toggle_pause)
    
    def _on_key_press(self, event):
        """按键按下事件处理"""
        self.keys_pressed.add(event.keysym)
        
        if event.keysym == 'space':
            if self.game_running and not self.game_paused:
                self._player_shoot()
            elif self.game_running:
                self._toggle_pause(None)
    
    def _on_key_release(self, event):
        """按键释放事件处理"""
        self.keys_pressed.discard(event.keysym)
    
    def _set_difficulty(self, difficulty):
        """设置游戏难度"""
        self.difficulty = difficulty
        
        self.btn_easy.config(relief=tk.RAISED if difficulty != 'easy' else tk.SUNKEN)
        self.btn_medium.config(relief=tk.RAISED if difficulty != 'medium' else tk.SUNKEN)
        self.btn_hard.config(relief=tk.RAISED if difficulty != 'hard' else tk.SUNKEN)
    
    def _start_game(self):
        """开始游戏"""
        if self.game_running:
            return
        
        self._init_game_state()
        self.canvas.delete('all')
        self._draw_background()
        
        self._create_walls()
        
        self.player = PlayerTank(
            self.canvas,
            self.GAME_WIDTH // 2,
            self.GAME_HEIGHT - 50
        )
        
        self.score = 0
        self._update_score_display()
        self._update_lives_display()
        
        self.game_running = True
        self.game_paused = False
        self.btn_start.config(state=tk.DISABLED)
        
        self._game_loop()
    
    def _restart_game(self):
        """重新开始游戏"""
        self.game_running = False
        self.root.after(100, self._start_game)
    
    def _create_walls(self):
        """创建地图障碍物"""
        wall_positions = [
            (100, 150), (140, 150), (180, 150),
            (620, 150), (660, 150), (700, 150),
            (100, 350), (140, 350), (180, 350),
            (620, 350), (660, 350), (700, 350),
            (350, 200), (390, 200), (430, 200),
            (350, 400), (390, 400), (430, 400),
            (200, 250, 40, 80, False),
            (560, 250, 40, 80, False),
        ]
        
        for pos in wall_positions:
            if len(pos) == 2:
                self.walls.append(Wall(self.canvas, pos[0], pos[1]))
            elif len(pos) == 4:
                self.walls.append(Wall(self.canvas, pos[0], pos[1], pos[2], pos[3]))
            else:
                self.walls.append(Wall(self.canvas, pos[0], pos[1], pos[2], pos[3], pos[4]))
    
    def _spawn_enemy(self):
        """生成敌方坦克"""
        if len(self.enemies) >= self.max_enemies[self.difficulty]:
            return
        
        self.enemy_spawn_timer += 1
        if self.enemy_spawn_timer < self.spawn_interval[self.difficulty]:
            return
        self.enemy_spawn_timer = 0
        
        spawn_points = [
            (50, 80),
            (self.GAME_WIDTH // 2, 80),
            (self.GAME_WIDTH - 50, 80)
        ]
        
        for _ in range(10):
            x, y = random.choice(spawn_points)
            x += random.randint(-30, 30)
            
            can_spawn = True
            for enemy in self.enemies:
                if abs(enemy.x - x) < 50 and abs(enemy.y - y) < 50:
                    can_spawn = False
                    break
            
            if can_spawn:
                enemy = EnemyTank(self.canvas, x, y, self.difficulty)
                self.enemies.append(enemy)
                break
    
    def _player_shoot(self):
        """玩家发射子弹"""
        if not self.player or not self.player.alive:
            return
        
        if len(self.player_bullets) >= 3:
            return
        
        offset = self.player.size // 2 + 10
        if self.player.direction == 'up':
            bx, by = self.player.x, self.player.y - offset
        elif self.player.direction == 'down':
            bx, by = self.player.x, self.player.y + offset
        elif self.player.direction == 'left':
            bx, by = self.player.x - offset, self.player.y
        else:
            bx, by = self.player.x + offset, self.player.y
        
        bullet = Bullet(self.canvas, bx, by, self.player.direction, 'player')
        self.player_bullets.append(bullet)
        self.sound_manager.play('shoot')
    
    def _enemy_shoot(self, enemy):
        """敌方坦克发射子弹"""
        if len(self.enemy_bullets) >= 10:
            return
        
        offset = enemy.size // 2 + 8
        if enemy.direction == 'up':
            bx, by = enemy.x, enemy.y - offset
        elif enemy.direction == 'down':
            bx, by = enemy.x, enemy.y + offset
        elif enemy.direction == 'left':
            bx, by = enemy.x - offset, enemy.y
        else:
            bx, by = enemy.x + offset, enemy.y
        
        bullet = Bullet(self.canvas, bx, by, enemy.direction, 'enemy')
        self.enemy_bullets.append(bullet)
    
    def _toggle_pause(self, event):
        """切换暂停状态"""
        if not self.game_running:
            return
        
        self.game_paused = not self.game_paused
        
        if self.game_paused:
            self._show_pause_overlay()
        else:
            self.canvas.delete('pause_overlay')
            self._game_loop()
    
    def _show_pause_overlay(self):
        """显示暂停提示"""
        self.canvas.create_rectangle(
            0, 0, self.GAME_WIDTH, self.GAME_HEIGHT,
            fill='black', stipple='gray50', tags='pause_overlay'
        )
        self.canvas.create_text(
            self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2,
            text="游戏暂停\n按 P 或 空格 继续",
            fill='white', font=('Arial', 24, 'bold'),
            justify='center', tags='pause_overlay'
        )
    
    def _update_player(self):
        """更新玩家状态"""
        if not self.player or not self.player.alive:
            return
        
        dx, dy = 0, 0
        new_direction = None
        
        if 'Up' in self.keys_pressed:
            dy = -self.player.speed
            new_direction = 'up'
        elif 'Down' in self.keys_pressed:
            dy = self.player.speed
            new_direction = 'down'
        elif 'Left' in self.keys_pressed:
            dx = -self.player.speed
            new_direction = 'left'
        elif 'Right' in self.keys_pressed:
            dx = self.player.speed
            new_direction = 'right'
        
        if new_direction:
            self.player.set_direction(new_direction)
        
        if dx != 0 or dy != 0:
            new_x = self.player.x + dx
            new_y = self.player.y + dy
            
            if self._can_player_move(new_x, new_y):
                self.player.move(dx, dy)
        
        self.player.update_invincibility()
    
    def _can_player_move(self, new_x, new_y):
        """检查玩家是否可以移动到指定位置"""
        half = self.player.size // 2
        
        if new_x - half < 0 or new_x + half > self.GAME_WIDTH:
            return False
        if new_y - half < 60 or new_y + half > self.GAME_HEIGHT:
            return False
        
        for wall in self.walls:
            if wall.alive and wall.collides_with(new_x, new_y, self.player.size):
                return False
        
        for enemy in self.enemies:
            if enemy.alive:
                dist = math.sqrt((enemy.x - new_x)**2 + (enemy.y - new_y)**2)
                if dist < self.player.size:
                    return False
        
        return True
    
    def _update_bullets(self):
        """更新所有子弹"""
        for bullet in self.player_bullets[:]:
            bullet.move()
            
            if bullet.is_out_of_bounds():
                bullet.destroy()
                self.player_bullets.remove(bullet)
                continue
            
            for wall in self.walls[:]:
                if wall.alive and wall.collides_with_bullet(bullet):
                    bullet.destroy()
                    self.player_bullets.remove(bullet)
                    if wall.destructible:
                        wall.destroy()
                    break
            
            for enemy in self.enemies[:]:
                if enemy.alive and self._check_collision(bullet, enemy):
                    bullet.destroy()
                    self.player_bullets.remove(bullet)
                    enemy.destroy()
                    self.enemies.remove(enemy)
                    self.score += 100
                    self._update_score_display()
                    self.explosions.append(Explosion(self.canvas, enemy.x, enemy.y))
                    self.sound_manager.play('explosion')
                    break
        
        for bullet in self.enemy_bullets[:]:
            bullet.move()
            
            if bullet.is_out_of_bounds():
                bullet.destroy()
                self.enemy_bullets.remove(bullet)
                continue
            
            for wall in self.walls[:]:
                if wall.alive and wall.collides_with_bullet(bullet):
                    bullet.destroy()
                    self.enemy_bullets.remove(bullet)
                    if wall.destructible:
                        wall.destroy()
                    break
            
            if self.player and self.player.alive and not self.player.invincible:
                if self._check_collision(bullet, self.player):
                    bullet.destroy()
                    self.enemy_bullets.remove(bullet)
                    self._player_hit()
    
    def _check_collision(self, bullet, tank):
        """检查子弹与坦克的碰撞"""
        dist = math.sqrt((bullet.x - tank.x)**2 + (bullet.y - tank.y)**2)
        return dist < tank.size // 2 + bullet.size
    
    def _player_hit(self):
        """玩家被击中"""
        self.player.lives -= 1
        self._update_lives_display()
        self.explosions.append(Explosion(self.canvas, self.player.x, self.player.y))
        self.sound_manager.play('explosion')
        
        if self.player.lives <= 0:
            self._game_over()
        else:
            self.player.respawn(self.GAME_WIDTH // 2, self.GAME_HEIGHT - 50)
    
    def _update_enemies(self):
        """更新敌方坦克"""
        for enemy in self.enemies[:]:
            if not enemy.alive:
                continue
            
            enemy.ai_move(self.player.x if self.player else 0, 
                         self.player.y if self.player else 0, 
                         [w for w in self.walls if w.alive])
            
            if enemy.should_shoot():
                self._enemy_shoot(enemy)
    
    def _update_explosions(self):
        """更新爆炸效果"""
        for explosion in self.explosions[:]:
            if not explosion.update():
                explosion.destroy()
                self.explosions.remove(explosion)
    
    def _update_score_display(self):
        """更新分数显示"""
        self.score_label.config(text=f"分数: {self.score}")
        
        if self.score > self.high_score:
            self.high_score = self.score
            self.high_score_label.config(text=f"最高分: {self.high_score}")
            self._save_high_score()
    
    def _update_lives_display(self):
        """更新生命值显示"""
        if self.player:
            hearts = '❤' * self.player.lives + '♡' * (3 - self.player.lives)
            self.lives_label.config(text=f"生命: {hearts}")
    
    def _game_over(self):
        """游戏结束"""
        self.game_running = False
        self.player.destroy()
        self.sound_manager.play('game_over')
        
        self.canvas.create_rectangle(
            0, 0, self.GAME_WIDTH, self.GAME_HEIGHT,
            fill='black', stipple='gray50'
        )
        self.canvas.create_text(
            self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2 - 40,
            text="游戏结束",
            fill='#E74C3C', font=('Arial', 36, 'bold')
        )
        self.canvas.create_text(
            self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2 + 20,
            text=f"最终得分: {self.score}",
            fill='white', font=('Arial', 24)
        )
        self.canvas.create_text(
            self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2 + 60,
            text=f"最高分: {self.high_score}",
            fill='#F1C40F', font=('Arial', 18)
        )
        
        self.btn_start.config(state=tk.NORMAL)
    
    def _game_loop(self):
        """游戏主循环"""
        if not self.game_running or self.game_paused:
            return
        
        self._update_player()
        self._spawn_enemy()
        self._update_enemies()
        self._update_bullets()
        self._update_explosions()
        
        self.root.after(16, self._game_loop)


def main():
    """程序入口"""
    root = tk.Tk()
    root.configure(bg='#2C3E50')
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width - 800) // 2
    y = (screen_height - 660) // 2
    root.geometry(f"800x660+{x}+{y}")
    
    game = TankGame(root)
    
    root.mainloop()


if __name__ == '__main__':
    main()
