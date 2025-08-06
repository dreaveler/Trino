import sys
import random
import os
from card import UnoCard
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, 
                             QDialog, QHBoxLayout, QLabel, QComboBox, QListWidget, 
                             QListWidgetItem, QInputDialog, QDialogButtonBox, QGridLayout,
                             QScrollArea, QTextEdit, QStackedLayout, QLayout, 
                             QSpacerItem, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush
from player import AIPlayer, HumanPlayer

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def get_card_image_path(card):
    """全局函数，用于获取卡牌图片路径"""
    if card is None:
        return resource_path(os.path.join('images', 'uno_images', 'back.png'))
        
    color = card.color
    type_ = card.type
    value = card.value
    
    base = os.path.join('images', 'uno_images')

    if type_ == 'number':
        filename = f'{color}_{value}.png'
    elif type_ == 'draw2':
        filename = f'{color}_+2.png'
    elif type_ == 'reverse':
        filename = f'{color}_reverse.png'
    elif type_ == 'skip':
        filename = f'{color}_skip.png'
    elif type_ == 'wild':
        filename = 'black_wildcard.png'
    elif type_ == 'wild_draw4':
        filename = 'black_+4.png'
    else:
        filename = 'back.png'
        
    return resource_path(os.path.join(base, filename))

def get_faction_image_path(team):
    """获取势力图片的路径"""
    relative_path = os.path.join('images', f'{team}.png')
    full_path = resource_path(relative_path)
    
    # 检查文件是否存在，如果不存在，可以返回一个None或者默认图片路径
    if os.path.exists(full_path):
        return full_path
    return None

class PlayerInfoWidget(QWidget):
    """用于显示单个玩家信息的组件，模仿三国杀武将栏"""
    def __init__(self, player, is_main_player=False, is_current=False, parent=None):
        super().__init__(parent)
        self.player = player
        self.is_main_player = is_main_player
        self.is_current = is_current
        
        # 根据是否是主玩家，使用不同的布局和尺寸
        if self.is_main_player:
            self.layout = QHBoxLayout(self)
            self.layout.setContentsMargins(10, 5, 10, 5)
            self.hero_image_size = (150, 210)
            self.faction_image_size = (45, 45)
            self.font_size_name = "20px"
            self.font_size_hand = "20px"
        else: # 其他玩家，更紧凑
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(5, 5, 5, 5)
            self.hero_image_size = (100, 140)
            self.faction_image_size = (30, 30)
            self.font_size_name = "16px"
            self.font_size_hand = "18px"
            
        self.layout.setSpacing(5)
        
        # 存储基准尺寸用于缩放
        self.base_hero_image_size = self.hero_image_size
        self.base_faction_image_size = self.faction_image_size
        self.base_font_size_name = int(self.font_size_name.replace('px', ''))
        self.base_font_size_hand = int(self.font_size_hand.replace('px', ''))

        # --- 武将及势力图片区域 ---
        self.hero_image_container = QWidget()
        hero_image_layout = QGridLayout(self.hero_image_container)
        hero_image_layout.setContentsMargins(0, 0, 0, 0)

        self.hero_image_label = QLabel()
        if player.mr_card and player.mr_card.image_path:
            pixmap = QPixmap(resource_path(os.path.join('images', player.mr_card.image_path)))
            self.hero_image_label.setPixmap(pixmap.scaled(self.hero_image_size[0], self.hero_image_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.hero_image_label.setAlignment(Qt.AlignCenter)
        hero_image_layout.addWidget(self.hero_image_label, 0, 0, Qt.AlignCenter)

        self.faction_image_label = QLabel()
        faction_path = get_faction_image_path(player.team)
        if faction_path:
            pixmap = QPixmap(faction_path)
            self.faction_image_label.setPixmap(pixmap.scaled(self.faction_image_size[0], self.faction_image_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.faction_image_label.setFixedSize(self.faction_image_size[0], self.faction_image_size[1])
            hero_image_layout.addWidget(self.faction_image_label, 0, 0, Qt.AlignTop | Qt.AlignLeft)
            self.faction_image_label.setContentsMargins(0, 2, 0, 0)

        # --- 文本信息区域 ---
        self.name_label = QLabel(f"<b>{player.mr_card.name}({player.position+1})</b>")
        self.hand_count_label = QLabel(f"手牌: {len(player.uno_list)}")
        
        # 检查是否应该显示UNO标签（标准UNO规则或恃才技能）
        should_show_uno = player.uno_state  # 标准UNO规则（1张牌）
        if not should_show_uno and player.mr_card:
            # 检查恃才技能（2张牌时显示UNO）
            shicai_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'ShiCai'), None)
            if shicai_skill and len(player.uno_list) == 2:
                should_show_uno = True
        
        self.uno_state_label = QLabel("UNO!") if should_show_uno else QLabel("")
        
        self.name_label.setAlignment(Qt.AlignCenter)
        self.hand_count_label.setAlignment(Qt.AlignCenter)
        self.uno_state_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"font-size: {self.font_size_name}; color: white; font-weight: bold; background: transparent;")
        self.hand_count_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: white; background: transparent;")
        self.uno_state_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: #FFD700; font-weight: bold; background: transparent;")
        
        self.layout.addWidget(self.hero_image_container)

        if self.is_main_player:
            # 主玩家信息在右侧
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            info_layout.setContentsMargins(0,0,0,0)
            info_layout.setAlignment(Qt.AlignCenter)
            info_layout.addWidget(self.name_label)
            info_layout.addWidget(self.hand_count_label)
            info_layout.addWidget(self.uno_state_label)
            info_layout.addStretch()
            self.layout.addWidget(info_widget)
        else: # 其他玩家信息在图片下方
            self.layout.addWidget(self.name_label)
            self.layout.addWidget(self.hand_count_label)
            self.layout.addWidget(self.uno_state_label)

        # 调整组件大小策略，使其紧凑
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.update_style()

    def update_info(self, player, is_current):
        """更新信息"""
        self.player = player
        self.is_current = is_current
        try:
            if hasattr(self, 'hand_count_label') and self.hand_count_label is not None:
                self.hand_count_label.setText(f"手牌: {len(player.uno_list)}")
            if hasattr(self, 'uno_state_label') and self.uno_state_label is not None:
                # 检查是否应该显示UNO标签（标准UNO规则或恃才技能）
                should_show_uno = player.uno_state  # 标准UNO规则（1张牌）
                if not should_show_uno and player.mr_card:
                    # 检查恃才技能（2张牌时显示UNO）
                    shicai_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'ShiCai'), None)
                    if shicai_skill and len(player.uno_list) == 2:
                        should_show_uno = True
                
                if should_show_uno:
                    self.uno_state_label.setText("UNO!")
                    self.uno_state_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: #FFD700; font-weight: bold; background: transparent;")
                else:
                    self.uno_state_label.setText("")
        except RuntimeError:
            pass
        self.update_style()

    def update_style(self):
        """根据是否为当前玩家更新样式"""
        border_color = "#FFD700" if self.is_current else "#34495e"
        border_width = 4 if self.is_current else 2 # Current player gets thicker border
        bg_color = "rgba(139, 0, 0, 0.8)" if self.is_current else "rgba(44, 62, 80, 0.7)"
        self.setStyleSheet(f"""
            PlayerInfoWidget {{
                background-color: {bg_color}; 
                border: {border_width}px solid {border_color}; 
                border-radius: 10px;
            }}
        """)
    
    def update_scaling(self, scale_factor):
        """更新缩放"""
        # 更新武将图片尺寸
        scaled_hero_width = int(self.base_hero_image_size[0] * scale_factor)
        scaled_hero_height = int(self.base_hero_image_size[1] * scale_factor)
        self.hero_image_size = (scaled_hero_width, scaled_hero_height)
        
        # 更新势力图片尺寸
        scaled_faction_width = int(self.base_faction_image_size[0] * scale_factor)
        scaled_faction_height = int(self.base_faction_image_size[1] * scale_factor)
        self.faction_image_size = (scaled_faction_width, scaled_faction_height)
        
        # 更新字体大小
        scaled_name_font = int(self.base_font_size_name * scale_factor)
        scaled_hand_font = int(self.base_font_size_hand * scale_factor)
        self.font_size_name = f"{scaled_name_font}px"
        self.font_size_hand = f"{scaled_hand_font}px"
        
        # 重新设置武将图片
        if self.player.mr_card and self.player.mr_card.image_path:
            pixmap = QPixmap(resource_path(os.path.join('images', self.player.mr_card.image_path)))
            self.hero_image_label.setPixmap(pixmap.scaled(self.hero_image_size[0], self.hero_image_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # 重新设置势力图片
        faction_path = get_faction_image_path(self.player.team)
        if faction_path:
            faction_pixmap = QPixmap(faction_path)
            self.faction_image_label.setPixmap(faction_pixmap.scaled(self.faction_image_size[0], self.faction_image_size[1], Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        # 更新字体大小
        self.name_label.setStyleSheet(f"font-size: {self.font_size_name}; color: white; font-weight: bold; background: transparent;")
        self.hand_count_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: white; background: transparent;")
        
        # 更新UNO标签字体大小
        if hasattr(self, 'uno_state_label') and self.uno_state_label is not None:
            if self.uno_state_label.text() == "UNO!":
                self.uno_state_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: #FFD700; font-weight: bold; background: transparent;")
            else:
                self.uno_state_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: white; background: transparent;")

class ModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('选择模式')
        layout = QVBoxLayout(self)
        
        label = QLabel('请选择游戏模式:')
        self.combo = QComboBox()
        self.combo.addItems(['身份局', '国战', '1v1'])
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(label)
        layout.addWidget(self.combo)
        layout.addWidget(buttons)
        
    @property
    def selected_mode(self):
        return self.combo.currentText()

class SelectHeroDialog(QDialog):
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        from mr_cards import all_heroes
        import random
        self.main_window = parent
        self.mode = mode
        self.all_heroes = list(all_heroes.keys())
        
        # 随机选择三个武将供玩家选择
        self.available_heroes = random.sample(self.all_heroes, min(3, len(self.all_heroes)))
        print(f"选择的武将: {self.available_heroes}")  # 调试信息
        self.selected_hero = None
        
        self.setWindowTitle('选择你的武将')
        # 固定窗口大小，不使用弹性区域
        self.setFixedSize(1600, 1000)
        
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 设置对话框本身的背景图片
        background_path = resource_path(os.path.join('images', 'choose_mr_background.jpg'))
        print(f"背景图片路径: {background_path}")
        print(f"文件是否存在: {os.path.exists(background_path)}")
        if os.path.exists(background_path):
            try:
                # 使用QPalette设置背景图片，确保完全填充窗口
                pixmap = QPixmap(background_path)
                if not pixmap.isNull():
                    # 缩放到窗口大小，保持宽高比但填充整个窗口
                    scaled_pixmap = pixmap.scaled(
                        self.size(), 
                        Qt.KeepAspectRatioByExpanding, 
                        Qt.SmoothTransformation
                    )
                    palette = self.palette()
                    palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
                    self.setPalette(palette)
                    self.setAutoFillBackground(True)
                    print("使用QPalette设置背景图片成功")
                else:
                    print("背景图片加载失败")
                    self.setStyleSheet("background-color: white;")
            except Exception as e:
                print(f"设置背景图片时出错: {e}")
                self.setStyleSheet("background-color: white;")
        else:
            print("背景图片文件不存在，使用白色背景")
            self.setStyleSheet("background-color: white;")
        
        # 添加弹性空间，将标题向下移动
        layout.addStretch(1)
        
        # 标题
        title_label = QLabel('请选择你的武将:')
        title_label.setStyleSheet("font-size: 28px; font-weight: bold; margin: 20px; background: transparent; color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 添加弹性空间，将内容推向顶部
        layout.addStretch(1)
        
        # 武将选择区域
        hero_widget = QWidget()
        hero_widget.setStyleSheet("background: transparent;")
        hero_layout = QHBoxLayout(hero_widget)
        hero_layout.setSpacing(10)
        hero_layout.setAlignment(Qt.AlignCenter)
        
        self.hero_buttons = []
        for hero_name in self.available_heroes:
            hero_card = all_heroes[hero_name]
            
            # 创建武将卡片容器
            card_widget = QWidget()
            card_widget.setFixedSize(400, 750)
            card_widget.setStyleSheet("""
                QWidget {
                    background-color: transparent;
                    border: none;
                    border-radius: 10px;
                    padding: 2px;
                }
                QWidget:hover {
                    background-color: rgba(227, 242, 253, 0.3);
                }
                QWidget[selected="true"] {
                    background-color: rgba(212, 237, 218, 0.5);
                }
            """)
            
            card_layout = QVBoxLayout(card_widget)
            card_layout.setSpacing(1)
            
            # 武将图片
            image_path = resource_path(os.path.join('images', hero_card.image_path))
            print(f"武将 {hero_name} 图片路径: {image_path}")  # 调试信息
            image_label = QLabel()
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    target_width = 380  # 与技能介绍信息栏宽度一致
                    target_height = int(target_width * 750 / 530)  # 约538
                    pixmap = pixmap.scaled(target_width, target_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    image_label.setPixmap(pixmap)
                else:
                    # 如果图片加载失败，显示默认文本
                    image_label.setText("图片加载失败")
                    image_label.setStyleSheet("color: #999; font-size: 16px;")
            else:
                # 如果图片文件不存在，显示默认文本
                image_label.setText("图片不存在")
                image_label.setStyleSheet("color: #999; font-size: 16px;")
            
            image_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(image_label)
            
            # 武将名称
            name_label = QLabel(hero_name)
            name_label.setStyleSheet("font-size: 24px; font-weight: bold; color: black; margin: 0px;")
            name_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(name_label)
            
            # 势力信息
            team_map = {'shu': '蜀', 'wei': '魏', 'wu': '吴', 'qun': '群'}
            team_text = team_map.get(hero_card.team, hero_card.team)
            team_label = QLabel(f"势力: {team_text}")
            team_label.setStyleSheet("font-size: 18px; color: black; margin: 0px;")
            team_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(team_label)
            
            # 技能描述（完整版）
            skill_label = QLabel(hero_card.skill_description)
            skill_label.setStyleSheet("font-size: 18px; color: black; margin: 0px; line-height: 1.0;")
            skill_label.setAlignment(Qt.AlignLeft)
            skill_label.setWordWrap(True)
            card_layout.addWidget(skill_label)
            
            # 特点信息
            if hasattr(hero_card, 'tags') and hero_card.tags:
                tags_label = QLabel(f"特点: {hero_card.tags}")
                tags_label.setStyleSheet("font-size: 18px; color: #333; margin: 0px; font-weight: bold;")
                tags_label.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(tags_label)
            
            # 难度信息
            if hasattr(hero_card, 'difficulty'):
                difficulty_label = QLabel(f"难度: {hero_card.difficulty}/10")
                difficulty_label.setStyleSheet("font-size: 18px; color: #333; margin: 0px; font-weight: bold;")
                difficulty_label.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(difficulty_label)
            
            # 使卡片可点击
            card_widget.hero_name = hero_name  # 存储武将名称
            card_widget.mousePressEvent = self.create_hero_click_handler(card_widget, hero_name)
            card_widget.setCursor(Qt.PointingHandCursor)
            
            self.hero_buttons.append((card_widget, hero_name))
            hero_layout.addWidget(card_widget)
        
        layout.addWidget(hero_widget)
        
        # 添加弹性空间，将按钮推向底部
        layout.addStretch(2)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignCenter)
        
        start_button = QPushButton('开始游戏')
        start_button.setFixedSize(240, 80)
        start_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        start_button.clicked.connect(self.start_game_action)
        start_button.setEnabled(False)  # 初始状态禁用，直到选择武将
        self.start_button = start_button
        
        button_layout.addWidget(start_button)
        layout.addLayout(button_layout)
        
        # 添加底部间距
        layout.addStretch(1)

    def create_hero_click_handler(self, widget, hero_name):
        """创建武将卡片点击事件处理器"""
        def handler(event):
            self.on_hero_clicked(widget, hero_name)
        return handler

    def on_hero_clicked(self, widget, hero_name):
        """处理武将卡片点击事件"""
        # 清除之前的选择
        for card_widget, _ in self.hero_buttons:
            card_widget.setProperty("selected", False)
            card_widget.style().unpolish(card_widget)
            card_widget.style().polish(card_widget)
        
        # 设置当前选择
        widget.setProperty("selected", True)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        
        self.selected_hero = hero_name
        self.start_button.setEnabled(True)

    def resizeEvent(self, event):
        """处理窗口大小改变事件，重新设置背景"""
        super().resizeEvent(event)
        # 重新设置背景图片以适应新的窗口大小
        background_path = resource_path(os.path.join('images', 'choose_mr_background.jpg'))
        if os.path.exists(background_path):
            try:
                pixmap = QPixmap(background_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.size(), 
                        Qt.KeepAspectRatioByExpanding, 
                        Qt.SmoothTransformation
                    )
                    palette = self.palette()
                    palette.setBrush(QPalette.Window, QBrush(scaled_pixmap))
                    self.setPalette(palette)
                    self.setAutoFillBackground(True)
            except Exception as e:
                print(f"重新设置背景图片时出错: {e}")

    def start_game_action(self):
        if not self.selected_hero:
            QMessageBox.warning(self, '提示', '请选择一个武将！')
            return
        
        player_hero = self.selected_hero
        
        # 从所有武将中移除已选择的武将
        remaining_heroes = [hero for hero in self.all_heroes if hero != player_hero]
        
        # 根据模式确定对手数量，这里暂时写死为2
        num_others = 2 
        if len(remaining_heroes) < num_others:
            # 如果不够，允许重复选择
            other_heros = random.choices(remaining_heroes, k=num_others)
        else:
            other_heros = random.sample(remaining_heroes, k=num_others)
            
        self.main_window.start_game(self.mode, player_hero, other_heros)
        self.accept()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.history_lines = []  # 提前初始化历史记录列表
        self.setWindowTitle('Trino 游戏')
        
        # 设置窗口大小和位置，考虑系统限制
        self.setMinimumSize(1200, 800)  # 设置最小尺寸
        self.resize(1600, 900)  # 使用resize而不是setGeometry
        self.move(100, 100)  # 单独设置位置
        
        # 设置窗口属性，避免尺寸警告
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        self.setAutoFillBackground(True) # 允许窗口自动填充背景
        self.wusheng_active = False # 武圣技能状态
        # 删除弃牌模式状态相关代码

        # 添加缩放相关属性
        self.base_width = 1600
        self.base_height = 900
        self.scale_factor = 1.0
        self.scaled_components = []  # 存储需要缩放的组件

        # 为所有对话框设置一个更明亮的全局样式
        QApplication.instance().setStyleSheet("""
            QMessageBox, QInputDialog {
                background-color: white; /* 将背景设置为纯白 */
                color: black;
            }
            QDialog QLabel, QMessageBox QLabel, QInputDialog QLabel {
                color: black;
            }
            QDialog QPushButton, QMessageBox QPushButton, QInputDialog QPushButton {
                background-color: #f0f0f0; /* 按钮用浅灰色 */
                border: 1px solid #adadad;
                padding: 5px;
                min-width: 60px;
                border-radius: 3px;
                color: black;
            }
            QDialog QPushButton:hover, QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {
                background-color: #e1e1e1;
            }
            QListWidget, QComboBox, QLineEdit {
                background-color: white;
                color: black;
                border: 1px solid #adadad;
            }
        """)

        self.main_layout = QVBoxLayout(self) # 先用QVBoxLayout容纳初始菜单
        self.game_widget = None # 游戏界面的主容器
        self.player_widgets = {}

        self._init_background() # 初始化背景
        self.show_main_menu()

    def calculate_scale_factor(self):
        """计算当前窗口相对于基准尺寸的缩放因子"""
        current_width = self.width()
        current_height = self.height()
        
        # 计算宽度和高度的缩放比例，取较小值以保持比例
        width_scale = current_width / self.base_width
        height_scale = current_height / self.base_height
        
        # 限制缩放范围，避免过小或过大
        scale_factor = min(width_scale, height_scale)
        scale_factor = max(0.5, min(scale_factor, 2.0))  # 限制在0.5到2.0之间
        
        return scale_factor

    def apply_scaling_to_component(self, component, base_size, base_font_size=None):
        """对单个组件应用缩放"""
        if component is None:
            return
            
        try:
            # 缩放尺寸
            if base_size:
                scaled_width = int(base_size[0] * self.scale_factor)
                scaled_height = int(base_size[1] * self.scale_factor)
                component.setFixedSize(scaled_width, scaled_height)
            
            # 缩放字体
            if base_font_size and hasattr(component, 'setStyleSheet'):
                scaled_font_size = int(base_font_size * self.scale_factor)
                current_style = component.styleSheet()
                # 更新字体大小
                import re
                current_style = re.sub(r'font-size:\s*\d+px', f'font-size: {scaled_font_size}px', current_style)
                component.setStyleSheet(current_style)
        except RuntimeError:
            # 组件已被删除，忽略错误
            pass

    def update_all_scaled_components(self):
        """更新所有需要缩放的组件"""
        # 创建临时列表来存储有效的组件，避免在迭代时修改列表
        valid_components = []
        for component_info in self.scaled_components:
            component, base_size, base_font_size = component_info
            try:
                # 检查组件是否仍然有效
                if component is not None and not component.isHidden():
                    self.apply_scaling_to_component(component, base_size, base_font_size)
                    valid_components.append(component_info)
            except RuntimeError:
                # 组件已被删除，跳过
                continue
        
        # 更新缩放组件列表，只保留有效的组件
        self.scaled_components = valid_components
        
        # 更新PlayerInfoWidget的缩放
        for player_widget in self.player_widgets.values():
            if hasattr(player_widget, 'update_scaling'):
                try:
                    player_widget.update_scaling(self.scale_factor)
                except RuntimeError:
                    # 如果PlayerInfoWidget已被删除，跳过
                    continue

    def add_scaled_component(self, component, base_size=None, base_font_size=None):
        """添加需要缩放的组件到列表"""
        self.scaled_components.append((component, base_size, base_font_size))
        # 立即应用当前缩放
        self.apply_scaling_to_component(component, base_size, base_font_size)

    def resizeEvent(self, event):
        """处理窗口大小改变事件，重新设置背景和缩放"""
        # 计算新的缩放因子
        new_scale_factor = self.calculate_scale_factor()
        
        # 如果缩放因子发生变化，更新所有组件
        if abs(new_scale_factor - self.scale_factor) > 0.01:  # 避免微小变化
            self.scale_factor = new_scale_factor
            self.update_all_scaled_components()
        
        self._init_background()
        super().resizeEvent(event)

    def _init_background(self):
        """初始化并设置窗口背景图片"""
        palette = QPalette()
        pixmap = QPixmap(resource_path(os.path.join('images', 'background.jpg')))
        if not pixmap.isNull():
            brush = QBrush(pixmap.scaled(self.size(), Qt.KeepAspectRatioByExpanding))
            palette.setBrush(QPalette.Window, brush)
            self.setPalette(palette)

    def show_main_menu(self):
        """显示主菜单"""
        self.clear_window()
        
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setAlignment(Qt.AlignCenter)
        menu_layout.setSpacing(20)

        self.start_btn = QPushButton('开始游戏(三足鼎立)')
        self.hero_btn = QPushButton('武将图鉴')
        self.rule_btn = QPushButton('游戏规则')
        self.exit_btn = QPushButton('退出游戏')

        self.btns = [self.start_btn, self.hero_btn, self.rule_btn, self.exit_btn]
        for btn in self.btns:
            # 添加按钮到缩放系统
            self.add_scaled_component(btn, base_size=(200, 50), base_font_size=20)
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 20px; color: white; background-color: #2980b9; 
                    border: 2px solid #3498db; border-radius: 10px;
                }
                QPushButton:hover { background-color: #3498db; }
            """)
            menu_layout.addWidget(btn)

        self.main_layout.addWidget(menu_widget, alignment=Qt.AlignCenter)

        self.start_btn.clicked.connect(lambda: self.show_select_hero("三足鼎立"))
        self.exit_btn.clicked.connect(self.close)
        self.rule_btn.clicked.connect(self.show_rule_dialog)
        self.hero_btn.clicked.connect(self.show_hero_dialog)

    def clear_window(self):
        """清空窗口所有内容"""
        for i in reversed(range(self.main_layout.count())): 
            widgetToRemove = self.main_layout.itemAt(i).widget()
            if widgetToRemove:
                widgetToRemove.setParent(None)
        if self.game_widget:
            self.game_widget.setParent(None)
            self.game_widget = None
        
        # 清理AI状态标签
        try:
            if hasattr(self, 'ai_status_label') and self.ai_status_label is not None:
                self.ai_status_label.setParent(None)
                self.ai_status_label = None
        except RuntimeError:
            pass
            
        # 清空缩放组件列表，避免访问已删除的组件
        self.scaled_components.clear()

    def setup_game_ui(self):
        """创建并设置游戏界面的布局，具有中心弃牌堆、牌堆和信息区"""
        self.clear_window()

        self.game_widget = QWidget()
        self.grid_layout = QGridLayout(self.game_widget)
        self.main_layout.addWidget(self.game_widget)

        # --- 布局划分 ---
        # (row, col, rowspan, colspan)
        self.top_area = QHBoxLayout()
        self.grid_layout.addLayout(self.top_area, 0, 0, 1, 5) # 顶部区域跨越5列

        self.bottom_area = QGridLayout()
        self.grid_layout.addLayout(self.bottom_area, 2, 0, 1, 5) # 底部区域跨越5列

        # --- 中间区域 ---
        # 牌堆 (左侧)
        self.draw_pile_widget = QWidget()
        draw_pile_layout = QVBoxLayout(self.draw_pile_widget)
        draw_pile_layout.setAlignment(Qt.AlignCenter)
        
        self.draw_pile_image = QLabel()
        back_pixmap = QPixmap(get_card_image_path(None)) # 获取牌背图片
        self.draw_pile_image.setPixmap(back_pixmap.scaled(100, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self.draw_pile_count = QLabel()
        self.draw_pile_count.setAlignment(Qt.AlignCenter)
        self.draw_pile_count.setStyleSheet("font-size: 18px; color: white; font-weight: bold; background: rgba(0,0,0,0.5); border-radius: 5px;")
        
        # 添加牌堆组件到缩放系统
        self.add_scaled_component(self.draw_pile_image, base_size=(100, 150))
        self.add_scaled_component(self.draw_pile_count, base_font_size=18)
        
        draw_pile_layout.addWidget(self.draw_pile_image)
        draw_pile_layout.addWidget(self.draw_pile_count)
        self.grid_layout.addWidget(self.draw_pile_widget, 1, 0, alignment=Qt.AlignCenter)

        # 中心弃牌区 (中间)
        self.center_card_widget = QWidget()
        self.center_card_area_layout = QVBoxLayout(self.center_card_widget)
        self.center_card_area_layout.setAlignment(Qt.AlignCenter)
        self.center_card_widget.setMinimumSize(200, 350)
        self.grid_layout.addWidget(self.center_card_widget, 1, 1, 1, 3) # 占据中间3列

        # 信息区 (右侧)
        self.info_area_widget = QWidget()
        self.info_area_widget.setMinimumWidth(350)  # 设置最小宽度
        info_layout = QVBoxLayout(self.info_area_widget)
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(10)  # 增加组件间距
        info_layout.setContentsMargins(5, 5, 5, 5)  # 设置边距
        
        # 信息标签
        self.info_label = QLabel() # 之前是 color_label
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet('font-size:18px;color:white;background:rgba(44, 62, 80, 0.8);border:2px solid #99c;border-radius:10px;padding:15px;min-width:200px;min-height:150px;')
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        # 添加信息标签到缩放系统
        self.add_scaled_component(self.info_label, base_font_size=18)
        
        # 历史记录按钮 (放在信息区下面)
        self.history_btn = QPushButton('📜 历史')
        self.add_scaled_component(self.history_btn, base_size=(150, 45), base_font_size=16)
        self.history_btn.setStyleSheet("""
            QPushButton { 
                font-size: 16px; font-weight: bold; color: white; 
                background-color: rgba(52, 152, 219, 0.8); 
                border: 2px solid #2980b9; border-radius: 8px; 
                padding: 8px; 
            }
            QPushButton:hover { background-color: rgba(41, 128, 185, 0.9); }
            QPushButton:pressed { background-color: rgba(36, 113, 163, 1.0); }
        """)
        self.history_btn.clicked.connect(self.show_history_dialog)
        info_layout.addWidget(self.history_btn, 0, Qt.AlignCenter)
        
        # 添加弹性空间，让信息区能够充分显示
        info_layout.addStretch(1)
        
        # 只添加一次信息区到网格布局
        self.grid_layout.addWidget(self.info_area_widget, 1, 4, alignment=Qt.AlignCenter)

        # 设置行和列的伸展系数
        self.grid_layout.setRowStretch(0, 2) # 顶部
        self.grid_layout.setRowStretch(1, 4) # 中部
        self.grid_layout.setRowStretch(2, 4) # 底部
        self.grid_layout.setColumnStretch(0, 1) # 牌堆
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 2) # 中心弃牌区
        self.grid_layout.setColumnStretch(3, 1)
        self.grid_layout.setColumnStretch(4, 3) # 信息区 - 增加更多空间分配

        # --- 填充底部和顶部内容 ---
        main_player_pos = 0
        other_players = [p for p in self.game.player_list if p.position != main_player_pos]
        
        # 顶部其他玩家区域
        self.top_area.addStretch(1) # 左侧空白
        for p in other_players:
            player_widget = PlayerInfoWidget(p, is_main_player=False)
            self.player_widgets[p.position] = player_widget
            self.top_area.addWidget(player_widget, 0, Qt.AlignTop) # addWidget(widget, stretch, alignment)
            self.top_area.addStretch(1) # 玩家之间的空白
        self.top_area.setSpacing(20) # 设置玩家控件之间的最小间距

        # 底部主玩家区域
        main_player = self.game.player_list[main_player_pos]
        main_player_widget = PlayerInfoWidget(main_player, is_main_player=True, is_current=True) # 主玩家默认高亮
        self.player_widgets[main_player_pos] = main_player_widget
        self.bottom_area.addWidget(main_player_widget, 0, 0, 2, 1) # (row, col, rowspan, colspan)

        # 手牌区
        self.card_area = QWidget()
        self.card_area_layout = QHBoxLayout(self.card_area)
        self.card_area_layout.setSpacing(-40) # 让手牌部分重叠
        self.card_area_layout.setAlignment(Qt.AlignCenter)
        self.bottom_area.addWidget(self.card_area, 0, 1, 2, 3)
        
        # 操作区和技能区
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.setContentsMargins(0,0,0,0)

        self.action_area = QWidget()
        self.action_area_layout = QVBoxLayout(self.action_area)
        self.action_area_layout.setSpacing(8)  # 减少间距，为4个按钮留出更多空间
        self.action_area_layout.setAlignment(Qt.AlignCenter)
        self.action_area_layout.setContentsMargins(5, 5, 5, 5)  # 添加边距
        
        self.my_skill_label = QLabel()
        self.my_skill_label.setWordWrap(True)
        self.my_skill_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.my_skill_label.setStyleSheet("""
            font-size: 15px; color: white; background: rgba(0,0,0,0.6); 
            border: 1px solid #99c; border-radius: 8px; padding: 8px; min-height: 100px;
        """)
        
        # 添加技能标签到缩放系统
        self.add_scaled_component(self.my_skill_label, base_font_size=15)
        
        right_panel_layout.addWidget(self.action_area)
        right_panel_layout.addWidget(self.my_skill_label)
        right_panel_layout.setStretchFactor(self.action_area, 1)
        right_panel_layout.setStretchFactor(self.my_skill_label, 1)

        self.bottom_area.addWidget(right_panel_widget, 0, 4, 2, 1)

        # 设置底部列的伸展系数
        self.bottom_area.setColumnStretch(0, 2) # 主玩家信息
        self.bottom_area.setColumnStretch(1, 5) # 手牌区
        self.bottom_area.setColumnStretch(2, 0)
        self.bottom_area.setColumnStretch(3, 0)
        self.bottom_area.setColumnStretch(4, 2) # 操作和技能区

    # 加历史记录
    def add_history(self, text):
        self.history_lines.append(text)
        if len(self.history_lines) > 50:
            self.history_lines = self.history_lines[-50:]
        
        # 更新历史记录按钮的文本，显示最新记录数量
        if hasattr(self, 'history_btn'):
            self.history_btn.setText(f'📜 历史 ({len(self.history_lines)})')

    def show_history_dialog(self):
        """显示历史记录对话框"""
        dialog = HistoryDialog(self.history_lines, self)
        dialog.exec_()


    

    def start_game(self, mode, player_hero, other_heros):
        from game import Game
        
        # 清空历史记录
        self.history_lines = []
        
        # 清空缩放组件列表，避免内存泄漏
        self.scaled_components.clear()
        
        num_players = len(other_heros) + 1
        self.game = Game(player_num=num_players, mode=mode)
        self.game.set_gui(self)

        # 重置武圣状态
        self.wusheng_active = False

        # 1. 初始化玩家，这会填充 self.game.player_list
        self.game.initialize_players(player_hero_name=player_hero, ai_hero_names=other_heros)
        
        # 2. 现在 player_list 已经有数据，可以安全地设置UI了
        self.setup_game_ui() 
        
        # 3. 完成剩下的游戏设置（发牌、翻开第一张牌等）
        self.game.finalize_setup()
        
        # 4. 显示第一回合
        self.show_game_round(first_round=True)
        
        # 5. 更新历史记录按钮文本
        if hasattr(self, 'history_btn'):
            self.history_btn.setText('📜 历史 (0)')

    def get_cur_player_info(self):
        """获取当前玩家的相关信息"""
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        hand = player.uno_list
        draw_n = self.game.draw_n
        can_draw_chain = self.game.can_continue_draw_chain(player)
        return cur_idx, player, hand, draw_n, can_draw_chain

    def show_game_round(self, first_round=False):
        # 如果游戏已经结束，不更新界面
        if hasattr(self, 'game') and self.game and self.game.game_over:
            return
            
        # 获取当前玩家信息
        cur_location = self.game.cur_location
        player = self.game.player_list[cur_location]
        draw_n = self.game.draw_n
        
        # 更新玩家信息显示
        for position, player_widget in self.player_widgets.items():
            is_current = (position == cur_location)
            player_widget.update_info(self.game.player_list[position], is_current)
        
        # 更新中央牌堆显示
        self.show_center_card_stack()
        
        # 更新摸牌堆数量
        self.update_draw_pile_count()
        
        # 更新历史记录
        self.render_info_area()
        
        # 根据当前玩家类型处理
        if isinstance(player, AIPlayer):
            # AI玩家回合
            try:
                if hasattr(self, 'ai_status_label') and self.ai_status_label is not None:
                    self.ai_status_label.setVisible(True)
                    self.ai_status_label.setText(f"AI ({player.mr_card.name}) 正在思考...")
            except RuntimeError:
                pass  # 如果标签已被删除，静默忽略

            # 延迟后执行AI操作
            def execute_ai_turn_safe():
                try:
                    if hasattr(self, 'game') and self.game is not None and not self.game.game_over:
                        self.game.execute_turn()
                except RuntimeError:
                    pass  # 如果GUI已被删除，静默忽略
            QTimer.singleShot(2000, execute_ai_turn_safe)
        else:
            # 人类玩家回合
            try:
                if hasattr(self, 'ai_status_label') and self.ai_status_label is not None:
                    self.ai_status_label.setVisible(False)
            except RuntimeError:
                pass  # 如果标签已被删除，静默忽略

            # 回合开始时，检查手牌是否超限
            if len(player.uno_list) > player.hand_limit:
                # 手牌超限时，显示提示信息
                self.show_temporary_message(f"{player.mr_card.name} 手牌已达上限，不能再摸牌！", duration=3000)
            
            # 渲染手牌区域
            can_draw_chain = self.game.can_continue_draw_chain(player)
            self.render_hand_area(player.uno_list, draw_n, can_draw_chain, enable_click=True)
            
            # 渲染操作按钮区域
            is_forced_draw_pending = draw_n > 0
            can_play = len(player.uno_list) > 0  # 有手牌就可以出牌
            end_enabled = self.game.turn_action_taken  # 已经执行过行动就可以结束回合
            self.render_action_area(is_forced_draw_pending, can_play, end_enabled)

    def render_hand_area(self, hand, draw_n, can_draw_chain, enable_click=True):
        """渲染手牌区域"""
        # 清空旧手牌
        while self.card_area_layout.count():
            item = self.card_area_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.card_buttons = []
        for i, card in enumerate(hand):
            card_button = QPushButton()
            card_button.setFixedSize(80, 120)
            
            display_card = card
            # 如果武圣激活，并且是红色牌，则显示为红+2
            if self.wusheng_active and card.color == 'red':
                display_card = UnoCard('draw2', 'red', 0)

            icon = QIcon(get_card_image_path(display_card))
            card_button.setIcon(icon)
            card_button.setIconSize(QSize(75, 110))
            card_button.setStyleSheet("background-color: transparent; border: none;")
            if enable_click:
                card_button.clicked.connect(lambda _, idx=i: self.on_card_clicked(idx))
            self.card_buttons.append(card_button)
            self.card_area_layout.addWidget(card_button)

    def render_action_area(self, is_forced_draw_pending=False, can_play=True, end_enabled=False):
        """渲染操作按钮区域"""
        # 清空旧按钮
        while self.action_area_layout.count():
            item = self.action_area_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Clear old references to prevent accessing deleted widgets
        for attr in ['play_btn', 'draw_btn', 'skill_btn', 'end_btn']:
            if hasattr(self, attr):
                delattr(self, attr)

        cur_player = self.game.player_list[self.game.cur_location] # This is the human player (pos 0)
        
        active_skills = []
        if cur_player.mr_card and cur_player.mr_card.skills:
            for skill in cur_player.mr_card.skills:
                if skill.is_active_in_turn:
                    active_skills.append(skill)
        
        # 出牌按钮
        self.play_btn = QPushButton('出牌')
        self.add_scaled_component(self.play_btn, base_font_size=16)
        btn_style = """
            QPushButton { font-size: 16px; font-weight: bold; color: white; background-color: #e74c3c; 
                          border: 2px solid #c0392b; border-radius: 8px; padding: 8px 12px; min-height: 35px; }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.play_btn.setStyleSheet(btn_style)
        self.play_btn.clicked.connect(self.on_play_card_clicked)
        self.play_btn.setEnabled(can_play and not self.game.turn_action_taken)
        self.action_area_layout.addWidget(self.play_btn)

        # 摸牌按钮
        draw_btn_text = '强制摸牌' if is_forced_draw_pending else '摸牌'
        self.draw_btn = QPushButton(draw_btn_text)
        self.add_scaled_component(self.draw_btn, base_font_size=16)
        btn_style = """
            QPushButton { font-size: 16px; font-weight: bold; color: white; background-color: #3498db; 
                          border: 2px solid #2980b9; border-radius: 8px; padding: 8px 12px; min-height: 35px; }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.draw_btn.setStyleSheet(btn_style)
        self.draw_btn.clicked.connect(self.on_draw_card_clicked)
        self.draw_btn.setEnabled(not self.game.turn_action_taken)
        self.action_area_layout.addWidget(self.draw_btn)

        # 技能按钮 - 检查技能是否可用
        if active_skills:
            # 检查技能是否可用
            skill_available = True
            skill_unavailable_reason = ""
            
            for skill in active_skills:
                if skill.name == '缔盟':
                    # 鲁肃缔盟技能：手牌数大于6时失效
                    if len(cur_player.uno_list) > 6:
                        skill_available = False
                        skill_unavailable_reason = "手牌数大于6，技能失效"
                        break
                elif skill.name == '武圣':
                    # 关羽武圣技能：需要红色牌
                    red_cards = [card for card in cur_player.uno_list if card.color == 'red']
                    if not red_cards:
                        skill_available = False
                        skill_unavailable_reason = "没有红色牌，无法发动武圣"
                        break
            
            # 根据武圣状态设置按钮文本
            skill_btn_text = '取消武圣' if self.wusheng_active else '技能'
            self.skill_btn = QPushButton(skill_btn_text)
            self.add_scaled_component(self.skill_btn, base_font_size=16)
            btn_style = """
                QPushButton { font-size: 16px; font-weight: bold; color: white; background-color: #9b59b6; 
                              border: 2px solid #8e44ad; border-radius: 8px; padding: 8px 12px; min-height: 35px; }
                QPushButton:hover { background-color: #8e44ad; }
                QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
            """
            self.skill_btn.setStyleSheet(btn_style)
            self.skill_btn.clicked.connect(self.on_skill_button_clicked)
            
            # 设置按钮状态
            button_enabled = (not self.game.turn_action_taken and 
                            not is_forced_draw_pending and 
                            (skill_available or self.wusheng_active))  # 武圣激活时允许取消
            
            self.skill_btn.setEnabled(button_enabled)
            
            # 如果技能不可用，设置工具提示
            if not skill_available and not self.wusheng_active:
                self.skill_btn.setToolTip(skill_unavailable_reason)
            else:
                self.skill_btn.setToolTip("")
                
            self.action_area_layout.addWidget(self.skill_btn)

        # 结束回合按钮
        self.end_btn = QPushButton('结束回合')
        self.add_scaled_component(self.end_btn, base_font_size=16)
        btn_style = """
            QPushButton { font-size: 16px; font-weight: bold; color: white; background-color: #f39c12; 
                          border: 2px solid #e67e22; border-radius: 8px; padding: 8px 12px; min-height: 35px; }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.end_btn.setStyleSheet(btn_style)
        self.end_btn.clicked.connect(self.on_end_turn_clicked)
        self.end_btn.setEnabled(end_enabled)
        self.action_area_layout.addWidget(self.end_btn)

    def show_center_card_stack(self):
        """显示中央弃牌堆的牌，通过手动计算位置来实现精确的堆叠和居中。"""
        # 清理旧的卡牌标签
        for label in self.center_card_widget.findChildren(QLabel):
            label.deleteLater()

        cards_to_show = self.game.playedcards.get_last_cards(5)
        if not cards_to_show:
            return

        card_width, card_height = 150, 225
        y_offset_step = 8   # 大幅减小垂直偏移，形成紧凑堆叠
        x_offset_step = 5   # 增加一个小的水平偏移

        container_width = self.center_card_widget.width()
        container_height = self.center_card_widget.height()

        # 计算整个牌堆的总高度和宽度
        num_cards = len(cards_to_show)
        total_stack_height = card_height + (num_cards - 1) * y_offset_step
        total_stack_width = card_width + (num_cards - 1) * x_offset_step

        # 计算第一张牌的起始位置，以使整个牌堆居中
        base_x = (container_width - total_stack_width) // 2
        base_y = (container_height - total_stack_height) // 2

        # 从底层到顶层创建和放置卡牌
        for i, card in enumerate(cards_to_show):
            card_label = QLabel(self.center_card_widget) # 指定父控件
            pixmap = QPixmap(get_card_image_path(card)).scaled(card_width, card_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            card_label.setPixmap(pixmap)
            card_label.setFixedSize(card_width, card_height)
            
            # 添加边框以区分卡牌
            card_label.setStyleSheet("border: 1px solid rgba(255, 255, 255, 0.5); border-radius: 8px;")

            # 计算当前卡牌的位置，加入水平和垂直偏移
            x_pos = base_x + i * x_offset_step
            y_pos = base_y + i * y_offset_step
            card_label.move(x_pos, y_pos)
            
            card_label.show()
            card_label.raise_() # 确保后添加的牌在上面

    def on_skill_button_clicked(self):
        """处理技能按钮的点击事件"""
        print(f"DEBUG on_skill_button_clicked: wusheng_active = {self.wusheng_active}")
        
        # 检查是否武圣已激活，如果是则取消武圣状态
        if self.wusheng_active:
            print("DEBUG: Cancelling WuSheng")
            self.wusheng_active = False
            self.show_temporary_message("武圣技能已取消", 1500)
            # 立即更新技能按钮文本
            if hasattr(self, 'skill_btn'):
                self.skill_btn.setText('技能')
            self.show_game_round()
            return
        
        # 调用原有的技能按钮逻辑
        cur_player = self.game.player_list[self.game.cur_location]
        active_skills = []
        if cur_player.mr_card and cur_player.mr_card.skills:
            for skill in cur_player.mr_card.skills:
                if skill.is_active_in_turn:
                    active_skills.append(skill)
        
        print(f"DEBUG: Found {len(active_skills)} active skills")
        
        if len(active_skills) == 1:
            # 如果只有一个主动技能，直接发动
            skill = active_skills[0]
            print(f"DEBUG: Activating single skill: {skill.name}")
            self.direct_activate_skill(skill)
            
            # 武圣技能不会自动结束回合，需要玩家选择牌
            if skill.name != '武圣':
                # 执行技能后，技能内部会处理回合结束
                pass
        elif len(active_skills) > 1:
            # 如果有多个主动技能，弹出选择对话框
            skill_names = [skill.name for skill in active_skills]
            skill_name, ok = QInputDialog.getItem(self, "选择技能", "请选择要发动的技能:", skill_names, 0, False)
            if ok and skill_name:
                selected_skill = next(skill for skill in active_skills if skill.name == skill_name)
                print(f"DEBUG: Activating selected skill: {selected_skill.name}")
                self.direct_activate_skill(selected_skill)
                
                # 武圣技能不会自动结束回合，需要玩家选择牌
                if selected_skill.name != '武圣':
                    # 执行技能后，技能内部会处理回合结束
                    pass

    def direct_activate_skill(self, skill):
        """直接激活技能的最终执行逻辑"""
        player = self.game.player_list[self.game.cur_location]
        
        if skill.name == '反间':
            player.activate_skill('反间')
            # 反间技能有自己的UI流程和刷新，这里不需要再调用show_game_round
        elif skill.name == '武圣':
            self.activate_wusheng_skill()
        elif skill.name == '缔盟':
            player.activate_skill('缔盟')
            # 缔盟技能有自己的UI流程和刷新，这里不需要再调用show_game_round
        else:
            self.show_message_box("提示", f"技能 [{skill.name}] 的界面交互尚未实现。")
            # 不再在这里调用show_game_round，由on_skill_button_clicked统一处理

    def activate_wusheng_skill(self):
        """激活武圣技能"""
        print("DEBUG: activate_wusheng_skill called")
        player = self.game.player_list[self.game.cur_location]
        
        # 检查玩家是否有红色牌
        red_cards = [i for i, card in enumerate(player.uno_list) if card.color == 'red']
        
        if not red_cards:
            self.show_message_box("提示", "你没有红色牌，无法发动武圣技能。")
            return
        
        # 设置武圣状态为激活
        self.wusheng_active = True
        print(f"DEBUG: Set wusheng_active = {self.wusheng_active}")
        
        # 显示提示信息
        self.show_temporary_message("武圣技能已激活！请选择一张红色牌，它将作为红+2打出。再次点击技能按钮可取消。", 3000)
        
        # 刷新界面，让玩家选择牌
        self.show_game_round()


    def choose_target_player_dialog(self, exclude_self=False):
        """弹窗让玩家选择一个目标玩家"""
        players = self.game.player_list
        target_candidates = {}
        for p in players:
            if exclude_self and p.position == self.game.cur_location:
                continue
            target_candidates[f"玩家{p.position+1} ({p.mr_card.name})"] = p

        if not target_candidates:
            return None

        target_name, ok = QInputDialog.getItem(self, "选择目标", "请选择一个目标玩家:", target_candidates.keys(), 0, False)
        if ok and target_name:
            return target_candidates[target_name]
        return None

    def choose_specific_card_dialog(self, player, cards, prompt):
        """弹窗让玩家从指定的卡牌列表中选择一张"""
        hand_map = {str(card): card for card in cards}
        if not hand_map:
            return None
        card_str, ok = QInputDialog.getItem(self, "选择卡牌", prompt, hand_map.keys(), 0, False)
        if ok and card_str:
            return hand_map[card_str]
        return None

    def choose_card_from_hand_dialog(self, player, prompt):
        """弹窗让玩家从手牌中选择一张牌"""
        return self.choose_specific_card_dialog(player, player.uno_list, prompt)

    def choose_cards_to_discard_dialog(self, player, num_to_discard):
        """让玩家选择要弃置的牌的对话框"""
        cards = player.uno_list
        if len(cards) < num_to_discard:
            return None
        
        dialog = QDialog(self)
        dialog.setWindowTitle("选择要弃置的牌")
        dialog.setModal(True)
        dialog.resize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        # 提示文本
        prompt_label = QLabel(f"请选择 {num_to_discard} 张牌来弃置：")
        prompt_label.setStyleSheet("font-size: 16px; color: white; margin: 10px;")
        layout.addWidget(prompt_label)
        
        # 卡牌选择区域
        card_widget = QWidget()
        card_layout = QHBoxLayout(card_widget)
        card_layout.setSpacing(10)
        
        selected_indices = []
        card_buttons = []
        
        def on_card_clicked(idx):
            if idx in selected_indices:
                selected_indices.remove(idx)
                card_buttons[idx].setStyleSheet("""
                    QPushButton {
                        background-color: #34495e;
                        border: 2px solid #2c3e50;
                        border-radius: 8px;
                        padding: 5px;
                        min-width: 80px;
                        min-height: 120px;
                    }
                    QPushButton:hover {
                        background-color: #2c3e50;
                    }
                """)
            else:
                if len(selected_indices) < num_to_discard:
                    selected_indices.append(idx)
                    card_buttons[idx].setStyleSheet("""
                        QPushButton {
                            background-color: #e74c3c;
                            border: 2px solid #c0392b;
                            border-radius: 8px;
                            padding: 5px;
                            min-width: 80px;
                            min-height: 120px;
                        }
                        QPushButton:hover {
                            background-color: #c0392b;
                        }
                    """)
        
        # 创建卡牌按钮
        for i, card in enumerate(cards):
            card_btn = QPushButton()
            card_btn.setFixedSize(80, 120)
            card_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    border: 2px solid #2c3e50;
                    border-radius: 8px;
                    padding: 5px;
                    min-width: 80px;
                    min-height: 120px;
                }
                QPushButton:hover {
                    background-color: #2c3e50;
                }
            """)
            
            # 设置卡牌图片
            card_image_path = get_card_image_path(card)
            if os.path.exists(card_image_path):
                pixmap = QPixmap(card_image_path)
                card_btn.setIcon(QIcon(pixmap))
                card_btn.setIconSize(QSize(70, 110))
            
            card_btn.clicked.connect(lambda checked, idx=i: on_card_clicked(idx))
            card_buttons.append(card_btn)
            card_layout.addWidget(card_btn)
        
        layout.addWidget(card_widget)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("确认")
        confirm_btn.setEnabled(False)
        confirm_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        # 更新确认按钮状态
        def update_confirm_button():
            confirm_btn.setEnabled(len(selected_indices) == num_to_discard)
        
        # 监听选择变化
        for btn in card_buttons:
            btn.clicked.connect(update_confirm_button)
        
        if dialog.exec_() == QDialog.Accepted:
            return selected_indices
        else:
            return None

    def update_draw_pile_count(self):
        """更新牌堆数量标签"""
        count = len(self.game.unocard_pack)
        self.draw_pile_count.setText(f"{count}")

    def render_info_area(self):
        """更新右侧信息区的文本，使其更清晰"""
        color = self.game.cur_color
        color_map = {'red': '红色', 'blue': '蓝色', 'green': '绿色', 'yellow': '黄色', 'black': '任意'}
        
        # 获取上一张牌和当前玩家信息
        last_card = self.game.playedcards.get_one()
        current_player = self.game.player_list[self.game.cur_location]
        current_player_text = f"当前回合: <b>{current_player.mr_card.name}({current_player.position+1})</b>"
        
        # 根据游戏状态确定出牌要求
        if self.game.draw_n > 0:
            # 如果有强制摸牌，根据加牌串中最后一张牌的类型显示正确的出牌要求
            if self.game.draw_chain_cards:
                # 获取加牌串中最后一张牌的类型
                last_chain_card = self.game.draw_chain_cards[-1][0]  # effective_card
                if last_chain_card.type == 'draw2':
                    draw_requirement_text = f"当前出牌要求: <b>必须摸{self.game.draw_n}张牌或出+2/+4</b>"
                elif last_chain_card.type == 'wild_draw4':
                    draw_requirement_text = f"当前出牌要求: <b>必须摸{self.game.draw_n}张牌或出+4</b>"
                else:
                    # 默认情况
                    draw_requirement_text = f"当前出牌要求: <b>必须摸{self.game.draw_n}张牌或出+2/+4</b>"
            else:
                # 没有加牌串信息时的默认显示
                draw_requirement_text = f"当前出牌要求: <b>必须摸{self.game.draw_n}张牌或出+2/+4</b>"
        else:
            # 正常出牌，显示颜色和类型要求
            if last_card:
                if last_card.type == 'number':
                    # 数字牌：显示颜色/数字
                    draw_requirement_text = f"当前出牌要求: <b>{color_map.get(color, '任意颜色')}/{last_card.value}</b>"
                elif last_card.type in ['draw2', 'reverse', 'skip']:
                    # 功能牌：显示颜色/类型
                    type_map = {'draw2': '+2', 'reverse': '反转', 'skip': '跳过'}
                    draw_requirement_text = f"当前出牌要求: <b>{color_map.get(color, '任意颜色')}/{type_map.get(last_card.type, '')}</b>"
                elif last_card.type in ['wild', 'wild_draw4']:
                    # 万能牌：只显示颜色（因为万能牌可以改变颜色）
                    draw_requirement_text = f"当前出牌要求: <b>{color_map.get(color, '任意颜色')}</b>"
                else:
                    # 其他情况：只显示颜色
                    draw_requirement_text = f"当前出牌要求: <b>{color_map.get(color, '任意颜色')}</b>"
            else:
                # 没有上一张牌：只显示颜色
                draw_requirement_text = f"当前出牌要求: <b>{color_map.get(color, '任意颜色')}</b>"

        direction_text = f"游戏方向: {'顺序' if self.game.dir == 1 else '逆序'}"
        card_info_text = "上一张牌: 无"
        if last_card:
            card_display_str = ""
            if last_card.type == 'number':
                # 颜色数字
                card_display_str = f"{color_map.get(last_card.color, '')} <b>{last_card.value}</b>"
            elif last_card.type == 'wild':
                # 万能牌(选定颜色)
                if self.game.cur_color != 'black':
                    card_display_str = f"<b>万能牌({color_map.get(self.game.cur_color, '')})</b>"
                else:
                    card_display_str = f"<b>万能牌</b>"
            elif last_card.type == 'wild_draw4':
                # 万能+4牌(选定颜色)
                if self.game.cur_color != 'black':
                    card_display_str = f"<b>万能+4牌({color_map.get(self.game.cur_color, '')})</b>"
                else:
                    card_display_str = f"<b>万能+4牌</b>"
            elif last_card.type == 'reverse':
                # 颜色转
                card_display_str = f"{color_map.get(last_card.color, '')} <b>转</b>"
            elif last_card.type == 'skip':
                # 颜色禁
                card_display_str = f"{color_map.get(last_card.color, '')} <b>禁</b>"
            elif last_card.type == 'draw2':
                # 颜色+2
                card_display_str = f"{color_map.get(last_card.color, '')} <b>+2</b>"
            else:
                # 其他情况保持原样
                type_map = {'draw2': '+2', 'reverse': '反转', 'skip': '跳过'}
                card_display_str = f"{color_map.get(last_card.color, '')} <b>{type_map.get(last_card.type, '')}</b>"
            
            card_info_text = f"上一张牌: {card_display_str}"

        # 使用HTML换行<br>以获得更好的控制
        self.info_label.setText(
            f"{current_player_text}<br><br>"
            f"{draw_requirement_text}<br>"
            f"{direction_text}<br>"
            f"{card_info_text}"
        )

    def show_temporary_message(self, message, duration=1500):
        """在屏幕中央显示一个临时的、带样式的消息"""
        if not self.game_widget or (hasattr(self, 'game') and self.game.game_over):
            return
            
        temp_label = QLabel(message, self.game_widget)
        temp_label.setStyleSheet("font-size: 30px; color: #f1c40f; background-color: rgba(0, 0, 0, 0.7); border-radius: 15px; padding: 20px;")
        temp_label.setAlignment(Qt.AlignCenter)
        
        temp_label.adjustSize()
        temp_label.move(self.game_widget.rect().center() - temp_label.rect().center())
        temp_label.show()
        temp_label.raise_()

        # Use a lambda to capture the current temp_label
        QTimer.singleShot(duration, lambda: temp_label.deleteLater())

    def show_message_box(self, title, message, icon_type='information'):
        """显示一个通用的消息框"""
        if "跳牌" in title or "跳牌" in message:
            self.show_temporary_message(message)
            return
            
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStyleSheet("QMessageBox { background-color: white; color: black; }")
        if icon_type == 'warning':
            msg_box.setIcon(QMessageBox.Warning)
        elif icon_type == 'critical':
            msg_box.setIcon(QMessageBox.Critical)
        else:
            msg_box.setIcon(QMessageBox.Information)
        msg_box.exec_()

    def show_winner_and_exit(self, winner):
        """显示游戏结束时的胜利者并退出游戏"""
        self.show_message_box('游戏结束', f'玩家 {winner.position + 1} ({winner.mr_card.name}) 获胜！')
        self.show_main_menu()

    def show_draw_and_exit(self, winners):
        """显示游戏结束时的平局并退出游戏"""
        if len(winners) == 2:
            winner_names = f'玩家 {winners[0].position + 1} ({winners[0].mr_card.name}) 和 玩家 {winners[1].position + 1} ({winners[1].mr_card.name})'
        else:
            winner_names = ', '.join([f'玩家 {w.position + 1} ({w.mr_card.name})' for w in winners])
        self.show_message_box('游戏结束', f'{winner_names} 平局！')
        self.show_main_menu()

    def choose_color_dialog(self):
        """让玩家选择颜色的对话框"""
        colors = ['red', 'blue', 'green', 'yellow']
        color, ok = QInputDialog.getItem(self, "选择颜色", "请选择一种颜色:", colors, 0, False)
        if ok and color:
            return color
        return None
    
    def on_play_card_clicked(self):
        """处理出牌按钮的点击"""
        if self.selected_card_idx is None:
            self.show_message_box('提示', '请先选择一张牌！')
            return

        player = self.game.player_list[0] # 假设人类玩家总是0号
        card = player.uno_list[self.selected_card_idx]
        
        # 检查武圣状态下的出牌
        if self.wusheng_active and card.color == 'red':
            # 武圣激活且选择了红色牌，执行武圣技能
            self.game.execute_skill_wusheng(player, self.selected_card_idx)
            # 重置武圣状态
            self.wusheng_active = False
        else:
            # 正常出牌
            player.play(self.selected_card_idx, self.wusheng_active)
        
        # 执行出牌后，禁用所有行动按钮
        self.disable_action_buttons()
        # 处理回合结束后的逻辑
        # 非跳牌的正常出牌逻辑
        player.game.turn_action_taken = True  # 标记回合已结束
        player.game.clear_state()
        player.game.turn_count += 1
        
        # 检查是否有玩家可以跳牌
        if player.handle_jump_logic():
            return
        
        # 没有跳牌，正常切换到下一个玩家
        # 切换玩家逻辑由游戏主循环处理，这里只需要刷新UI
        if player.game.gui:
            player.game.gui.show_game_round()
        # GUI更新将通过Observer模式自动处理

    def on_draw_card_clicked(self):
        """处理摸牌按钮的点击"""
        player = self.game.player_list[0] # 假设人类玩家总是0号
        
        # 显示摸牌提示
        if self.game.draw_n > 0:
            self.show_temporary_message(f"{player.mr_card.name} 摸了 {self.game.draw_n} 张牌", duration=2000)
        else:
            self.show_temporary_message(f"{player.mr_card.name} 摸了 1 张牌", duration=2000)
        
        # 调用game.py中的核心逻辑
        player.draw_cards(1)
        # 执行摸牌后，禁用所有行动按钮
        self.disable_action_buttons()
        # 处理回合结束后的逻辑
        # 非跳牌的正常出牌逻辑
        player.game.turn_action_taken = True  # 标记回合已结束
        player.game.clear_state()
        player.game.turn_count += 1
        
        # 检查是否有玩家可以跳牌
        if player.handle_jump_logic():
            return
        
        # 没有跳牌，正常切换到下一个玩家
        # 切换玩家逻辑由游戏主循环处理，这里只需要刷新UI
        if player.game.gui:
            player.game.gui.show_game_round()
        # GUI更新将通过Observer模式自动处理

    def on_end_turn_clicked(self):
        """处理结束回合按钮的点击"""
        player = self.game.player_list[0] # 假设人类玩家总是0号
        
        # 结束回合
        player.game.turn_action_taken = True
        # 处理回合结束后的逻辑
        # 非跳牌的正常出牌逻辑
        player.game.turn_action_taken = True  # 标记回合已结束
        player.game.clear_state()
        player.game.turn_count += 1
        
        # 检查是否有玩家可以跳牌
        if player.handle_jump_logic():
            return
        
        # 没有跳牌，正常切换到下一个玩家
        # 切换玩家逻辑由游戏主循环处理，这里只需要刷新UI
        if player.game.gui:
            player.game.gui.show_game_round()
        # GUI更新将通过Observer模式自动处理

    def ask_yes_no_question(self, title, question):
        """弹出一个通用的"是/否"对话框"""
        reply = QMessageBox.question(self, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def ask_for_card_choice(self, title, message, cards):
        """弹出一个让玩家选择手牌的对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(message))
        
        list_widget = QListWidget()
        for card in cards:
            item = QListWidgetItem(str(card))
            item.setData(Qt.UserRole, card)
            list_widget.addItem(item)
        layout.addWidget(list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted and list_widget.selectedItems():
            return list_widget.selectedItems()[0].data(Qt.UserRole)
        return None

    def highlight_selected_card(self, idx):
        """高亮显示选中的卡牌"""
        # 重置所有卡牌的高亮状态
        for i, btn in enumerate(self.card_buttons):
            if i == idx:
                btn.setStyleSheet("background-color: #f39c12; border: 2px solid #e67e22; border-radius: 5px;")
            else:
                btn.setStyleSheet("background-color: transparent; border: none;")
        self.selected_card_idx = idx

    def on_card_clicked(self, idx):
        self.highlight_selected_card(idx)
        
        cur_player_idx = self.game.cur_location
        player = self.game.player_list[cur_player_idx]
        if isinstance(player, AIPlayer):
            return # 不处理AI玩家的点击

        card = player.uno_list[idx]
        
        card_to_check = card
        # If WuSheng is active and the card is red, check validity as a virtual red +2 card
        if self.wusheng_active and card.color == 'red':
            from card import UnoCard
            card_to_check = UnoCard('draw2', 'red', 0)

        # Enable play button only if the card is valid to play
        if hasattr(self, 'play_btn'):
            self.play_btn.setEnabled(player.check_card(card_to_check))

    def show_mode_dialog(self):
        dialog = ModeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            mode = dialog.selected_mode
            self.show_select_hero(mode)

    def show_select_hero(self, mode):
        select_dialog = SelectHeroDialog(mode, self)
        select_dialog.exec_()

    def get_player_card_index(self, player):
        hand = '\n'.join([f'{i}: {str(card)}' for i, card in enumerate(player.uno_list)])
        idx, ok = QInputDialog.getInt(self, '出牌', f'你的手牌：\n{hand}\n请输入你要出的牌序号：', 0, 0, len(player.uno_list)-1, 1)
        return idx, ok

    def show_hero_dialog(self):
        from mr_cards import all_heroes
        dialog = QDialog(self)
        dialog.setWindowTitle('武将图鉴')
        dialog.setStyleSheet("background-color: white;")
        dialog.resize(1200, 800)

        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        
        content_widget = QWidget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setSpacing(20)

        heroes = list(all_heroes.values())
        cols = 3 # 每行显示3个武将
        
        for i, hero_card in enumerate(heroes):
            row, col = divmod(i, cols)
            
            # 单个武将的容器
            hero_box = QWidget()
            hero_layout = QHBoxLayout(hero_box)
            hero_box.setStyleSheet("background-color: #f0f0f0; border-radius: 10px;")

            # 武将图片
            img_label = QLabel()
            if hero_card.image_path and os.path.exists(resource_path(os.path.join('images', hero_card.image_path))):
                pixmap = QPixmap(resource_path(os.path.join('images', hero_card.image_path)))
                img_label.setPixmap(pixmap.scaled(150, 210, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_label.setText("无图片")
                img_label.setFixedSize(150, 210)
            img_label.setAlignment(Qt.AlignCenter)
            hero_layout.addWidget(img_label)

            # 武将信息
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            
            name_label = QLabel(f"<b>{hero_card.name}</b> ({hero_card.team})")
            name_label.setStyleSheet("font-size: 16px;")
            
            skill_label = QLabel(hero_card.skill_description)
            skill_label.setWordWrap(True)
            skill_label.setAlignment(Qt.AlignTop)
            
            info_layout.addWidget(name_label)
            info_layout.addWidget(skill_label)
            
            # 特点信息
            if hasattr(hero_card, 'tags') and hero_card.tags:
                tags_label = QLabel(f"特点: {hero_card.tags}")
                tags_label.setStyleSheet("font-size: 16px; color: #333; font-weight: bold;")
                info_layout.addWidget(tags_label)
            
            # 难度信息
            if hasattr(hero_card, 'difficulty'):
                difficulty_label = QLabel(f"难度: {hero_card.difficulty}/10")
                difficulty_label.setStyleSheet("font-size: 16px; color: #333; font-weight: bold;")
                info_layout.addWidget(difficulty_label)
            info_layout.addStretch() # 将内容推到顶部

            hero_layout.addWidget(info_widget, stretch=1)
            grid_layout.addWidget(hero_box, row, col)

        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(scroll)
        dialog.exec_()

    def show_rule_dialog(self):
        rule_text = (
            "=== 基础规则 ===\n"
            "1. 出牌规则：必须出与当前颜色相同的牌，或使用万能牌改变颜色；\n"
            "2. 特殊牌效果：\n"
            "   • [+2]：下家摸2张牌\n"
            "   • [+4]：下家摸4张牌\n"
            "   • [跳过]：跳过下家回合\n"
            "   • [转向]：改变游戏方向\n"
            "   • [万能牌]：改变颜色\n"
            "3. 胜利条件：手牌数为0时获胜\n\n"
            "=== 进阶规则 ===\n"
            "4. UNO规则：仅剩余1张牌时，须喊\"UNO\"，否则若被抓需要摸1张牌；\n"
            "5. 手牌上限：通常为20张，达到上限后剩余加牌不再生效；\n"
            "6. 跳牌规则：颜色和牌面完全相同时可以跳过其余玩家回合抢先打出该牌；黑色牌不能跳牌；\n"
            "7. 跳牌优先级：通过技能发动的跳牌优先级低于未发动技能的跳牌；相同优先级的跳牌按照游戏内出牌顺序执行；\n"
            "8. 加牌叠加：[+2]可以叠[+2]，[+2]可以叠[+4]，[+4]可以叠[+4]，[+4]不可以叠[+2]；\n"
            "9. 技能限制：仅剩余1张牌时回合内的主动技能失效；\n"
            "10. 黑色牌限制：黑色牌不能当作最后一张牌打出，否则需再摸1张牌；\n\n"
            "=== 武将技能 ===\n"
            "游戏包含三国杀风格的武将技能系统，每个武将都有独特的技能效果。\n"
            "技能会在适当的时机自动触发或由玩家主动发动。"
        )
        rule_dialog = QDialog(self)
        rule_dialog.setWindowTitle('游戏规则')
        rule_dialog.setStyleSheet("background-color: white;")
        rule_dialog.resize(700, 800)
        vbox = QVBoxLayout(rule_dialog)
        label = QLabel(rule_text)
        label.setWordWrap(True)
        vbox.addWidget(label)
        rule_dialog.setLayout(vbox)
        rule_dialog.exec_()

    def disable_action_buttons(self):
        """禁用所有行动按钮"""
        # 检查按钮是否存在且未被删除
        def safe_disable_button(button_name):
            try:
                if hasattr(self, button_name):
                    button = getattr(self, button_name)
                    if button and not button.isHidden():
                        button.setEnabled(False)
            except (RuntimeError, AttributeError):
                pass  # 按钮已被删除或不存在
        
        safe_disable_button('play_btn')
        safe_disable_button('draw_btn')
        safe_disable_button('skill_btn')
        safe_disable_button('end_btn')

    def on_turn_start(self, player):
        """
        回合开始时的观察者方法
        """
        # 更新界面显示
        self.show_game_round()
        
    def on_turn_end(self, player):
        """
        回合结束时的观察者方法
        """
        # 可以在这里添加回合结束时的界面更新
        pass

    def on_card_played(self, player, card):
        """
        有玩家出牌时的观察者方法
        """
        # 更新中央牌堆显示
        self.show_center_card_stack()
        # 更新历史记录
        self.render_info_area()
        # 更新玩家手牌数量显示
        self.update_player_hand_display(player)
        
        # 如果是人类玩家出牌，需要重新渲染手牌和操作区域
        if isinstance(player, HumanPlayer):
            cur_location = self.game.cur_location
            current_player = self.game.player_list[cur_location]
            if isinstance(current_player, HumanPlayer):
                # 重新渲染手牌区域
                can_draw_chain = self.game.can_continue_draw_chain(current_player)
                self.render_hand_area(current_player.uno_list, self.game.draw_n, can_draw_chain, enable_click=True)
                
                # 重新渲染操作按钮区域
                is_forced_draw_pending = self.game.draw_n > 0
                can_play = len(current_player.uno_list) > 0
                end_enabled = self.game.turn_action_taken
                self.render_action_area(is_forced_draw_pending, can_play, end_enabled)
        
    def on_cards_drawn(self, player, num_cards):
        """
        有玩家摸牌时的观察者方法
        """
        # 更新玩家手牌数量显示
        self.update_player_hand_display(player)
        # 更新摸牌堆数量
        self.update_draw_pile_count()
        
        # 如果是人类玩家摸牌，需要重新渲染手牌和操作区域
        if isinstance(player, HumanPlayer):
            cur_location = self.game.cur_location
            current_player = self.game.player_list[cur_location]
            if isinstance(current_player, HumanPlayer):
                # 重新渲染手牌区域
                can_draw_chain = self.game.can_continue_draw_chain(current_player)
                self.render_hand_area(current_player.uno_list, self.game.draw_n, can_draw_chain, enable_click=True)
                
                # 重新渲染操作按钮区域
                is_forced_draw_pending = self.game.draw_n > 0
                can_play = len(current_player.uno_list) > 0
                end_enabled = self.game.turn_action_taken
                self.render_action_area(is_forced_draw_pending, can_play, end_enabled)
        
    def on_player_hand_changed(self, player):
        """
        玩家手牌数量变化时的观察者方法
        """
        # 更新玩家信息显示
        if player.position in self.player_widgets:
            player_widget = self.player_widgets[player.position]
            player_widget.update_info(player, is_current=(player.position == self.game.cur_location))
                
        # 如果是人类玩家手牌变化，需要重新渲染手牌和操作区域
        if isinstance(player, HumanPlayer):
            cur_location = self.game.cur_location
            current_player = self.game.player_list[cur_location]
            if isinstance(current_player, HumanPlayer):
                # 重新渲染手牌区域
                can_draw_chain = self.game.can_continue_draw_chain(current_player)
                self.render_hand_area(current_player.uno_list, self.game.draw_n, can_draw_chain, enable_click=True)
                
                # 重新渲染操作按钮区域
                is_forced_draw_pending = self.game.draw_n > 0
                can_play = len(current_player.uno_list) > 0
                end_enabled = self.game.turn_action_taken
                self.render_action_area(is_forced_draw_pending, can_play, end_enabled)
                
    def on_draw_pile_changed(self):
        """
        摸牌堆数量变化时的观察者方法
        """
        # 更新摸牌堆数量显示
        self.update_draw_pile_count()
        
    def on_history_updated(self, message):
        """
        历史记录更新时的观察者方法
        """
        # 更新历史记录显示
        self.render_info_area()
        
    def on_game_state_changed(self):
        """
        游戏状态变化时的观察者方法（通用）
        """
        # 更新整个界面
        self.show_game_round()
        
    def update_player_hand_display(self, player):
        """
        更新指定玩家的手牌数量显示
        """
        if player.position < len(self.player_widgets):
            player_widget = self.player_widgets[player.position]
            player_widget.update_info(player, is_current=(player.position == self.game.cur_location))

# 在文件开头添加历史记录对话框类
class HistoryDialog(QDialog):
    def __init__(self, history_lines, parent=None):
        super().__init__(parent)
        self.setWindowTitle('游戏历史记录')
        self.setModal(True)
        self.resize(600, 500)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                color: white;
            }
            QTextEdit {
                background-color: rgba(44, 62, 80, 0.8);
                color: #f1c40f;
                border: 2px solid #34495e;
                border-radius: 8px;
                padding: 10px;
                font-family: "隶书", "LiSu", serif;
                font-size: 24px;
                line-height: 1.8;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel('游戏历史记录')
        title_label.setStyleSheet("font-family: '隶书', 'LiSu', serif; font-size: 28px; font-weight: bold; color: white; margin: 10px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 历史记录文本区域
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setPlainText('\n'.join(history_lines))
        
        # 滚动到底部
        scrollbar = self.history_text.verticalScrollBar()
        if scrollbar.isVisible():
            scrollbar.setValue(scrollbar.maximum())
        
        layout.addWidget(self.history_text)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 清空历史按钮
        clear_btn = QPushButton('清空历史')
        clear_btn.clicked.connect(self.clear_history)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def clear_history(self):
        """清空历史记录"""
        self.history_text.clear()
        if hasattr(self.parent(), 'history_lines'):
            self.parent().history_lines.clear()