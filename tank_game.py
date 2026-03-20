"""
坦克大战游戏 - Tank Battle Game
================================
使用Python + Tkinter开发的经典坦克大战游戏

依赖安装:
    pip install pygame  # 用于音效播放（可选）

文件说明:
    - tank_game.py: 主程序文件
    - tank_high_score.txt: 最高分记录文件（自动创建）
    - shoot.wav: 发射子弹音效（可选）
    - explosion.wav: 爆炸音效（可选）
    - game_over.wav: 游戏结束音效（可选）

作者: AI Assistant
日期: 2026-03-18
"""

import tkinter as tk
from tkinter import messagebox
import random
import os
import math
import time
from typing import List, Optional, Tuple

# 尝试导入pygame用于音效，如果失败则使用静音模式
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("提示: 未安装pygame，游戏将以静音模式运行。安装命令: pip install pygame")


# ==================== 常量定义 ====================

# 游戏窗口设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GAME_AREA_HEIGHT = 520  # 游戏区域高度（顶部留空给控制面板）
CONTROL_PANEL_HEIGHT = 80

# 游戏元素尺寸
TANK_SIZE = 30
BULLET_SIZE = 6
WALL_SIZE = 20

# 游戏速度设置
PLAYER_SPEED = 5
BULLET_SPEED = 8

# 方向常量
DIRECTION_UP = 0
DIRECTION_RIGHT = 1
DIRECTION_DOWN = 2
DIRECTION_LEFT = 3

# 颜色定义
COLOR_BACKGROUND = "#2d5016"  # 深绿色草地背景
COLOR_PLAYER = "#4169E1"  # 皇家蓝（玩家坦克）
COLOR_ENEMY = "#DC143C"  # 深红色（敌方坦克）
COLOR_BULLET_PLAYER = "#FFD700"  # 金色（玩家子弹）
COLOR_BULLET_ENEMY = "#FF6347"  # 番茄红（敌方子弹）
COLOR_WALL = "#8B4513"  #  saddlebrown（墙体）
COLOR_STEEL_WALL = "#708090"  # 石板灰（钢铁墙）
COLOR_TEXT = "#FFFFFF"  # 白色文字
COLOR_PANEL_BG = "#1a1a1a"  # 控制面板背景

# 难度设置
DIFFICULTY_SETTINGS = {
    "简单": {"enemy_count": 3, "enemy_speed": 2, "enemy_shoot_interval": 2000, "spawn_interval": 4000},
    "中等": {"enemy_count": 5, "enemy_speed": 3, "enemy_shoot_interval": 1500, "spawn_interval": 3000},
    "困难": {"enemy_count": 8, "enemy_speed": 5, "enemy_shoot_interval": 800, "spawn_interval": 2000}
}


# ==================== 音效管理类 ====================

class SoundManager:
    """
    音效管理类
    负责加载和播放游戏音效，支持静音模式（当pygame不可用或音效文件缺失时）
    """
    
    def __init__(self):
        """初始化音效管理器"""
        self.sounds = {}
        self.muted = not PYGAME_AVAILABLE
        
        if PYGAME_AVAILABLE:
            pygame.mixer.init()
            self._load_sounds()
    
    def _load_sounds(self):
        """加载音效文件，如果文件不存在则跳过"""
        sound_files = {
            "shoot": "shoot.wav",
            "explosion": "explosion.wav",
            "game_over": "game_over.wav"
        }
        
        for name, filename in sound_files.items():
            try:
                if os.path.exists(filename):
                    self.sounds[name] = pygame.mixer.Sound(filename)
                else:
                    print(f"提示: 音效文件 '{filename}' 不存在，将跳过此音效")
            except Exception as e:
                print(f"警告: 无法加载音效 '{filename}': {e}")
    
    def play(self, sound_name: str):
        """
        播放指定音效
        
        Args:
            sound_name: 音效名称 (shoot/explosion/game_over)
        """
        if self.muted or sound_name not in self.sounds:
            return
        try:
            self.sounds[sound_name].play()
        except Exception:
            pass  # 播放失败时静默处理


# ==================== 游戏实体基类 ====================

class GameObject:
    """
    游戏对象基类
    所有游戏实体（坦克、子弹、墙体）的父类
    """
    
    def __init__(self, x: int, y: int, width: int, height: int):
        """
        初始化游戏对象
        
        Args:
            x: 对象左上角X坐标
            y: 对象左上角Y坐标
            width: 对象宽度
            height: 对象高度
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.alive = True
    
    def get_rect(self) -> Tuple[int, int, int, int]:
        """
        获取对象的矩形区域
        
        Returns:
            (x, y, x+width, y+height) 格式的元组
        """
        return (self.x, self.y, self.x + self.width, self.y + self.height)
    
    def collides_with(self, other: 'GameObject') -> bool:
        """
        检测与另一个对象的碰撞
        
        Args:
            other: 另一个游戏对象
            
        Returns:
            如果发生碰撞返回True，否则返回False
        """
        r1 = self.get_rect()
        r2 = other.get_rect()
        return not (r1[2] <= r2[0] or r1[0] >= r2[2] or 
                    r1[3] <= r2[1] or r1[1] >= r2[3])


# ==================== 子弹类 ====================

class Bullet(GameObject):
    """
    子弹类
    表示坦克发射的子弹，包含位置、方向、速度等属性
    """
    
    def __init__(self, x: int, y: int, direction: int, is_player: bool = True):
        """
        初始化子弹
        
        Args:
            x: 子弹初始X坐标
            y: 子弹初始Y坐标
            direction: 子弹飞行方向 (0-3)
            is_player: 是否为玩家子弹（影响颜色和伤害对象）
        """
        super().__init__(x, y, BULLET_SIZE, BULLET_SIZE)
        self.direction = direction
        self.is_player = is_player
        self.speed = BULLET_SPEED
    
    def move(self):
        """根据方向移动子弹"""
        if self.direction == DIRECTION_UP:
            self.y -= self.speed
        elif self.direction == DIRECTION_RIGHT:
            self.x += self.speed
        elif self.direction == DIRECTION_DOWN:
            self.y += self.speed
        elif self.direction == DIRECTION_LEFT:
            self.x -= self.speed
    
    def is_out_of_bounds(self) -> bool:
        """
        检查子弹是否超出游戏边界
        
        Returns:
            如果子弹超出边界返回True
        """
        return (self.x < 0 or self.x > WINDOW_WIDTH or 
                self.y < CONTROL_PANEL_HEIGHT or self.y > WINDOW_HEIGHT)


# ==================== 坦克基类 ====================

class Tank(GameObject):
    """
    坦克基类
    玩家坦克和敌方坦克的父类，包含通用的坦克属性和方法
    """
    
    def __init__(self, x: int, y: int, color: str, speed: int = PLAYER_SPEED):
        """
        初始化坦克
        
        Args:
            x: 坦克初始X坐标
            y: 坦克初始Y坐标
            color: 坦克颜色
            speed: 坦克移动速度
        """
        super().__init__(x, y, TANK_SIZE, TANK_SIZE)
        self.color = color
        self.direction = DIRECTION_UP
        self.speed = speed
        self.last_shot_time = 0
        self.shoot_cooldown = 300  # 射击冷却时间（毫秒）
    
    def move(self, direction: int, walls: List['Wall']):
        """
        移动坦克
        
        Args:
            direction: 移动方向
            walls: 墙体列表（用于碰撞检测）
        """
        self.direction = direction
        
        # 计算新位置
        new_x, new_y = self.x, self.y
        if direction == DIRECTION_UP:
            new_y -= self.speed
        elif direction == DIRECTION_RIGHT:
            new_x += self.speed
        elif direction == DIRECTION_DOWN:
            new_y += self.speed
        elif direction == DIRECTION_LEFT:
            new_x -= self.speed
        
        # 边界检测
        if new_x < 0:
            new_x = 0
        elif new_x > WINDOW_WIDTH - self.width:
            new_x = WINDOW_WIDTH - self.width
        
        if new_y < CONTROL_PANEL_HEIGHT:
            new_y = CONTROL_PANEL_HEIGHT
        elif new_y > WINDOW_HEIGHT - self.height:
            new_y = WINDOW_HEIGHT - self.height
        
        # 墙体碰撞检测
        old_x, old_y = self.x, self.y
        self.x, self.y = new_x, new_y
        
        for wall in walls:
            if wall.alive and self.collides_with(wall):
                # 发生碰撞，恢复原位置
                self.x, self.y = old_x, old_y
                break
    
    def can_shoot(self, current_time: int) -> bool:
        """
        检查是否可以射击
        
        Args:
            current_time: 当前时间（毫秒）
            
        Returns:
            如果可以射击返回True
        """
        return current_time - self.last_shot_time >= self.shoot_cooldown
    
    def shoot(self, current_time: int) -> Optional[Bullet]:
        """
        发射子弹
        
        Args:
            current_time: 当前时间（毫秒）
            
        Returns:
            返回新创建的子弹对象，如果冷却中则返回None
        """
        if not self.can_shoot(current_time):
            return None
        
        self.last_shot_time = current_time
        
        # 计算子弹发射位置（坦克炮口）
        bullet_x = self.x + self.width // 2 - BULLET_SIZE // 2
        bullet_y = self.y + self.height // 2 - BULLET_SIZE // 2
        
        # 根据方向调整子弹位置
        if self.direction == DIRECTION_UP:
            bullet_y = self.y - BULLET_SIZE
        elif self.direction == DIRECTION_RIGHT:
            bullet_x = self.x + self.width
        elif self.direction == DIRECTION_DOWN:
            bullet_y = self.y + self.height
        elif self.direction == DIRECTION_LEFT:
            bullet_x = self.x - BULLET_SIZE
        
        return Bullet(bullet_x, bullet_y, self.direction, isinstance(self, PlayerTank))


# ==================== 玩家坦克类 ====================

class PlayerTank(Tank):
    """
    玩家坦克类
    继承自Tank，表示玩家控制的坦克
    """
    
    def __init__(self, x: int, y: int):
        """
        初始化玩家坦克
        
        Args:
            x: 初始X坐标
            y: 初始Y坐标
        """
        super().__init__(x, y, COLOR_PLAYER, PLAYER_SPEED)
        self.lives = 3  # 初始生命值


# ==================== 敌方坦克类 ====================

class EnemyTank(Tank):
    """
    敌方坦克类
    继承自Tank，具备简单的AI行为
    """
    
    def __init__(self, x: int, y: int, speed: int = 3):
        """
        初始化敌方坦克
        
        Args:
            x: 初始X坐标
            y: 初始Y坐标
            speed: 移动速度
        """
        super().__init__(x, y, COLOR_ENEMY, speed)
        self.move_timer = 0
        self.move_interval = 500  # 改变方向的间隔（毫秒）
        self.ai_type = random.choice(["random", "chase"])  # AI类型：随机移动或追踪玩家
    
    def ai_update(self, current_time: int, player: PlayerTank, walls: List['Wall']):
        """
        AI更新逻辑
        
        Args:
            current_time: 当前时间（毫秒）
            player: 玩家坦克对象
            walls: 墙体列表
        """
        # 定期改变方向
        if current_time - self.move_timer > self.move_interval:
            self.move_timer = current_time
            
            if self.ai_type == "chase" and random.random() < 0.6:
                # 追踪玩家：选择朝向玩家的方向
                self.direction = self._get_direction_toward_player(player)
            else:
                # 随机移动
                self.direction = random.randint(0, 3)
        
        # 尝试移动
        old_x, old_y = self.x, self.y
        self.move(self.direction, walls)
        
        # 如果无法移动（被墙挡住），随机选择新方向
        if self.x == old_x and self.y == old_y:
            self.direction = random.randint(0, 3)
    
    def _get_direction_toward_player(self, player: PlayerTank) -> int:
        """
        计算朝向玩家的方向
        
        Args:
            player: 玩家坦克
            
        Returns:
            最佳方向 (0-3)
        """
        dx = player.x - self.x
        dy = player.y - self.y
        
        # 选择距离较大的轴方向
        if abs(dx) > abs(dy):
            return DIRECTION_RIGHT if dx > 0 else DIRECTION_LEFT
        else:
            return DIRECTION_DOWN if dy > 0 else DIRECTION_UP
    
    def should_shoot(self, current_time: int, shoot_interval: int) -> bool:
        """
        AI决定是否射击
        
        Args:
            current_time: 当前时间
            shoot_interval: 射击间隔
            
        Returns:
            是否应该射击
        """
        if current_time - self.last_shot_time < shoot_interval:
            return False
        
        # 随机决定是否射击，增加一些不确定性
        return random.random() < 0.3


# ==================== 墙体类 ====================

class Wall(GameObject):
    """
    墙体类
    表示地图上的障碍物，可以是可破坏或不可破坏的
    """
    
    def __init__(self, x: int, y: int, destructible: bool = True):
        """
        初始化墙体
        
        Args:
            x: X坐标
            y: Y坐标
            destructible: 是否可被破坏
        """
        super().__init__(x, y, WALL_SIZE, WALL_SIZE)
        self.destructible = destructible
        self.color = COLOR_WALL if destructible else COLOR_STEEL_WALL


# ==================== 游戏主类 ====================

class TankGame:
    """
    坦克大战游戏主类
    管理游戏状态、渲染、事件处理和游戏逻辑
    """
    
    def __init__(self, root: tk.Tk):
        """
        初始化游戏
        
        Args:
            root: Tkinter根窗口
        """
        self.root = root
        self.root.title("坦克大战")
        self.root.resizable(False, False)
        
        # 初始化音效管理器
        self.sound_manager = SoundManager()
        
        # 游戏状态变量
        self.score = 0
        self.high_score = self._load_high_score()
        self.difficulty = "中等"
        self.paused = False
        self.game_over = False
        self.running = True
        
        # 游戏对象列表
        self.player: Optional[PlayerTank] = None
        self.enemies: List[EnemyTank] = []
        self.bullets: List[Bullet] = []
        self.walls: List[Wall] = []
        
        # 游戏时间跟踪
        self.last_spawn_time = 0
        self.game_start_time = 0
        
        # 创建UI
        self._create_ui()
        
        # 初始化游戏
        self.init_game()
        
        # 绑定键盘事件
        self._bind_events()
        
        # 启动游戏循环
        self.game_loop()
    
    def _create_ui(self):
        """创建游戏界面元素"""
        # 创建画布
        self.canvas = tk.Canvas(
            self.root, 
            width=WINDOW_WIDTH, 
            height=WINDOW_HEIGHT,
            bg=COLOR_BACKGROUND
        )
        self.canvas.pack()
        
        # 创建控制面板背景
        self.canvas.create_rectangle(
            0, 0, WINDOW_WIDTH, CONTROL_PANEL_HEIGHT,
            fill=COLOR_PANEL_BG, outline="", tags="panel"
        )
        
        # 难度选择按钮
        self._create_difficulty_buttons()
        
        # 分数和生命值显示
        self.score_text = self.canvas.create_text(
            150, 25, text=f"分数: {self.score}",
            fill=COLOR_TEXT, font=("Arial", 14, "bold"), tags="ui"
        )
        
        self.high_score_text = self.canvas.create_text(
            150, 55, text=f"最高分: {self.high_score}",
            fill=COLOR_TEXT, font=("Arial", 14, "bold"), tags="ui"
        )
        
        self.lives_text = self.canvas.create_text(
            300, 40, text="生命: ❤❤❤",
            fill=COLOR_TEXT, font=("Arial", 16, "bold"), tags="ui"
        )
        
        self.difficulty_text = self.canvas.create_text(
            450, 40, text=f"难度: {self.difficulty}",
            fill=COLOR_TEXT, font=("Arial", 14, "bold"), tags="ui"
        )
        
        # 暂停提示（初始隐藏）
        self.pause_overlay = self.canvas.create_rectangle(
            0, CONTROL_PANEL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT,
            fill="black", stipple="gray50", tags="pause_overlay", state="hidden"
        )
        self.pause_text = self.canvas.create_text(
            WINDOW_WIDTH // 2, (WINDOW_HEIGHT + CONTROL_PANEL_HEIGHT) // 2,
            text="游戏暂停", fill="white", font=("Arial", 36, "bold"),
            tags="pause_text", state="hidden"
        )
        
        # 游戏结束界面（初始隐藏）
        self.game_over_overlay = self.canvas.create_rectangle(
            0, CONTROL_PANEL_HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT,
            fill="black", stipple="gray75", tags="game_over_overlay", state="hidden"
        )
        self.game_over_text = self.canvas.create_text(
            WINDOW_WIDTH // 2, (WINDOW_HEIGHT + CONTROL_PANEL_HEIGHT) // 2 - 50,
            text="游戏结束", fill="red", font=("Arial", 48, "bold"),
            tags="game_over_text", state="hidden"
        )
        self.final_score_text = self.canvas.create_text(
            WINDOW_WIDTH // 2, (WINDOW_HEIGHT + CONTROL_PANEL_HEIGHT) // 2 + 20,
            text="", fill="white", font=("Arial", 24),
            tags="final_score", state="hidden"
        )
        
        # 重新开始按钮（初始隐藏）
        self.restart_button = tk.Button(
            self.root, text="重新开始", command=self.restart_game,
            font=("Arial", 16, "bold"), bg="#4CAF50", fg="white",
            width=12, height=1
        )
        self.restart_button_window = self.canvas.create_window(
            WINDOW_WIDTH // 2, (WINDOW_HEIGHT + CONTROL_PANEL_HEIGHT) // 2 + 80,
            window=self.restart_button, tags="restart_button", state="hidden"
        )
    
    def _create_difficulty_buttons(self):
        """创建难度选择按钮"""
        button_frame = tk.Frame(self.root, bg=COLOR_PANEL_BG)
        self.canvas.create_window(650, 40, window=button_frame, tags="ui")
        
        difficulties = ["简单", "中等", "困难"]
        self.difficulty_buttons = {}
        
        for diff in difficulties:
            btn = tk.Button(
                button_frame, text=diff, command=lambda d=diff: self.set_difficulty(d),
                font=("Arial", 12), width=8,
                bg="#555" if diff != self.difficulty else "#4CAF50",
                fg="white"
            )
            btn.pack(side=tk.LEFT, padx=5)
            self.difficulty_buttons[diff] = btn
    
    def _bind_events(self):
        """绑定键盘事件"""
        self.root.bind("<KeyPress>", self._on_key_press)
        self.root.bind("<KeyRelease>", self._on_key_release)
        
        # 按键状态跟踪
        self.keys_pressed = set()
    
    def _on_key_press(self, event):
        """处理按键按下事件"""
        key = event.keysym
        self.keys_pressed.add(key)
        
        # 空格键：暂停/继续 或 发射子弹
        if key == "space":
            if self.game_over:
                return
            # 如果游戏进行中，空格键用于发射子弹
            # 暂停功能通过其他方式触发，这里简化处理
            pass
        
        # P键：暂停/继续
        if key.lower() == "p":
            self.toggle_pause()
    
    def _on_key_release(self, event):
        """处理按键释放事件"""
        key = event.keysym
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)
    
    def _load_high_score(self) -> int:
        """
        从文件加载最高分
        
        Returns:
            最高分，如果文件不存在则返回0
        """
        filename = "tank_high_score.txt"
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    return int(f.read().strip())
            else:
                # 文件不存在，创建并初始化为0
                with open(filename, "w") as f:
                    f.write("0")
                return 0
        except Exception:
            return 0
    
    def _save_high_score(self):
        """保存最高分到文件"""
        filename = "tank_high_score.txt"
        try:
            with open(filename, "w") as f:
                f.write(str(self.high_score))
        except Exception as e:
            print(f"警告: 无法保存最高分: {e}")
    
    def set_difficulty(self, difficulty: str):
        """
        设置游戏难度
        
        Args:
            difficulty: 难度级别 ("简单"/"中等"/"困难")
        """
        if self.game_over:
            return
        
        self.difficulty = difficulty
        
        # 更新按钮颜色
        for diff, btn in self.difficulty_buttons.items():
            btn.config(bg="#4CAF50" if diff == difficulty else "#555")
        
        # 更新显示
        self.canvas.itemconfig(self.difficulty_text, text=f"难度: {difficulty}")
        
        # 调整现有敌人的速度
        settings = DIFFICULTY_SETTINGS[difficulty]
        for enemy in self.enemies:
            enemy.speed = settings["enemy_speed"]
    
    def toggle_pause(self):
        """切换暂停状态"""
        if self.game_over:
            return
        
        self.paused = not self.paused
        
        if self.paused:
            self.canvas.itemconfig(self.pause_overlay, state="normal")
            self.canvas.itemconfig(self.pause_text, state="normal")
        else:
            self.canvas.itemconfig(self.pause_overlay, state="hidden")
            self.canvas.itemconfig(self.pause_text, state="hidden")
    
    def init_game(self):
        """初始化游戏状态"""
        # 清空游戏对象
        self.enemies.clear()
        self.bullets.clear()
        self.walls.clear()
        
        # 创建玩家坦克
        self.player = PlayerTank(WINDOW_WIDTH // 2 - TANK_SIZE // 2, WINDOW_HEIGHT - TANK_SIZE - 20)
        
        # 创建地图墙体
        self._create_map()
        
        # 重置游戏状态
        self.score = 0
        self.game_over = False
        self.paused = False
        self.running = True
        self.last_spawn_time = int(time.time() * 1000)
        self.game_start_time = self.last_spawn_time
        
        # 隐藏游戏结束界面
        self.canvas.itemconfig(self.game_over_overlay, state="hidden")
        self.canvas.itemconfig(self.game_over_text, state="hidden")
        self.canvas.itemconfig(self.final_score_text, state="hidden")
        self.canvas.itemconfig(self.restart_button_window, state="hidden")
        
        # 更新UI
        self._update_ui()
    
    def _create_map(self):
        """创建游戏地图（墙体布局）"""
        # 创建边界墙体
        for x in range(0, WINDOW_WIDTH, WALL_SIZE):
            if x < WINDOW_WIDTH // 3 or x > WINDOW_WIDTH * 2 // 3:
                self.walls.append(Wall(x, CONTROL_PANEL_HEIGHT + 100, True))
                self.walls.append(Wall(x, WINDOW_HEIGHT - 100, True))
        
        for y in range(CONTROL_PANEL_HEIGHT + 100, WINDOW_HEIGHT - 100, WALL_SIZE):
            if random.random() < 0.3:
                self.walls.append(Wall(100, y, True))
                self.walls.append(Wall(WINDOW_WIDTH - 120, y, True))
        
        # 创建中央障碍物
        for x in range(WINDOW_WIDTH // 2 - 60, WINDOW_WIDTH // 2 + 60, WALL_SIZE):
            for y in range(WINDOW_HEIGHT // 2 - 40, WINDOW_HEIGHT // 2 + 40, WALL_SIZE):
                if random.random() < 0.5:
                    self.walls.append(Wall(x, y, random.choice([True, True, False])))  # 30%钢铁墙
    
    def restart_game(self):
        """重新开始游戏"""
        self.init_game()
    
    def _update_ui(self):
        """更新UI显示"""
        # 更新分数
        self.canvas.itemconfig(self.score_text, text=f"分数: {self.score}")
        self.canvas.itemconfig(self.high_score_text, text=f"最高分: {self.high_score}")
        
        # 更新生命值（使用心形符号）
        lives_str = "❤" * self.player.lives if self.player else ""
        self.canvas.itemconfig(self.lives_text, text=f"生命: {lives_str}")
    
    def game_loop(self):
        """游戏主循环"""
        if self.running:
            if not self.paused and not self.game_over:
                self.update()
            
            self.draw()
            
            # 继续下一帧
            self.root.after(16, self.game_loop)  # 约60 FPS
    
    def update(self):
        """更新游戏逻辑"""
        current_time = int(time.time() * 1000)
        
        # 处理玩家输入
        self._handle_player_input(current_time)
        
        # 更新敌人
        self._update_enemies(current_time)
        
        # 更新子弹
        self._update_bullets()
        
        # 生成新敌人
        self._spawn_enemies(current_time)
        
        # 更新UI
        self._update_ui()
    
    def _handle_player_input(self, current_time: int):
        """处理玩家输入"""
        if not self.player or not self.player.alive:
            return
        
        # 方向键移动
        if "Up" in self.keys_pressed:
            self.player.move(DIRECTION_UP, self.walls)
        elif "Down" in self.keys_pressed:
            self.player.move(DIRECTION_DOWN, self.walls)
        elif "Left" in self.keys_pressed:
            self.player.move(DIRECTION_LEFT, self.walls)
        elif "Right" in self.keys_pressed:
            self.player.move(DIRECTION_RIGHT, self.walls)
        
        # 空格键发射子弹
        if "space" in self.keys_pressed:
            bullet = self.player.shoot(current_time)
            if bullet:
                self.bullets.append(bullet)
                self.sound_manager.play("shoot")
    
    def _update_enemies(self, current_time: int):
        """更新敌人AI和行为"""
        settings = DIFFICULTY_SETTINGS[self.difficulty]
        
        for enemy in self.enemies[:]:
            if not enemy.alive:
                continue
            
            # AI更新
            enemy.ai_update(current_time, self.player, self.walls)
            
            # AI射击
            if enemy.should_shoot(current_time, settings["enemy_shoot_interval"]):
                bullet = enemy.shoot(current_time)
                if bullet:
                    self.bullets.append(bullet)
    
    def _update_bullets(self):
        """更新子弹位置和碰撞检测"""
        for bullet in self.bullets[:]:
            if not bullet.alive:
                continue
            
            # 移动子弹
            bullet.move()
            
            # 检查是否超出边界
            if bullet.is_out_of_bounds():
                bullet.alive = False
                continue
            
            # 子弹与墙体碰撞
            for wall in self.walls:
                if wall.alive and bullet.collides_with(wall):
                    bullet.alive = False
                    if wall.destructible:
                        wall.alive = False
                        self.sound_manager.play("explosion")
                    break
            
            if not bullet.alive:
                continue
            
            # 子弹与坦克碰撞
            if bullet.is_player:
                # 玩家子弹击中敌人
                for enemy in self.enemies:
                    if enemy.alive and bullet.collides_with(enemy):
                        bullet.alive = False
                        enemy.alive = False
                        self.score += 100
                        self.sound_manager.play("explosion")
                        
                        # 更新最高分
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self._save_high_score()
                        break
            else:
                # 敌人子弹击中玩家
                if self.player and self.player.alive and bullet.collides_with(self.player):
                    bullet.alive = False
                    self.player.lives -= 1
                    self.sound_manager.play("explosion")
                    
                    if self.player.lives <= 0:
                        self.player.alive = False
                        self._game_over()
                    else:
                        # 玩家被击中后重置位置
                        self.player.x = WINDOW_WIDTH // 2 - TANK_SIZE // 2
                        self.player.y = WINDOW_HEIGHT - TANK_SIZE - 20
        
        # 清理死亡的子弹
        self.bullets = [b for b in self.bullets if b.alive]
        # 清理死亡的敌人
        self.enemies = [e for e in self.enemies if e.alive]
        # 清理被破坏的墙体
        self.walls = [w for w in self.walls if w.alive]
    
    def _spawn_enemies(self, current_time: int):
        """生成新的敌人"""
        settings = DIFFICULTY_SETTINGS[self.difficulty]
        
        # 检查是否需要生成新敌人
        if (len(self.enemies) < settings["enemy_count"] and 
            current_time - self.last_spawn_time > settings["spawn_interval"]):
            
            # 随机选择生成位置（顶部区域）
            x = random.randint(50, WINDOW_WIDTH - TANK_SIZE - 50)
            y = random.randint(CONTROL_PANEL_HEIGHT + 20, CONTROL_PANEL_HEIGHT + 150)
            
            # 检查是否与现有物体重叠
            new_enemy = EnemyTank(x, y, settings["enemy_speed"])
            overlap = False
            
            for enemy in self.enemies:
                if new_enemy.collides_with(enemy):
                    overlap = True
                    break
            
            for wall in self.walls:
                if new_enemy.collides_with(wall):
                    overlap = True
                    break
            
            if not overlap:
                self.enemies.append(new_enemy)
                self.last_spawn_time = current_time
    
    def _game_over(self):
        """处理游戏结束"""
        self.game_over = True
        self.sound_manager.play("game_over")
        
        # 显示游戏结束界面
        self.canvas.itemconfig(self.game_over_overlay, state="normal")
        self.canvas.itemconfig(self.game_over_text, state="normal")
        self.canvas.itemconfig(
            self.final_score_text, 
            text=f"最终得分: {self.score}  最高分: {self.high_score}",
            state="normal"
        )
        self.canvas.itemconfig(self.restart_button_window, state="normal")
    
    def draw(self):
        """绘制游戏画面"""
        # 清空画布（保留UI元素）
        self.canvas.delete("game_object")
        
        # 绘制墙体
        for wall in self.walls:
            self.canvas.create_rectangle(
                wall.x, wall.y, wall.x + wall.width, wall.y + wall.height,
                fill=wall.color, outline="#333", width=1, tags="game_object"
            )
        
        # 绘制玩家坦克
        if self.player and self.player.alive:
            self._draw_tank(self.player, True)
        
        # 绘制敌人坦克
        for enemy in self.enemies:
            self._draw_tank(enemy, False)
        
        # 绘制子弹
        for bullet in self.bullets:
            color = COLOR_BULLET_PLAYER if bullet.is_player else COLOR_BULLET_ENEMY
            self.canvas.create_oval(
                bullet.x, bullet.y, bullet.x + bullet.width, bullet.y + bullet.height,
                fill=color, outline="", tags="game_object"
            )
    
    def _draw_tank(self, tank: Tank, is_player: bool):
        """
        绘制坦克
        
        Args:
            tank: 坦克对象
            is_player: 是否为玩家坦克
        """
        x, y = tank.x, tank.y
        size = tank.width
        color = tank.color
        direction = tank.direction
        
        # 坦克主体（矩形）
        self.canvas.create_rectangle(
            x + 2, y + 2, x + size - 2, y + size - 2,
            fill=color, outline="#333", width=2, tags="game_object"
        )
        
        # 炮塔（中心圆形）
        center_x = x + size // 2
        center_y = y + size // 2
        self.canvas.create_oval(
            center_x - 6, center_y - 6, center_x + 6, center_y + 6,
            fill="#333", outline="", tags="game_object"
        )
        
        # 炮管（根据方向绘制）
        barrel_length = 12
        barrel_width = 4
        
        if direction == DIRECTION_UP:
            bx1, by1 = center_x - barrel_width // 2, y - barrel_length
            bx2, by2 = center_x + barrel_width // 2, center_y
        elif direction == DIRECTION_RIGHT:
            bx1, by1 = center_x, center_y - barrel_width // 2
            bx2, by2 = x + size + barrel_length, center_y + barrel_width // 2
        elif direction == DIRECTION_DOWN:
            bx1, by1 = center_x - barrel_width // 2, center_y
            bx2, by2 = center_x + barrel_width // 2, y + size + barrel_length
        else:  # LEFT
            bx1, by1 = x - barrel_length, center_y - barrel_width // 2
            bx2, by2 = center_x, center_y + barrel_width // 2
        
        self.canvas.create_rectangle(
            bx1, by1, bx2, by2,
            fill="#333", outline="", tags="game_object"
        )
        
        # 履带细节
        track_color = "#222"
        if direction in [DIRECTION_UP, DIRECTION_DOWN]:
            # 垂直方向，履带在左右
            self.canvas.create_rectangle(
                x, y + 3, x + 4, y + size - 3,
                fill=track_color, outline="", tags="game_object"
            )
            self.canvas.create_rectangle(
                x + size - 4, y + 3, x + size, y + size - 3,
                fill=track_color, outline="", tags="game_object"
            )
        else:
            # 水平方向，履带在上下
            self.canvas.create_rectangle(
                x + 3, y, x + size - 3, y + 4,
                fill=track_color, outline="", tags="game_object"
            )
            self.canvas.create_rectangle(
                x + 3, y + size - 4, x + size - 3, y + size,
                fill=track_color, outline="", tags="game_object"
            )


# ==================== 主程序入口 ====================

def main():
    """游戏主入口函数"""
    root = tk.Tk()
    
    # 创建游戏实例
    game = TankGame(root)
    
    # 启动主循环
    root.mainloop()


if __name__ == "__main__":
    main()6
