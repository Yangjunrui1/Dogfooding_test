"""
坦克大战小游戏
使用Python + Tkinter开发
依赖安装: pip install pygame
音效文件需放置在与主程序同目录下：
- shoot.wav     发射子弹音效
- explosion.wav 击中敌人音效
- game_over.wav 游戏结束音效
"""

import tkinter as tk
from tkinter import ttk
import random
import os
import time

# 尝试导入pygame用于音效播放
try:
    import pygame
    pygame.mixer.init()
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False
    print("pygame未安装，将使用静音模式。安装命令: pip install pygame")
except pygame.error:
    SOUND_AVAILABLE = False
    print("音频初始化失败，将使用静音模式。")

# 游戏配置
GAME_WIDTH = 800
GAME_HEIGHT = 600
TANK_SIZE = 40
BULLET_SIZE = 8
BULLET_SPEED = 10
WALL_SIZE = 40

# 方向定义
UP = 0
DOWN = 1
LEFT = 2
RIGHT = 3

# 颜色定义
COLOR_PLAYER = "#00FF00"
COLOR_ENEMY = "#FF0000"
COLOR_BULLET_PLAYER = "#FFFF00"
COLOR_BULLET_ENEMY = "#FF6600"
COLOR_WALL = "#8B4513"
COLOR_GROUND = "#2F4F4F"


class Tank:
    """坦克基类"""
    def __init__(self, x, y, color, direction=UP):
        self.x = x
        self.y = y
        self.color = color
        self.direction = direction
        self.speed = 3
        self.size = TANK_SIZE
        self.last_shot = 0
        self.shoot_cooldown = 500  # 射击冷却时间(ms)
    
    def move(self, direction, walls, tanks):
        """移动坦克"""
        self.direction = direction
        new_x, new_y = self.x, self.y
        
        if direction == UP:
            new_y -= self.speed
        elif direction == DOWN:
            new_y += self.speed
        elif direction == LEFT:
            new_x -= self.speed
        elif direction == RIGHT:
            new_x += self.speed
        
        # 边界检测
        if 0 <= new_x <= GAME_WIDTH - self.size and 0 <= new_y <= GAME_HEIGHT - self.size:
            # 墙体碰撞检测
            if not self.check_collision(new_x, new_y, walls, tanks):
                self.x, self.y = new_x, new_y
    
    def check_collision(self, x, y, walls, tanks):
        """检测碰撞"""
        tank_rect = (x, y, x + self.size, y + self.size)
        
        # 检测与墙体碰撞
        for wall in walls:
            if self.rect_overlap(tank_rect, wall.get_rect()):
                return True
        
        # 检测与其他坦克碰撞
        for tank in tanks:
            if tank != self:
                if self.rect_overlap(tank_rect, (tank.x, tank.y, tank.x + tank.size, tank.y + tank.size)):
                    return True
        return False
    
    def rect_overlap(self, rect1, rect2):
        """检测两个矩形是否重叠"""
        x1_1, y1_1, x2_1, y2_1 = rect1
        x1_2, y1_2, x2_2, y2_2 = rect2
        return not (x2_1 <= x1_2 or x1_1 >= x2_2 or y2_1 <= y1_2 or y1_1 >= y2_2)
    
    def shoot(self):
        """发射子弹"""
        current_time = int(time.time() * 1000)
        if current_time - self.last_shot >= self.shoot_cooldown:
            self.last_shot = current_time
            # 根据方向计算子弹起始位置
            if self.direction == UP:
                bx = self.x + self.size // 2 - BULLET_SIZE // 2
                by = self.y - BULLET_SIZE
            elif self.direction == DOWN:
                bx = self.x + self.size // 2 - BULLET_SIZE // 2
                by = self.y + self.size
            elif self.direction == LEFT:
                bx = self.x - BULLET_SIZE
                by = self.y + self.size // 2 - BULLET_SIZE // 2
            else:  # RIGHT
                    bx = self.x + self.size
                    by = self.y + self.size // 2 - BULLET_SIZE // 2
            return Bullet(bx, by, self.direction, self.color == COLOR_PLAYER)
        return None
    
    def get_rect(self):
        """获取坦克矩形区域"""
        return (self.x, self.y, self.x + self.size, self.y + self.size)
    
    def draw(self, canvas):
        """绘制坦克"""
        # 坦克主体
        canvas.create_rectangle(self.x + 5, self.y + 5, 
                              self.x + self.size - 5, self.y + self.size - 5,
                              fill=self.color, outline=self.color)
        # 坦克炮管
        cx, cy = self.x + self.size // 2, self.y + self.size // 2
        if self.direction == UP:
            canvas.create_line(cx, cy, cx, self.y, width=4, fill=self.color)
        elif self.direction == DOWN:
            canvas.create_line(cx, cy, cx, self.y + self.size, width=4, fill=self.color)
        elif self.direction == LEFT:
            canvas.create_line(cx, cy, self.x, cy, width=4, fill=self.color)
        elif self.direction == RIGHT:
            canvas.create_line(cx, cy, self.x + self.size, cy, width=4, fill=self.color)
        # 坦克轮子（简化版）
        canvas.create_rectangle(self.x, self.y + 10, self.x + 5, self.y + self.size - 10, fill="#333")
        canvas.create_rectangle(self.x + self.size - 5, self.y + 10, self.x + self.size, self.y + self.size - 10, fill="#333")


class Bullet:
    """子弹类"""
    def __init__(self, x, y, direction, is_player):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = BULLET_SPEED
        self.size = BULLET_SIZE
        self.is_player = is_player  # True表示玩家子弹，False表示敌方子弹
        self.active = True
    
    def move(self):
        """移动子弹"""
        if self.direction == UP:
            self.y -= self.speed
        elif self.direction == DOWN:
            self.y += self.speed
        elif self.direction == LEFT:
            self.x -= self.speed
        elif self.direction == RIGHT:
            self.x += self.speed
        
        # 边界检测
        if self.x < 0 or self.x > GAME_WIDTH or self.y < 0 or self.y > GAME_HEIGHT:
            self.active = False
    
    def get_rect(self):
        """获取子弹矩形区域"""
        return (self.x, self.y, self.x + self.size, self.y + self.size)
    
    def draw(self, canvas):
        """绘制子弹"""
        color = COLOR_BULLET_PLAYER if self.is_player else COLOR_BULLET_ENEMY
        canvas.create_oval(self.x, self.y, self.x + self.size, self.y + self.size, fill=color, outline=color)


class Wall:
    """墙体类"""
    def __init__(self, x, y, destructible=True):
        self.x = x
        self.y = y
        self.size = WALL_SIZE
        self.destructible = destructible
        self.health = 2  # 可破坏墙体需要2发子弹
    
    def get_rect(self):
        """获取墙体矩形区域"""
        return (self.x, self.y, self.x + self.size, self.y + self.size)
    
    def hit(self):
        """被子弹击中"""
        if self.destructible:
            self.health -= 1
            return self.health <= 0
        return False
    
    def draw(self, canvas):
        """绘制墙体"""
        canvas.create_rectangle(self.x, self.y, 
                              self.x + self.size, self.y + self.size,
                              fill=COLOR_WALL, outline="#654321")
        # 绘制砖块纹理
        for i in range(2):
            for j in range(2):
                canvas.create_rectangle(
                    self.x + i * (self.size//2) + 2,
                    self.y + j * (self.size//2) + 2,
                    self.x + (i+1) * (self.size//2) - 2,
                    self.y + (j+1) * (self.size//2) - 2,
                    fill="#A0522D", outline="#8B4513")


class TankGame:
    """坦克大战游戏主类"""
    def __init__(self, root):
        self.root = root
        self.root.title("坦克大战")
        self.root.resizable(False, False)
        
        # 游戏状态
        self.game_state = "menu"  # menu, playing, paused, game_over
        self.score = 0
        self.high_score = self.load_high_score()
        self.lives = 3
        self.difficulty = "medium"
        self.difficulty_settings = {
            "easy": {"enemy_count": 3, "enemy_speed": 2, "shoot_rate": 0.005},
            "medium": {"enemy_count": 5, "enemy_speed": 3, "shoot_rate": 0.01},
            "hard": {"enemy_count": 7, "enemy_speed": 4, "shoot_rate": 0.02}
        }
        
        # 音效加载
        self.sounds = {}
        if SOUND_AVAILABLE:
            self.load_sounds()
        
        # 创建UI
        self.create_ui()
        
        # 绑定键盘事件
        self.bind_events()
        
        # 初始化游戏对象
        self.init_game()
    
    def load_high_score(self):
        """加载最高分"""
        try:
            if os.path.exists("tank_high_score.txt"):
                with open("tank_high_score.txt", "r") as f:
                    return int(f.read().strip() or 0)
            else:
                with open("tank_high_score.txt", "w") as f:
                    f.write("0")
                return 0
        except:
            return 0
    
    def save_high_score(self):
        """保存最高分"""
        try:
            with open("tank_high_score.txt", "w") as f:
                f.write(str(self.high_score))
        except:
            pass
    
    def load_sounds(self):
        """加载音效文件"""
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
                    print(f"音效文件 {filename} 不存在，将跳过此音效。")
            except:
                print(f"加载音效 {filename} 失败。")
    
    def play_sound(self, name):
        """播放音效"""
        if SOUND_AVAILABLE and name in self.sounds:
            try:
                self.sounds[name].play()
            except:
                pass
    
    def create_ui(self):
        """创建游戏界面"""
        # 顶部控制区
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 难度按钮
        ttk.Button(control_frame, text="简单", command=lambda: self.set_difficulty("easy")).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="中等", command=lambda: self.set_difficulty("medium")).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="困难", command=lambda: self.set_difficulty("hard")).pack(side=tk.LEFT, padx=5)
        
        # 状态显示
        self.status_label = ttk.Label(control_frame, text=f"分数: {self.score}")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        self.lives_label = ttk.Label(control_frame, text=f"生命: {self.lives}")
        self.lives_label.pack(side=tk.LEFT, padx=10)
        
        self.high_score_label = ttk.Label(control_frame, text=f"最高分: {self.high_score}")
        self.high_score_label.pack(side=tk.LEFT, padx=10)
        
        # 游戏画布
        self.canvas = tk.Canvas(self.root, width=GAME_WIDTH, height=GAME_HEIGHT, bg=COLOR_GROUND)
        self.canvas.pack(padx=5, pady=5)
    
    def bind_events(self):
        """绑定键盘事件"""
        self.root.bind("<KeyPress>", self.on_key_press)
        self.root.bind("<KeyRelease>", self.on_key_release)
    
    def on_key_press(self, event):
        """键盘按下事件"""
        if event.keysym == "space":
            if self.game_state == "playing":
                bullet = self.player.shoot()
                if bullet:
                    self.bullets.append(bullet)
                    self.play_sound("shoot")
            elif self.game_state == "paused":
                self.resume_game()
            elif self.game_state == "menu":
                self.start_game()
        elif event.keysym in ["Up", "Down", "Left", "Right"]:
            if self.game_state == "playing":
                direction = {"Up": UP, "Down": DOWN, "Left": LEFT, "Right": RIGHT}[event.keysym]
                self.player.move(direction, self.walls, [self.player] + self.enemies)
    
    def on_key_release(self, event):
        """键盘释放事件"""
        pass
    
    def set_difficulty(self, difficulty):
        """设置难度"""
        self.difficulty = difficulty
        if self.game_state == "menu":
            self.init_game()
    
    def init_game(self):
        """初始化游戏"""
        # 清空游戏对象
        self.player = Tank(GAME_WIDTH//2 - TANK_SIZE//2, GAME_HEIGHT - TANK_SIZE - 20, COLOR_PLAYER, UP)
        self.enemies = []
        self.bullets = []
        self.walls = []
        self.score = 0
        self.lives = 3
        self.game_state = "menu"
        
        # 生成墙体
        self.generate_walls()
        
        # 生成初始敌人
        self.generate_enemies()
        
        # 更新UI
        self.update_ui()
        
        # 绘制游戏
        self.draw()
    
    def generate_walls(self):
        """生成墙体"""
        wall_positions = [
            (100, 100), (100, 180), (100, 260),
            (200, 200), (200, 280),
            (300, 100), (300, 300),
            (400, 150), (400, 250),
            (500, 100), (500, 200),
            (600, 150), (600, 250), (600, 350),
            (150, 400), (250, 450), (350, 400),
            (450, 450), (550, 400),
            (700, 100), (700, 200), (700, 300),
        ]
        for x, y in wall_positions:
            self.walls.append(Wall(x, y, destructible=True))
        
        # 添加一些不可破坏的墙体
        for x, y in [(0, 300), (400, 0), (400, 100)]:
            self.walls.append(Wall(x, y, destructible=False))
    
    def generate_enemies(self):
        """生成敌方坦克"""
        settings = self.difficulty_settings[self.difficulty]
        while len(self.enemies) < settings["enemy_count"]:
            x = random.randint(0, GAME_WIDTH - TANK_SIZE)
            y = random.randint(0, GAME_HEIGHT//2 - TANK_SIZE)
            enemy = Tank(x, y, COLOR_ENEMY, random.choice([UP, DOWN, LEFT, RIGHT]))
            enemy.speed = settings["enemy_speed"]
            enemy.shoot_cooldown = int(1000 / settings["shoot_rate"])
            if not enemy.check_collision(x, y, self.walls, self.enemies):
                self.enemies.append(enemy)
    
    def start_game(self):
        """开始游戏"""
        self.game_state = "playing"
        self.game_loop()
    
    def pause_game(self):
        """暂停游戏"""
        self.game_state = "paused"
    
    def resume_game(self):
        """继续游戏"""
        self.game_state = "playing"
        self.game_loop()
    
    def game_over(self):
        """游戏结束"""
        self.game_state = "game_over"
        self.play_sound("game_over")
        # 更新最高分
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
        self.update_ui()
    
    def update_ui(self):
        """更新UI显示"""
        self.status_label.config(text=f"分数: {self.score}")
        self.lives_label.config(text=f"生命: {self.lives}")
        self.high_score_label.config(text=f"最高分: {self.high_score}")
    
    def game_loop(self):
        """游戏主循环"""
        if self.game_state != "playing":
            return
        
        # 更新敌方坦克
        self.update_enemies()
        
        # 更新子弹
        self.update_bullets()
        
        # 检测碰撞
        self.check_collisions()
        
        # 补充敌人
        self.generate_enemies()
        
        # 绘制
        self.draw()
        
        # 继续循环
        self.root.after(30, self.game_loop)
    
    def update_enemies(self):
        """更新敌方坦克状态"""
        settings = self.difficulty_settings[self.difficulty]
        for enemy in self.enemies[:]:
            # 随机移动
            if random.random() < 0.02:
                enemy.direction = random.choice([UP, DOWN, LEFT, RIGHT])
            enemy.move(enemy.direction, self.walls, [self.player] + self.enemies)
            
            # 随机射击
            if random.random() < settings["shoot_rate"]:
                bullet = enemy.shoot()
                if bullet:
                    self.bullets.append(bullet)
    
    def update_bullets(self):
        """更新子弹状态"""
        for bullet in self.bullets[:]:
            bullet.move()
            if not bullet.active:
                self.bullets.remove(bullet)
                continue
            
            # 检测子弹与墙体碰撞
            for wall in self.walls[:]:
                if self.rect_overlap(bullet.get_rect(), wall.get_rect()):
                    if wall.hit():
                        self.walls.remove(wall)
                    self.bullets.remove(bullet)
                    break
    
    def check_collisions(self):
        """检测碰撞"""
        # 玩家子弹击中敌人
        for bullet in self.bullets[:]:
            if bullet.is_player:
                for enemy in self.enemies[:]:
                    if self.rect_overlap(bullet.get_rect(), enemy.get_rect()):
                        self.bullets.remove(bullet)
                        self.enemies.remove(enemy)
                        self.score += 100
                        self.play_sound("explosion")
                        self.update_ui()
                        break
            else:
                # 敌方子弹击中玩家
                if self.rect_overlap(bullet.get_rect(), self.player.get_rect()):
                    self.bullets.remove(bullet)
                    self.lives -= 1
                    self.update_ui()
                    if self.lives <= 0:
                        self.game_over()
                    break
    
    def rect_overlap(self, rect1, rect2):
        """检测矩形重叠"""
        x1_1, y1_1, x2_1, y2_1 = rect1
        x1_2, y1_2, x2_2, y2_2 = rect2
        return not (x2_1 <= x1_2 or x1_1 >= x2_2 or y2_1 <= y1_2 or y1_1 >= y2_2)
    
    def draw(self):
        """绘制游戏"""
        self.canvas.delete(tk.ALL)
        
        # 绘制墙体
        for wall in self.walls:
            wall.draw(self.canvas)
        
        # 绘制玩家坦克
        self.player.draw(self.canvas)
        
        # 绘制敌方坦克
        for enemy in self.enemies:
            enemy.draw(self.canvas)
        
        # 绘制子弹
        for bullet in self.bullets:
            bullet.draw(self.canvas)
        
        # 绘制暂停提示
        if self.game_state == "paused":
            self.canvas.create_rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, fill="black", stipple="gray50")
            self.canvas.create_text(GAME_WIDTH//2, GAME_HEIGHT//2, text="游戏暂停", 
                                   fill="white", font=("Arial", 36, "bold"))
        
        # 绘制游戏结束提示
        elif self.game_state == "game_over":
            self.canvas.create_rectangle(0, 0, GAME_WIDTH, GAME_HEIGHT, fill="black", stipple="gray50")
            self.canvas.create_text(GAME_WIDTH//2, GAME_HEIGHT//2 - 50, text="游戏结束", 
                                   fill="red", font=("Arial", 48, "bold"))
            self.canvas.create_text(GAME_WIDTH//2, GAME_HEIGHT//2 + 20, text=f"得分: {self.score}", 
                                   fill="yellow", font=("Arial", 24))
            # 重新开始按钮
            restart_btn = ttk.Button(self.canvas, text="重新开始", command=self.restart_game)
            self.canvas.create_window(GAME_WIDTH//2, GAME_HEIGHT//2 + 80, window=restart_btn)
        
        # 菜单状态
        elif self.game_state == "menu":
            self.canvas.create_text(GAME_WIDTH//2, GAME_HEIGHT//2 - 50, text="坦克大战", 
                                   fill="yellow", font=("Arial", 48, "bold"))
            self.canvas.create_text(GAME_WIDTH//2, GAME_HEIGHT//2 + 20, text="按空格键开始游戏", 
                                   fill="white", font=("Arial", 20))
            self.canvas.create_text(GAME_WIDTH//2, GAME_HEIGHT//2 + 60, text="方向键移动，空格键发射", 
                                   fill="lightgray", font=("Arial", 14))
    
    def restart_game(self):
        """重新开始游戏"""
        self.init_game()
        self.start_game()


if __name__ == "__main__":
    root = tk.Tk()
    game = TankGame(root)
    root.mainloop()
