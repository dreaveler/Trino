import sys
import random
import os
from card import UnoCard
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, 
                             QDialog, QHBoxLayout, QLabel, QComboBox, QListWidget, 
                             QListWidgetItem, QInputDialog, QDialogButtonBox, QGridLayout,
                              QScrollArea, QTextEdit, QStackedLayout, QLayout, QTableWidget,
                              QTableWidgetItem,
                             QSpacerItem, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPalette, QBrush, QImage, QColor, QGuiApplication
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

_PM_CACHE = {}

def _load_transparent_pixmap(path: str, size: int) -> QPixmap:
    """加载 PNG 并将近白色背景转为透明，返回缩放后的 QPixmap。

    - 适用于源 PNG 不是透明底的情况（白底或近白底）。
    - 仅将非常接近白色的像素置为透明，避免把金黄色高光误删。
    - 添加简单缓存，避免重复处理。
    """
    full_path = resource_path(path)
    cache_key = (full_path, size)
    if cache_key in _PM_CACHE:
        return _PM_CACHE[cache_key]

    if not os.path.exists(full_path):
        return QPixmap()

    img = QImage(full_path)
    if img.isNull():
        return QPixmap()

    img = img.convertToFormat(QImage.Format_ARGB32)

    # 阈值与容差：非常接近白色才视为背景
    threshold = 245
    diff_tolerance = 12

    width = img.width()
    height = img.height()

    for y in range(height):
        for x in range(width):
            c = img.pixelColor(x, y)
            r, g, b, a = c.red(), c.green(), c.blue(), c.alpha()
            mx, mn = max(r, g, b), min(r, g, b)
            if r >= threshold and g >= threshold and b >= threshold and (mx - mn) <= diff_tolerance:
                c.setAlpha(0)
                img.setPixelColor(x, y, c)

    pix = QPixmap.fromImage(img)
    scaled = pix.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    _PM_CACHE[cache_key] = scaled
    return scaled

def create_star_widget(difficulty: int, star_size: int = 28):
    """根据难度数值(0-10)生成星级组件。0=0星, 5=2.5星, 10=5星。"""
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(2)  # 星星之间更紧凑
    container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    # 计算星星数量
    difficulty = max(0, min(10, int(difficulty)))
    full_stars = difficulty // 2
    has_half = (difficulty % 2) == 1

    # 读取三态星图：满星、半星、空星
    full_pm = _load_transparent_pixmap(os.path.join('images', 'star.png'), star_size)
    half_pm = _load_transparent_pixmap(os.path.join('images', 'half_star.png'), star_size)
    empty_pm = _load_transparent_pixmap(os.path.join('images', 'empty_star.png'), star_size)

    # 添加整星
    padding = 3  # 轻微收紧但保留足够边距
    for _ in range(full_stars):
        lbl = QLabel()
        if not full_pm.isNull():
            lbl.setPixmap(full_pm)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(star_size + padding, star_size + padding)
            # 阴影以提升可见度
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 0)
            shadow.setColor(QColor(0, 0, 0, 180))
            lbl.setGraphicsEffect(shadow)
        layout.addWidget(lbl)

    # 半星
    if has_half:
        lbl = QLabel()
        if not half_pm.isNull():
            lbl.setPixmap(half_pm)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedSize(star_size + padding, star_size + padding)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 0)
            shadow.setColor(QColor(0, 0, 0, 180))
            lbl.setGraphicsEffect(shadow)
        layout.addWidget(lbl)

    # 补足到5星的空星
    empties = 5 - full_stars - (1 if has_half else 0)
    for _ in range(max(0, empties)):
        el = QLabel()
        if not empty_pm.isNull():
            el.setPixmap(empty_pm)
            el.setAlignment(Qt.AlignCenter)
            el.setFixedSize(star_size + padding, star_size + padding)
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(12)
            shadow.setOffset(0, 0)
            shadow.setColor(QColor(0, 0, 0, 150))
            el.setGraphicsEffect(shadow)
        layout.addWidget(el)

    # 不添加任何文本；0星时容器为空

    return container

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
            self.layout.setContentsMargins(8, 3, 8, 3)
            self.hero_image_size = (220, 280)  # 进一步大幅放大武将图片
            self.faction_image_size = (60, 60)
            self.font_size_name = "20px"
            self.font_size_hand = "20px"
        else: # 其他玩家，更紧凑
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(3, 3, 3, 3)
            self.hero_image_size = (180, 220)  # 进一步大幅放大其他玩家武将图片
            self.faction_image_size = (50, 50)
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
        self.combo.addItems(['身份局', '国战', '1v1', '测试模式'])
        
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
    def __init__(self, parent=None):
        super().__init__(parent)
        from mr_cards import all_heroes
        import random
        self.main_window = parent
        self.all_heroes = list(all_heroes.keys())
        
        # 检查是否为测试模式，如果是则使用所有武将，否则随机选择三个
        if hasattr(self.main_window, 'selected_mode') and self.main_window.selected_mode == '测试模式':
            self.available_heroes = self.all_heroes
            print(f"测试模式：使用所有武将，共 {len(self.available_heroes)} 个")
            self.setWindowTitle('选择你的武将 (测试模式)')
        else:
            # 随机选择三个武将供玩家选择
            self.available_heroes = random.sample(self.all_heroes, min(3, len(self.all_heroes)))
            print(f"选择的武将: {self.available_heroes}")  # 调试信息
        self.selected_hero = None
        
        self.setWindowTitle('选择你的武将')
        # 根据模式设置窗口大小
        if hasattr(self.main_window, 'selected_mode') and self.main_window.selected_mode == '测试模式':
            # 测试模式：更大的窗口以容纳所有武将
            self.setFixedSize(1600, 1200)
        else:
            # 正常模式：标准窗口大小
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
        
        # 检查是否为测试模式，如果是则使用网格布局，否则使用水平布局
        if hasattr(self.main_window, 'selected_mode') and self.main_window.selected_mode == '测试模式':
            # 测试模式：使用网格布局显示所有武将
            hero_layout = QGridLayout(hero_widget)
            hero_layout.setSpacing(30)  # 增大间距
            hero_layout.setAlignment(Qt.AlignCenter)
            # 设置滚动区域
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(hero_widget)
            layout.addWidget(scroll_area)
        else:
            # 正常模式：使用水平布局
            hero_layout = QHBoxLayout(hero_widget)
            hero_layout.setSpacing(30)  # 增大间距
            hero_layout.setAlignment(Qt.AlignCenter)
            layout.addWidget(hero_widget)
        
        self.hero_buttons = []
        for i, hero_name in enumerate(self.available_heroes):
            hero_card = all_heroes[hero_name]
            
            # 创建武将卡片容器
            card_widget = QWidget()
            card_widget.setFixedSize(320, 600)  # 缩小卡片尺寸
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
                    target_width = 300  # 缩小图片宽度
                    target_height = int(target_width * 600 / 530)  # 约340，按比例缩小
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
            name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: black; margin: 0px;")  # 缩小字体
            name_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(name_label)
            
            # 势力信息
            team_map = {'shu': '蜀', 'wei': '魏', 'wu': '吴', 'qun': '群'}
            team_text = team_map.get(hero_card.team, hero_card.team)
            team_label = QLabel(f"势力: {team_text}")
            team_label.setStyleSheet("font-size: 16px; color: black; margin: 0px;")  # 缩小字体
            team_label.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(team_label)
            
            # 技能描述（完整版）
            skill_label = QLabel(hero_card.skill_description)
            skill_label.setStyleSheet("font-size: 16px; color: black; margin: 0px; line-height: 1.0;")  # 缩小字体
            skill_label.setAlignment(Qt.AlignLeft)
            skill_label.setWordWrap(True)
            card_layout.addWidget(skill_label)
            
            # 特点信息
            if hasattr(hero_card, 'tags') and hero_card.tags:
                tags_label = QLabel(f"特点: {hero_card.tags}")
                tags_label.setStyleSheet("font-size: 20px; color: #222; margin: 0px; font-weight: bold;")
                tags_label.setAlignment(Qt.AlignCenter)
                card_layout.addWidget(tags_label)
            
            # 星级展示（难度换算为星级：0=0星，5=2.5星，10=5星），前缀“操作难度”
            if hasattr(hero_card, 'difficulty'):
                star_widget = create_star_widget(getattr(hero_card, 'difficulty', 0), star_size=28)
                star_container = QWidget()
                star_layout = QHBoxLayout(star_container)
                star_layout.setContentsMargins(0, 0, 0, 0)
                star_layout.setSpacing(2)
                star_layout.setAlignment(Qt.AlignCenter)
                prefix_label = QLabel('操作难度:')
                prefix_label.setStyleSheet('font-size: 20px; color: #222; font-weight: bold; padding-right: 0px;')
                star_layout.addWidget(prefix_label)
                star_layout.addWidget(star_widget)
                card_layout.addWidget(star_container)
            
            # 使卡片可点击
            card_widget.hero_name = hero_name  # 存储武将名称
            card_widget.mousePressEvent = self.create_hero_click_handler(card_widget, hero_name)
            card_widget.setCursor(Qt.PointingHandCursor)
            
            self.hero_buttons.append((card_widget, hero_name))
            
            # 根据模式添加到不同的布局
            if hasattr(self.main_window, 'selected_mode') and self.main_window.selected_mode == '测试模式':
                # 测试模式：使用网格布局，每行3个
                row = i // 3
                col = i % 3
                hero_layout.addWidget(card_widget, row, col)
            else:
                # 正常模式：使用水平布局
                hero_layout.addWidget(card_widget)
        
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
            
        self.main_window.start_game(player_hero, other_heros)
        self.accept()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # 基础尺寸与缩放初始化
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.base_width = screen_geometry.width()
        self.base_height = screen_geometry.height()
        self.scale_factor = 1.0
        self.scaled_components = []  # 需要缩放组件注册

        # 历史记录（仅作缓存，真实数据在 game.history_lines）
        self.history_lines = []

        # 窗口属性
        self.setWindowTitle('Trino 游戏')
        self.setMinimumSize(1200, 700)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        self.setAutoFillBackground(True)

        # 状态
        self.wusheng_active = False
        # 是否允许本回合手动结束（默认不允许）
        self.allow_manual_end = False
        # 是否处于主菜单（用于中断任何仍在排队的计时回调）
        self.in_main_menu = False

        # 全局样式（对话框更明亮）
        QApplication.instance().setStyleSheet("""
            QMessageBox, QInputDialog { background-color: white; color: black; }
            QDialog QLabel, QMessageBox QLabel, QInputDialog QLabel { color: black; }
            QDialog QPushButton, QMessageBox QPushButton, QInputDialog QPushButton {
                background-color: #f0f0f0; border: 1px solid #adadad; padding: 5px; min-width: 60px; border-radius: 3px; color: black;
            }
            QDialog QPushButton:hover, QMessageBox QPushButton:hover, QInputDialog QPushButton:hover { background-color: #e1e1e1; }
            QListWidget, QComboBox, QLineEdit { background-color: white; color: black; border: 1px solid #adadad; }
        """)

        # 主布局与基本容器
        self.main_layout = QVBoxLayout(self)
        self.game_widget = None
        self.player_widgets = {}

        # 初始化背景并显示主菜单
        self._init_background()
        self.show_main_menu()

    def _force_close_all_dialogs(self):
        """强制关闭所有仍在打开的对话框/消息框，避免残留的模态窗口阻塞主界面。"""
        try:
            app = QApplication.instance()
            if not app:
                return
            for w in list(app.topLevelWidgets()):
                try:
                    from PyQt5.QtWidgets import QDialog
                    if w is self:
                        continue
                    # 将所有顶层窗口恢复为非模态并尝试关闭（无论是否可见）
                    try:
                        w.setWindowModality(Qt.NonModal)
                    except Exception:
                        pass
                    if isinstance(w, QDialog):
                        try:
                            w.setModal(False)
                        except Exception:
                            pass
                    try:
                        w.hide()
                    except Exception:
                        pass
                    try:
                        w.close()
                    except Exception:
                        pass
                except Exception:
                    continue
            QApplication.processEvents()
        except Exception:
            pass

    def _reenable_all_children(self):
        """遍历当前窗口的所有子控件，强制启用并允许鼠标事件。"""
        try:
            for child in self.findChildren(QWidget):
                try:
                    child.setEnabled(True)
                    child.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                except Exception:
                    continue
            QApplication.processEvents()
        except Exception:
            pass

    def _reset_window_state(self):
        """重置窗口为可交互的非模态常规状态，并获取焦点。"""
        try:
            self.setWindowModality(Qt.NonModal)
            self.setEnabled(True)
            self.setUpdatesEnabled(True)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.setFocusPolicy(Qt.StrongFocus)
            # 释放潜在的鼠标/键盘抓取
            try:
                mg = QWidget.mouseGrabber()
                if mg is not None:
                    mg.releaseMouse()
            except Exception:
                pass
            try:
                kg = QWidget.keyboardGrabber()
                if kg is not None:
                    kg.releaseKeyboard()
            except Exception:
                pass
            # 恢复光标（最多还原一次，避免阻塞）
            try:
                QApplication.restoreOverrideCursor()
            except Exception:
                pass
            # 退出全屏 -> 最大化 -> 普通，确保系统恢复窗口管理
            if self.isFullScreen():
                self.showNormal()
            # 重置窗口标志为标准窗口
            self.setWindowFlags(Qt.Window | Qt.WindowMinMaxButtonsHint)
            self.show()
            self.showMaximized()
            self.showNormal()
            self.activateWindow()
            self.raise_()
            QApplication.processEvents()
        except Exception:
            pass

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
        # 关闭所有可能残留的模态对话框
        self._force_close_all_dialogs()
        self._reset_window_state()
        # 标记回到主菜单，并清理游戏引用
        self.in_main_menu = True
        if hasattr(self, 'game') and self.game:
            try:
                self.game.game_over = True
            except Exception:
                pass
            self.game = None

        # 恢复窗口为常规大小，避免全屏残留影响点击
        try:
            if self.isFullScreen():
                self.showNormal()
        except Exception:
            pass

        # 主动激活并置顶窗口，防止焦点被隐藏窗口/对话框占用
        try:
            self.activateWindow()
            self.raise_()
        except Exception:
            pass
        
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setAlignment(Qt.AlignCenter)
        menu_layout.setSpacing(30)  # 增加按钮间距

        self.start_btn = QPushButton('开始游戏')
        self.hero_btn = QPushButton('武将图鉴')
        self.rule_btn = QPushButton('游戏规则')
        self.version_btn = QPushButton('版本信息')
        self.exit_btn = QPushButton('退出游戏')

        self.btns = [self.start_btn, self.hero_btn, self.rule_btn, self.version_btn, self.exit_btn]
        # 根据是否全屏自适应按钮尺寸与字体
        is_full = self.isFullScreen()
        if is_full:
            # 全屏时使用正常尺寸
            base_size = (300, 60)
            font_px = 28
            padding_v = 10
            min_h = 60
        else:
            # 非全屏时按钮变细长且字体变大
            base_size = (400, 45)  # 更宽但更矮，显得细长
            font_px = 32  # 字体变大
            padding_v = 8
            min_h = 45
        for btn in self.btns:
            self.add_scaled_component(btn, base_size=base_size, base_font_size=font_px)
            btn.setStyleSheet(f"""
                QPushButton {{
                    font-size: {font_px}px; color: white; background-color: #2980b9; 
                    border: 2px solid #3498db; border-radius: 10px;
                    padding: {padding_v}px; min-height: {min_h}px;
                }}
                QPushButton:hover {{ background-color: #3498db; }}
            """)
            menu_layout.addWidget(btn)

        self.main_layout.addWidget(menu_widget, alignment=Qt.AlignCenter)
        # 再次确保焦点在主窗口
        try:
            self.setFocus(Qt.ActiveWindowFocusReason)
        except Exception:
            pass

        # 保险起见：显式启用所有主菜单按钮
        for btn in self.btns:
            try:
                btn.setEnabled(True)
            except Exception:
                pass
        # 再保险：启用所有子控件
        self._reenable_all_children()

        # 先断开旧连接，避免重复绑定导致不可点击/多次触发
        for btn in (self.start_btn, self.exit_btn, self.rule_btn, self.hero_btn, self.version_btn):
            try:
                # disconnect 不带参数会断开该信号的所有槽连接
                btn.clicked.disconnect()
            except Exception:
                pass

        self.start_btn.clicked.connect(self.show_mode_dialog)
        self.exit_btn.clicked.connect(self.close)
        self.rule_btn.clicked.connect(self.show_rule_dialog)
        self.hero_btn.clicked.connect(self.show_hero_dialog)
        self.version_btn.clicked.connect(self.show_version_dialog)

    def clear_window(self):
        """清空窗口所有内容"""
        # 先完全清空布局中的部件，避免残留遮挡层
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
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

        # 强制处理一次事件队列，清理已删除部件的悬挂事件
        try:
            QApplication.processEvents()
        except Exception:
            pass

        # 在根窗口上移除任何可能残留的窗口遮罩
        try:
            self.setEnabled(True)
            self.setUpdatesEnabled(True)
            self.setWindowOpacity(1.0)
        except Exception:
            pass

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
        self.draw_pile_image.setPixmap(back_pixmap.scaled(80, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        
        self.draw_pile_count = QLabel()
        self.draw_pile_count.setAlignment(Qt.AlignCenter)
        self.draw_pile_count.setStyleSheet("font-size: 16px; color: white; font-weight: bold; background: rgba(0,0,0,0.5); border-radius: 5px;")
        
        # 添加牌堆组件到缩放系统
        self.add_scaled_component(self.draw_pile_image, base_size=(80, 120))
        self.add_scaled_component(self.draw_pile_count, base_font_size=16)
        
        draw_pile_layout.addWidget(self.draw_pile_image)
        draw_pile_layout.addWidget(self.draw_pile_count)
        self.grid_layout.addWidget(self.draw_pile_widget, 1, 0, alignment=Qt.AlignCenter)

        # 中心弃牌区 (中间)
        self.center_card_widget = QWidget()
        self.center_card_area_layout = QVBoxLayout(self.center_card_widget)
        self.center_card_area_layout.setAlignment(Qt.AlignTop)  # 顶部对齐，让弃牌堆在顶部
        self.center_card_widget.setMinimumSize(600, 700)  # 大幅增大最小尺寸，更符合三国杀风格
        # 调整垂直对齐，让弃牌堆更靠上
        self.center_card_area_layout.setContentsMargins(0, 100, 0, 0)  # 增加顶部边距，让弃牌堆更靠上
        self.center_card_area_layout.setAlignment(Qt.AlignTop)  # 改为顶部对齐，让弃牌堆在顶部
        self.grid_layout.addWidget(self.center_card_widget, 1, 1, 1, 3) # 占据中间3列

        # 信息区 (右侧)
        self.info_area_widget = QWidget()
        self.info_area_widget.setMinimumWidth(250)  # 增加最小宽度，让信息区更大
        info_layout = QVBoxLayout(self.info_area_widget)
        info_layout.setAlignment(Qt.AlignCenter)
        info_layout.setSpacing(8)  # 减少组件间距，让布局更紧凑
        info_layout.setContentsMargins(3, 3, 3, 3)  # 减少边距
        
        # 信息标签
        self.info_label = QLabel() # 之前是 color_label
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet('font-size:18px;color:white;background:rgba(44, 62, 80, 0.8);border:2px solid #99c;border-radius:8px;padding:12px;min-width:220px;min-height:140px;')
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        
        # 添加信息标签到缩放系统
        self.add_scaled_component(self.info_label, base_font_size=18)
        
        # 历史记录按钮 (放在信息区下面)
        self.history_btn = QPushButton('📜 历史')
        self.add_scaled_component(self.history_btn, base_size=(150, 40), base_font_size=16)
        self.history_btn.setStyleSheet("""
            QPushButton { 
                font-size: 16px; font-weight: bold; color: white; 
                background-color: rgba(52, 152, 219, 0.8); 
                border: 2px solid #2980b9; border-radius: 6px; 
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

        # 设置行和列的伸展系数 - 按照三国杀风格调整
        self.grid_layout.setRowStretch(0, 1) # 顶部玩家区域 - 最小占比
        self.grid_layout.setRowStretch(1, 15) # 中部游戏区域 - 最大占比，进一步增大
        self.grid_layout.setRowStretch(2, 1) # 底部玩家区域 - 最小占比
        self.grid_layout.setColumnStretch(0, 1) # 牌堆 - 最小占比
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 12) # 中心弃牌区 - 减少占比，给信息区更多空间
        self.grid_layout.setColumnStretch(3, 1)
        self.grid_layout.setColumnStretch(4, 3) # 信息区 - 增加占比，给更多空间

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
        self.top_area.setSpacing(20) # 减少玩家控件之间的间距，让布局更紧凑

        # 底部主玩家区域
        main_player = self.game.player_list[main_player_pos]
        main_player_widget = PlayerInfoWidget(main_player, is_main_player=True, is_current=True) # 主玩家默认高亮
        self.player_widgets[main_player_pos] = main_player_widget
        self.bottom_area.addWidget(main_player_widget, 0, 0, 2, 1) # (row, col, rowspan, colspan)

        # 手牌区
        self.card_area = QWidget()
        self.card_area_layout = QHBoxLayout(self.card_area)
        self.card_area_layout.setSpacing(-30) # 回调到原始间距
        self.card_area_layout.setAlignment(Qt.AlignCenter)
        self.bottom_area.addWidget(self.card_area, 0, 1, 2, 3)
        
        # 操作区和技能区 - 重新设计布局
        right_panel_widget = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_widget)
        right_panel_layout.setContentsMargins(0,0,0,0)
        right_panel_layout.setSpacing(20)  # 大幅增加操作区和技能信息区之间的间距

        # 操作区域 - 放在上面
        self.action_area = QWidget()
        self.action_area_layout = QVBoxLayout(self.action_area)
        self.action_area_layout.setSpacing(6)  # 进一步减少间距
        self.action_area_layout.setAlignment(Qt.AlignCenter)
        self.action_area_layout.setContentsMargins(3, 3, 3, 3)  # 减少边距
        
        # 技能信息区域 - 放大并左移，放在下面
        self.my_skill_label = QLabel()
        self.my_skill_label.setWordWrap(True)
        self.my_skill_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.my_skill_label.setStyleSheet("""
            font-size: 18px; color: white; background: rgba(0,0,0,0.6); 
            border: 1px solid #99c; border-radius: 6px; padding: 12px; min-height: 160px; min-width: 250px;
        """)
        
        # 添加技能标签到缩放系统
        self.add_scaled_component(self.my_skill_label, base_font_size=18)
        
        right_panel_layout.addWidget(self.action_area)
        right_panel_layout.addWidget(self.my_skill_label)
        right_panel_layout.setStretchFactor(self.action_area, 1)
        right_panel_layout.setStretchFactor(self.my_skill_label, 2)  # 技能信息区域占更多空间

        self.bottom_area.addWidget(right_panel_widget, 0, 4, 2, 1)

        # 设置底部列的伸展系数 - 按照三国杀风格调整
        self.bottom_area.setColumnStretch(0, 1) # 主玩家信息 - 减少占比
        self.bottom_area.setColumnStretch(1, 15) # 手牌区 - 减少占比，给右侧更多空间
        self.bottom_area.setColumnStretch(2, 0)
        self.bottom_area.setColumnStretch(3, 0)
        self.bottom_area.setColumnStretch(4, 4) # 操作和技能区 - 大幅增加占比，给更多空间

        # 添加退出游戏按钮到右上角
        self.exit_btn = QPushButton('退出游戏')
        self.add_scaled_component(self.exit_btn, base_font_size=14)
        btn_style = """
            QPushButton { font-size: 14px; font-weight: bold; color: white; background-color: #e74c3c; 
                          border: 2px solid #c0392b; border-radius: 6px; padding: 6px 10px; min-height: 30px; }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.exit_btn.setStyleSheet(btn_style)
        self.exit_btn.clicked.connect(self.on_exit_game_clicked)
        
        # 将退出按钮添加到右上角
        self.top_area.addWidget(self.exit_btn, 0, Qt.AlignTop | Qt.AlignRight)

    # 加历史记录
    def on_history_updated(self, message):
        """Game 调用：同步历史记录到GUI并更新按钮计数"""
        if hasattr(self, 'game') and self.game:
            self.history_lines = list(self.game.history_lines)
        if hasattr(self, 'history_btn') and self.history_btn:
            try:
                self.history_btn.setText(f'📜 历史 ({len(self.history_lines)})')
            except RuntimeError:
                pass

    def show_history_dialog(self):
        """显示历史记录对话框"""
        dialog = HistoryDialog(self.history_lines, self)
        dialog.exec_()


    

    def start_game(self, player_hero, other_heros):
        from game import Game
        
        # 进入游戏时变为全屏
        if not self.isFullScreen():
            self.showFullScreen()
        
        # 清空历史记录
        self.history_lines = []  # 清空本地缓存（Game 会重新推送）

        # 清空缩放组件列表，避免内存泄漏
        self.scaled_components.clear()

        # 重置获胜对话框标志
        self._winner_dialog_shown = False

        num_players = len(other_heros) + 1
        # 检查是否为测试模式
        test_mode = hasattr(self, 'selected_mode') and self.selected_mode == '测试模式'
        self.game = Game(player_num=num_players, test_mode=test_mode)
        self.game.set_gui(self)

        # 进入游戏状态
        self.in_main_menu = False

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
            self.history_btn.setText(f'📜 历史 ({len(self.history_lines)})')

        # 6. 启动标准游戏流程（在GUI模式下使用异步方式）
        self.start_standard_game_loop()

    def start_standard_game_loop(self):
        """启动标准游戏流程（GUI异步版本）"""
        # 委托给game.py处理游戏逻辑
        self.game.start_gui_game_loop()

    def execute_game_loop_step(self):
        """执行游戏循环的一个步骤 - 只负责界面更新"""
        # 若已退出到主菜单或游戏对象不存在/结束，忽略计时回调
        if not hasattr(self, 'game') or (self.game is None) or self.in_main_menu or getattr(self.game, 'game_over', False):
            return
        # 委托给game.py处理游戏逻辑
        self.game.execute_gui_game_step()

    def continue_game_loop(self):
        """继续游戏循环 - 由游戏逻辑调用"""
        if not hasattr(self, 'game') or (self.game is None) or self.in_main_menu or getattr(self.game, 'game_over', False):
            return
        # 委托给game.py处理游戏逻辑
        self.game.continue_gui_game_loop()

    def handle_gui_jump_turn(self):
        """在GUI模式下处理跳牌玩家的特殊回合 - 只负责界面更新"""
        if not hasattr(self, 'game') or (self.game is None) or self.in_main_menu or getattr(self.game, 'game_over', False):
            return
        # 委托给game.py处理游戏逻辑
        self.game.handle_gui_jump_turn()

    def execute_jump_player_turn_gui(self, jump_player):
        """在GUI模式下执行跳牌玩家的特殊回合 - 只负责界面更新"""
        if not hasattr(self, 'game') or (self.game is None) or self.in_main_menu or getattr(self.game, 'game_over', False):
            return
        # 委托给game.py处理游戏逻辑
        self.game.execute_jump_player_turn_gui(jump_player)

    def schedule_ai_turn(self, delay_ms):
        """安排AI回合执行"""
        QTimer.singleShot(delay_ms, self.execute_game_loop_step)

    def schedule_continue_loop(self, delay_ms):
        """安排继续游戏循环"""
        QTimer.singleShot(delay_ms, self.continue_game_loop)

    def schedule_jump_player_turn(self, jump_player, delay_ms):
        """安排跳牌玩家回合执行"""
        QTimer.singleShot(delay_ms, lambda: self.execute_jump_player_turn_gui(jump_player))

    def stop_game_loop(self):
        """停止游戏循环"""
        if hasattr(self, 'game_loop_timer'):
            self.game_loop_timer.stop()

    def restart_game_loop(self):
        """重启游戏循环"""
        if hasattr(self, 'game_loop_timer'):
            self.game_loop_timer.start(100)

    # 过时：get_cur_player_info 已由 game.get_current_player_info 直接替代，删除以精简接口

    def show_game_round(self, first_round=False):
        """显示当前回合"""
        # 获取当前玩家信息
        player_info = self.game.get_current_player_info()
        player = player_info['player']
        draw_n = player_info['draw_n']
        
        # 只在真正开始新回合时才重置回合行动标志
        # 避免在+牌串处理过程中错误地重置标志
        if self.game.is_current_player_human() and not self.game.draw_n > 0:
            self.game.turn_action_taken = False
            # 新回合开始时，默认不允许手动结束回合
            self.allow_manual_end = False
            print(f"DEBUG: Reset turn_action_taken for {player.mr_card.name}")
        
        # 更新玩家信息显示
        for position, player_widget in self.player_widgets.items():
            is_current = (position == self.game.cur_location)
            player_widget.update_info(self.game.player_list[position], is_current)
        
        # 更新中央牌堆显示
        self.show_center_card_stack()
        
        # 更新摸牌堆数量
        self.update_draw_pile_count()
        
        # 更新历史记录
        self.render_info_area()
        
        # 更新技能说明区域 - 始终显示人类玩家的技能
        human_player = None
        for p in self.game.player_list:
            if self.game._is_player_human(p):
                human_player = p
                break
        if human_player:
            self.update_skill_description_area(human_player)
        
        # 根据当前玩家类型处理
        if self.game.is_current_player_ai():
            # AI玩家回合
            try:
                if hasattr(self, 'ai_status_label') and self.ai_status_label is not None:
                    self.ai_status_label.setVisible(True)
                    self.ai_status_label.setText(f"AI ({player.mr_card.name}) 正在思考...")
            except RuntimeError:
                pass  # 如果标签已被删除，静默忽略
            # 禁用操作按钮
            self.disable_action_buttons()
            # AI玩家的回合由游戏循环处理，这里只显示状态
        else:
            # 人类玩家回合
            try:
                if hasattr(self, 'ai_status_label') and self.ai_status_label is not None:
                    self.ai_status_label.setVisible(False)
            except RuntimeError:
                pass  # 如果标签已被删除，静默忽略

            # 检查是否为跳牌回合
            last_play_info = self.game.playedcards.get_last_play_info()
            if last_play_info:
                effective_card, original_card, source_player = last_play_info
                if source_player:
                    # 检查当前玩家是否可以跳牌（允许自跳）
                    potential_jumps = player.check_for_jump(effective_card)
                    if potential_jumps:
                        # 显示跳牌决策对话框（必须先决定跳牌结果，未跳牌前禁止发动与跳牌有关的技能）
                        self.show_jump_decision_dialog(player)
                        return  # 跳牌决策对话框会处理后续逻辑

            # 正常回合处理
            # 回合开始时，检查手牌是否超限
            if len(player.uno_list) > player.hand_limit:
                # 手牌超限时，显示提示信息
                self.show_temporary_message(f"{player.mr_card.name} 手牌已达上限，不能再摸牌！", duration=1500)
            
            # 渲染手牌区域
            can_draw_chain = player_info['can_draw_chain']
            self.render_hand_area(player.uno_list, draw_n, can_draw_chain, enable_click=True)
            
            # 渲染操作按钮区域
            is_forced_draw_pending = player_info['is_forced_draw_pending']
            can_play = player_info['can_play']
            print(f"DEBUG: Rendering action area for {player.mr_card.name}, turn_action_taken={self.game.turn_action_taken}")
            # 检查当前玩家是否为人类玩家
            is_current_player_turn = self.game.is_current_player_human()
            self.render_action_area(is_forced_draw_pending, can_play, is_current_player_turn)
            # 若是当前人类玩家且尚未行动，确保按钮启用（render_action_area 已配置，但再次保障）
            if is_current_player_turn and not self.game.turn_action_taken:
                self.enable_action_buttons()
        
        # 如果是第一回合，总是显示人类玩家的手牌（无论当前玩家是谁）
        if first_round:
            # 找到人类玩家
            human_player = None
            for p in self.game.player_list:
                if self.game._is_player_human(p):
                    human_player = p
                    break
            
            if human_player:
                # 显示人类玩家的手牌
                self.render_hand_area(human_player.uno_list, 0, False, enable_click=False)
                # 禁用操作按钮（因为不是人类玩家的回合）
                self.render_action_area(is_forced_draw_pending=False, can_play=False, is_current_player_turn=False)
                # 更新技能说明区域 - 显示人类玩家的技能
                self.update_skill_description_area(human_player)

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
            card_button.setFixedSize(140, 190)  # 缩小手牌尺寸
            
            display_card = card
            # 如果武圣激活，并且是红色牌，则显示为红+2
            if self.wusheng_active and card.color == 'red':
                display_card = UnoCard('draw2', 'red', 0)

            # 加载并缩放图片
            pixmap = QPixmap(get_card_image_path(display_card))
            scaled_pixmap = pixmap.scaled(140, 190, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon = QIcon(scaled_pixmap)
            card_button.setIcon(icon)
            card_button.setIconSize(QSize(140, 190))  # 让图标完全填充按钮尺寸，确保图片显示完整
            
            # 应用当前的高亮状态
            if hasattr(self, 'selected_card_idx') and self.selected_card_idx == i:
                card_button.setStyleSheet("background-color: #f39c12; border: 2px solid #e67e22; border-radius: 5px;")
            else:
                card_button.setStyleSheet("background-color: transparent; border: none;")
                
            if enable_click:
                card_button.clicked.connect(lambda _, idx=i: self.on_card_clicked(idx))
            self.card_buttons.append(card_button)
            self.card_area_layout.addWidget(card_button)

    def render_action_area(self, is_forced_draw_pending=False, can_play=True, is_current_player_turn=True):
        """渲染操作按钮区域"""
        # 清空旧按钮
        while self.action_area_layout.count():
            item = self.action_area_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Clear old references to prevent accessing deleted widgets
        for attr in ['play_btn', 'draw_btn', 'skill_btn', 'end_btn', 'skill_info_btn']:
            if hasattr(self, attr):
                delattr(self, attr)

        # 使用game.py的状态管理器获取当前玩家
        cur_player = self.game.get_current_player()
        
        active_skills = []
        if cur_player.mr_card and cur_player.mr_card.skills:
            for skill in cur_player.mr_card.skills:
                if skill.is_active_in_turn:
                    active_skills.append(skill)
        
        # 出牌按钮
        self.play_btn = QPushButton('出牌')
        self.add_scaled_component(self.play_btn, base_font_size=18)
        btn_style = """
            QPushButton { font-size: 18px; font-weight: bold; color: white; background-color: #e74c3c; 
                          border: 2px solid #c0392b; border-radius: 6px; padding: 10px 16px; min-height: 40px; min-width: 120px; }
            QPushButton:hover { background-color: #c0392b; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.play_btn.setStyleSheet(btn_style)
        self.play_btn.clicked.connect(self.on_play_card_clicked)
        # 只有在当前玩家回合且满足其他条件时才启用
        play_enabled = is_current_player_turn and can_play and not self.game.turn_action_taken
        self.play_btn.setEnabled(play_enabled)
        print(f"DEBUG: Play button enabled={play_enabled}, is_current_player_turn={is_current_player_turn}, can_play={can_play}, turn_action_taken={self.game.turn_action_taken}")
        self.action_area_layout.addWidget(self.play_btn)

        # 摸牌按钮
        draw_btn_text = '强制摸牌' if is_forced_draw_pending else '摸牌'
        self.draw_btn = QPushButton(draw_btn_text)
        self.add_scaled_component(self.draw_btn, base_font_size=18)
        btn_style = """
            QPushButton { font-size: 18px; font-weight: bold; color: white; background-color: #3498db; 
                          border: 2px solid #2980b9; border-radius: 6px; padding: 10px 16px; min-height: 40px; min-width: 120px; }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.draw_btn.setStyleSheet(btn_style)
        self.draw_btn.clicked.connect(self.on_draw_card_clicked)
        # 只有在当前玩家回合且满足其他条件时才启用
        draw_enabled = is_current_player_turn and (is_forced_draw_pending or not self.game.turn_action_taken)
        self.draw_btn.setEnabled(draw_enabled)
        print(f"DEBUG: Draw button enabled={draw_enabled}, is_current_player_turn={is_current_player_turn}, turn_action_taken={self.game.turn_action_taken}, is_forced_draw_pending={is_forced_draw_pending}")
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
            self.add_scaled_component(self.skill_btn, base_font_size=20)
            btn_style = """
                QPushButton { font-size: 20px; font-weight: bold; color: white; background-color: #9b59b6; 
                              border: 2px solid #8e44ad; border-radius: 8px; padding: 12px 20px; min-height: 45px; min-width: 140px; }
                QPushButton:hover { background-color: #8e44ad; }
                QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
            """
            self.skill_btn.setStyleSheet(btn_style)
            self.skill_btn.clicked.connect(self.on_skill_button_clicked)
            
            # 只有在当前玩家回合且满足其他条件时才启用
            button_enabled = (is_current_player_turn and 
                            not self.game.turn_action_taken and 
                            not is_forced_draw_pending and 
                            (skill_available or self.wusheng_active))  # 武圣激活时允许取消
            
            self.skill_btn.setEnabled(button_enabled)
            print(f"DEBUG: Skill button enabled={button_enabled}, is_current_player_turn={is_current_player_turn}, turn_action_taken={self.game.turn_action_taken}, is_forced_draw_pending={is_forced_draw_pending}, skill_available={skill_available}, wusheng_active={self.wusheng_active}")
            
            # 如果技能不可用，设置工具提示
            if not skill_available and not self.wusheng_active:
                self.skill_btn.setToolTip(skill_unavailable_reason)
            else:
                self.skill_btn.setToolTip("")
                
            self.action_area_layout.addWidget(self.skill_btn)

        # 结束回合按钮
        self.end_btn = QPushButton('结束回合')
        self.add_scaled_component(self.end_btn, base_font_size=18)
        btn_style = """
            QPushButton { font-size: 18px; font-weight: bold; color: white; background-color: #f39c12; 
                          border: 2px solid #e67e22; border-radius: 8px; padding: 10px 16px; min-height: 40px; min-width: 120px; }
            QPushButton:hover { background-color: #e67e22; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        self.end_btn.setStyleSheet(btn_style)
        self.end_btn.clicked.connect(self.on_end_turn_clicked)
        # 在未进行有效动作前，不允许手动结束回合
        # 只有在被明确允许的特殊情况下（如某些技能/状态需要）才启用
        self.end_btn.setEnabled(bool(self.allow_manual_end))
        self.action_area_layout.addWidget(self.end_btn)

        # 更新技能说明区域
        self.update_skill_description_area(cur_player)

    def update_skill_description_area(self, player):
        """更新技能说明区域"""
        if not player.mr_card or not player.mr_card.skills:
            self.my_skill_label.setText("")
            return
            
        skill_text = f"<b>{player.mr_card.name}的技能：</b><br><br>"
        for skill in player.mr_card.skills:
            skill_text += f"<b>{skill.name}</b>: {skill.description}<br><br>"
        
        self.my_skill_label.setText(skill_text)

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
        # 如果当前存在可跳牌机会，先处理跳牌，再允许发动技能
        try:
            cur_player = self.game.get_current_player()
            last_play_info = self.game.playedcards.get_last_play_info()
            if last_play_info and cur_player.check_for_jump(last_play_info[0]):
                self.show_temporary_message("当前可跳牌，请先完成跳牌再发动技能", 1200)
                self.show_jump_decision_dialog(cur_player)
                return
        except Exception:
            pass
        
        # 检查是否武圣已激活，如果是则取消武圣状态
        if self.wusheng_active:
            print("DEBUG: Cancelling WuSheng")
            self.wusheng_active = False
            self.show_temporary_message("武圣技能已取消", 800)
            # 立即更新技能按钮文本
            if hasattr(self, 'skill_btn'):
                self.skill_btn.setText('技能')
            self.show_game_round()
            return
        
        # 调用game.py中的技能逻辑
        cur_player = self.game.get_current_player()
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
        """直接激活技能的最终执行逻辑 - 只负责用户交互"""
        player = self.game.get_current_player()
        # 统计：记录技能发动
        try:
            if hasattr(self, 'game') and self.game:
                self.game.record_skill(player, skill.name)
        except Exception:
            pass
        
        # 重置选中的卡牌
        self.selected_card_idx = None
        
        # 委托给game.py处理技能逻辑
        if skill.name == '反间':
            player.activate_skill('反间')
            # 反间技能有自己的UI流程和刷新，这里不需要再调用show_game_round
            # 反间技能执行完成后会自动结束回合
        elif skill.name == '武圣':
            self.activate_wusheng_skill()
        elif skill.name == '缔盟':
            player.activate_skill('缔盟')
            # 缔盟技能有自己的UI流程和刷新，这里不需要再调用show_game_round
        else:
            self.show_message_box("提示", f"技能 [{skill.name}] 的界面交互尚未实现。")
            # 不再在这里调用show_game_round，由on_skill_button_clicked统一处理
        
        # 对于会结束回合的技能，自动结束回合并通知游戏继续循环
        if skill.name in ['缔盟']:
            # 自动结束回合
            player.game.turn_action_taken = True
            # 通知游戏继续循环
            self.game.notify_gui_continue_loop()
        elif skill.name == '武圣':
            # 武圣技能不结束回合，只是激活状态
            pass
        elif skill.name == '反间':
            # 反间技能在_execute_fanjian_skill中已经处理了回合结束
            # 通知游戏继续循环
            self.game.notify_gui_continue_loop()
        else:
            # 其他技能也结束回合
            player.game.turn_action_taken = True
            # 通知游戏继续循环
            self.game.notify_gui_continue_loop()

    def activate_wusheng_skill(self):
        """激活武圣技能"""
        print("DEBUG: activate_wusheng_skill called")
        player = self.game.get_current_player()
        
        # 重置选中的卡牌
        self.selected_card_idx = None
        
        # 检查玩家是否有红色牌
        red_cards = [i for i, card in enumerate(player.uno_list) if card.color == 'red']
        
        if not red_cards:
            self.show_message_box("提示", "你没有红色牌，无法发动武圣技能。")
            return
        
        # 设置武圣状态为激活
        self.wusheng_active = True
        print(f"DEBUG: Set wusheng_active = {self.wusheng_active}")
        
        # 显示提示信息
        self.show_temporary_message("武圣技能已激活！请选择一张红色牌，它将作为红+2打出。再次点击技能按钮可取消。", 1500)
        
        # 刷新界面，让玩家选择牌
        self.show_game_round()
        
        # 武圣技能不结束回合，只是激活状态，等待玩家选择牌

    def choose_target_player_dialog(self, exclude_self=False):
        """选择目标玩家的对话框"""
        # 重置选中的卡牌
        self.selected_card_idx = None
        
        # 使用game.py的状态管理器获取玩家列表
        players = self.game.get_players_for_dialog(exclude_self)
        
        if not players:
            return None
        
        if len(players) == 1:
            return players[0]
        
        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择目标玩家")
        layout = QVBoxLayout(dialog)
        
        layout.addWidget(QLabel("请选择目标玩家:"))
        
        # 创建玩家选择列表
        list_widget = QListWidget()
        for player in players:
            item = QListWidgetItem(f"{player.mr_card.name} (位置 {player.position + 1})")
            item.setData(Qt.UserRole, player)
            list_widget.addItem(item)
        
        layout.addWidget(list_widget)
        
        # 添加按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec_() == QDialog.Accepted and list_widget.selectedItems():
            return list_widget.selectedItems()[0].data(Qt.UserRole)
        return None

    def choose_specific_card_dialog(self, player, cards, prompt):
        """弹窗选择卡牌"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择卡牌")
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
            }
        """)
        dialog.resize(600, 400)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加提示文本
        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        prompt_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(prompt_label)
        
        # 创建卡牌选择区域
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setSpacing(10)
        cards_layout.setAlignment(Qt.AlignCenter)
        
        selected_card = None
        card_buttons = []
        
        # 为每张卡牌创建按钮
        for i, card in enumerate(cards):
            card_btn = QPushButton()
            card_btn.setFixedSize(80, 120)
            card_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    background-color: white;
                }
                QPushButton:hover {
                    border-color: #3498db;
                }
                QPushButton:pressed {
                    border-color: #2980b9;
                    background-color: #ecf0f1;
                }
            """)
            
            # 设置卡牌图片
            card_image_path = get_card_image_path(card)
            if os.path.exists(card_image_path):
                pixmap = QPixmap(card_image_path)
                card_btn.setIcon(QIcon(pixmap.scaled(70, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                card_btn.setIconSize(QSize(70, 110))
            
            # 连接点击事件
            def make_click_handler(card):
                def click_handler():
                    nonlocal selected_card
                    selected_card = card
                    # 高亮选中的卡牌
                    for btn in card_buttons:
                        btn.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #bdc3c7;
                                border-radius: 8px;
                                background-color: white;
                            }
                            QPushButton:hover {
                                border-color: #3498db;
                            }
                        """)
                    card_btn.setStyleSheet("""
                        QPushButton {
                            border: 3px solid #e74c3c;
                            border-radius: 8px;
                            background-color: #fdf2f2;
                        }
                    """)
                return click_handler
            
            card_btn.clicked.connect(make_click_handler(card))
            card_buttons.append(card_btn)
            cards_layout.addWidget(card_btn)
        
        layout.addWidget(cards_widget)
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("确认")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        buttons_layout.addWidget(confirm_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        # 连接按钮事件
        confirm_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            return selected_card
        else:
            return None

    def choose_card_from_hand_dialog(self, player, prompt):
        """弹窗从手牌选择卡牌"""
        return self.choose_specific_card_dialog(player, player.uno_list, prompt)

    def choose_cards_to_discard_dialog(self, player, num_to_discard):
        """弹窗选择要弃置的牌"""
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("选择要弃置的牌")
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
            }
        """)
        dialog.resize(800, 500)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 添加提示文本
        prompt_label = QLabel(f"请选择 {num_to_discard} 张牌来弃置")
        prompt_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; margin: 10px;")
        prompt_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(prompt_label)
        
        # 创建卡牌选择区域
        cards_widget = QWidget()
        cards_layout = QHBoxLayout(cards_widget)
        cards_layout.setSpacing(10)
        cards_layout.setAlignment(Qt.AlignCenter)
        
        selected_cards = []
        card_buttons = []
        
        # 为每张卡牌创建按钮
        for i, card in enumerate(player.uno_list):
            card_btn = QPushButton()
            card_btn.setFixedSize(80, 120)
            card_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #bdc3c7;
                    border-radius: 8px;
                    background-color: white;
                }
                QPushButton:hover {
                    border-color: #3498db;
                }
                QPushButton:pressed {
                    border-color: #2980b9;
                    background-color: #ecf0f1;
                }
            """)
            
            # 设置卡牌图片
            card_image_path = get_card_image_path(card)
            if os.path.exists(card_image_path):
                pixmap = QPixmap(card_image_path)
                card_btn.setIcon(QIcon(pixmap.scaled(70, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)))
                card_btn.setIconSize(QSize(70, 110))
            
            # 连接点击事件
            def make_click_handler(card, btn):
                def click_handler():
                    if card in selected_cards:
                        # 取消选择
                        selected_cards.remove(card)
                        btn.setStyleSheet("""
                            QPushButton {
                                border: 2px solid #bdc3c7;
                                border-radius: 8px;
                                background-color: white;
                            }
                            QPushButton:hover {
                                border-color: #3498db;
                            }
                        """)
                    else:
                        # 添加选择
                        if len(selected_cards) < num_to_discard:
                            selected_cards.append(card)
                            btn.setStyleSheet("""
                                QPushButton {
                                    border: 3px solid #e74c3c;
                                    border-radius: 8px;
                                    background-color: #fdf2f2;
                                }
                            """)
                    
                    # 更新提示文本
                    remaining = num_to_discard - len(selected_cards)
                    if remaining > 0:
                        prompt_label.setText(f"还需选择 {remaining} 张牌")
                    else:
                        prompt_label.setText("选择完成，请点击确认")
                return click_handler
            
            card_btn.clicked.connect(make_click_handler(card, card_btn))
            card_buttons.append(card_btn)
            cards_layout.addWidget(card_btn)
        
        layout.addWidget(cards_widget)
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        
        confirm_btn = QPushButton("确认")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        buttons_layout.addWidget(confirm_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)
        
        # 连接按钮事件
        confirm_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 返回选中卡牌的索引
            selected_indices = []
            for card in selected_cards:
                if card in player.uno_list:
                    selected_indices.append(player.uno_list.index(card))
            return selected_indices if len(selected_indices) == num_to_discard else None
        else:
            return None



    def choose_to_use_skill_dialog(self, player, skill_name):
        """弹窗让玩家选择是否使用技能"""
        # 重置选中的卡牌
        self.selected_card_idx = None
        
        reply = QMessageBox.question(self, "技能选择", 
                                   f"是否使用技能【{skill_name}】？",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        return reply == QMessageBox.Yes

    def show_jump_decision_dialog(self, player):
        """显示跳牌决策对话框"""
        # 获取上一张牌信息
        last_play_info = self.game.playedcards.get_last_play_info()
        if not last_play_info:
            return False
        
        effective_card, original_card, source_player = last_play_info
        
        # 检查玩家是否有可以跳牌的牌
        potential_jumps = player.check_for_jump(effective_card)
        if not potential_jumps:
            return False
        
        # 创建跳牌决策对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("跳牌决策")
        dialog.setFixedSize(400, 300)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2c3e50;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: 2px solid #2980b9;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        # 标题
        title_label = QLabel(f"{player.mr_card.name}，你可以跳牌！")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        layout.addWidget(title_label)
        
        # 说明
        info_label = QLabel(f"上一张牌: {effective_card}")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        # 显示可以跳牌的牌（可选择列表）
        jumpable_cards = []
        for jump_info in potential_jumps:
            jumpable_cards.append(jump_info['original_card'])

        cards_label = QLabel("可以跳牌的牌（请选择其一）：")
        cards_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(cards_label)

        cards_list = QListWidget()
        for jump_info in potential_jumps:
            card = jump_info['original_card']
            item = QListWidgetItem(str(card))
            # 将完整的跳牌信息存入，便于后续直接执行标准跳牌流程（含跳牌相关技能）
            item.setData(Qt.UserRole, jump_info)
            cards_list.addItem(item)
        if cards_list.count() > 0:
            cards_list.setCurrentRow(0)
        layout.addWidget(cards_list)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        # 跳牌按钮（将所选卡牌一并传递）
        jump_btn = QPushButton("跳牌")
        jump_btn.clicked.connect(lambda: self.handle_jump_decision(
            player,
            True,
            dialog,
            cards_list.currentItem().data(Qt.UserRole) if cards_list.currentItem() else (potential_jumps[0] if potential_jumps else None)
        ))
        button_layout.addWidget(jump_btn)
        
        # 不跳牌按钮
        no_jump_btn = QPushButton("不跳牌")
        no_jump_btn.clicked.connect(lambda: self.handle_jump_decision(player, False, dialog))
        button_layout.addWidget(no_jump_btn)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec_()
        
        return True
    
    def handle_jump_decision(self, player, want_to_jump, dialog, selected_jump_info=None):
        """处理跳牌决策"""
        dialog.accept()
        
        if want_to_jump:
            # 玩家选择跳牌，执行标准跳牌流程（将触发与跳牌有关的技能）
            if selected_jump_info is not None:
                try:
                    player._execute_jump(player, selected_jump_info)
                except Exception:
                    # 退回默认跳牌逻辑
                    player.jump_turn()
            else:
                # 未选择时，走默认跳牌逻辑（取第一张可跳牌）
                player.jump_turn()
        else:
            # 玩家选择不跳牌，跳过这个特殊回合
            print(f"{player.mr_card.name} 选择不跳牌，跳过特殊回合")
            # 更新flag（在跳牌回合中，reverse/skip不生效）
            player._update_flags_after_jump_turn()
        
        # 继续游戏循环
        self.game.continue_game_after_jump_turn()

    def on_card_clicked(self, idx):
        """处理卡牌点击事件"""
        # 正常的卡牌选择逻辑（用于出牌）
        self.highlight_selected_card(idx)
        
        # 使用game.py的状态管理器
        player = self.game.get_current_player()
        if self.game.is_current_player_ai():
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



    def highlight_selected_card(self, idx):
        """高亮显示选中的卡牌"""
        # 重置所有卡牌的高亮状态
        for i, btn in enumerate(self.card_buttons):
            try:
                if i == idx:
                    btn.setStyleSheet("background-color: #f39c12; border: 2px solid #e67e22; border-radius: 5px;")
                else:
                    btn.setStyleSheet("background-color: transparent; border: none;")
            except RuntimeError:
                # 按钮已被删除，忽略错误
                continue
        self.selected_card_idx = idx

    def show_temporary_message(self, message, duration=800):
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
        # 重置选中的卡牌
        self.selected_card_idx = None
        
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

    def update_draw_pile_count(self):
        """更新牌堆数量标签"""
        # 使用game.py的状态管理器
        game_state = self.game.get_game_state()
        count = game_state['draw_pile_count']
        self.draw_pile_count.setText(f"{count}")

    def render_info_area(self):
        """更新右侧信息区的文本，使其更清晰"""
        # 使用game.py的状态管理器
        game_state = self.game.get_game_state()
        color = game_state['cur_color']
        color_map = {'red': '红色', 'blue': '蓝色', 'green': '绿色', 'yellow': '黄色', 'black': '任意'}
        
        # 获取上一张牌和当前玩家信息
        last_card = game_state['last_card']
        current_player = self.game.get_current_player()
        current_player_text = f"当前回合: <b>{current_player.mr_card.name}({current_player.position+1})</b>"
        
        # 根据游戏状态确定出牌要求
        if game_state['draw_n'] > 0:
            # 如果有强制摸牌，根据加牌串中最后一张牌的类型显示正确的出牌要求
            if game_state['draw_chain_cards']:
                # 获取加牌串中最后一张牌的类型
                last_chain_card = game_state['draw_chain_cards'][-1][0]  # effective_card
                if last_chain_card.type == 'draw2':
                    draw_requirement_text = f"当前出牌要求: <b>必须摸{game_state['draw_n']}张牌或出+2/+4</b>"
                elif last_chain_card.type == 'wild_draw4':
                    draw_requirement_text = f"当前出牌要求: <b>必须摸{game_state['draw_n']}张牌或出+4</b>"
                else:
                    # 默认情况
                    draw_requirement_text = f"当前出牌要求: <b>必须摸{game_state['draw_n']}张牌或出+2/+4</b>"
            else:
                # 没有加牌串信息时的默认显示
                draw_requirement_text = f"当前出牌要求: <b>必须摸{game_state['draw_n']}张牌或出+2/+4</b>"
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

        direction_text = f"游戏方向: {'顺序' if game_state['dir'] == 1 else '逆序'}"
        card_info_text = "上一张牌: 无"
        if last_card:
            card_display_str = ""
            if last_card.type == 'number':
                # 颜色数字
                card_display_str = f"{color_map.get(last_card.color, '')} <b>{last_card.value}</b>"
            elif last_card.type == 'wild':
                # 万能牌(选定颜色)
                if game_state['cur_color'] != 'black':
                    card_display_str = f"<b>万能牌({color_map.get(game_state['cur_color'], '')})</b>"
                else:
                    card_display_str = f"<b>万能牌</b>"
            elif last_card.type == 'wild_draw4':
                # 万能+4牌(选定颜色)
                if game_state['cur_color'] != 'black':
                    card_display_str = f"<b>万能+4牌({color_map.get(game_state['cur_color'], '')})</b>"
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

    def on_play_card_clicked(self):
        """处理出牌按钮的点击 - 只负责用户交互"""
        # 使用game.py的状态管理器获取人类玩家
        player = self.game.get_current_player()
        
        # 检查是否有选中的卡牌
        if not hasattr(self, 'selected_card_idx') or self.selected_card_idx is None:
            self.show_temporary_message("请先选择一张牌", duration=800)
            return
        
        # 调用game.py中的核心逻辑，如果武圣激活则传递wusheng_active参数
        if hasattr(self, 'wusheng_active') and self.wusheng_active:
            player.play(self.selected_card_idx, wusheng_active=True)
            # 武圣技能使用后，重置状态
            self.wusheng_active = False
            # 立即重新渲染手牌区域，显示原始牌值
            self.render_hand_area(player.uno_list, 0, False, enable_click=False)
        else:
            player.play(self.selected_card_idx)
        
        # 执行出牌后，禁用所有行动按钮
        self.disable_action_buttons()
        
        # 自动结束回合
        player.game.turn_action_taken = True
        # 完成了有效行动，不再需要手动结束
        self.allow_manual_end = False
        
        # 通知游戏继续循环
        self.game.notify_gui_continue_loop()

    def on_draw_card_clicked(self):
        """处理摸牌按钮的点击 - 只负责用户交互"""
        # 使用game.py的状态管理器获取人类玩家
        player = self.game.get_current_player()
        
        # 检查是否是强制摸牌
        game_state = self.game.get_game_state()
        if game_state['draw_n'] > 0:
            # 强制摸牌
            self.show_temporary_message(f"{player.mr_card.name} 强制摸了 {game_state['draw_n']} 张牌", duration=1000)
            # 调用强制摸牌逻辑
            player.handle_forced_draw()
        else:
            # 普通摸牌
            self.show_temporary_message(f"{player.mr_card.name} 摸了 1 张牌", duration=1000)
            # 调用普通摸牌逻辑
            player.draw_cards(1)
            # 执行摸牌后，禁用所有行动按钮
            self.disable_action_buttons()
            # 自动结束回合
            player.game.turn_action_taken = True
            # 完成了有效行动，不再需要手动结束
            self.allow_manual_end = False
        
        # 通知游戏继续循环
        self.game.notify_gui_continue_loop()

    def on_end_turn_clicked(self):
        """处理结束回合按钮的点击 - 只负责用户交互"""
        # 使用game.py的状态管理器获取人类玩家
        player = self.game.get_current_player()
        
        # 重置选中的卡牌
        self.selected_card_idx = None
        
        # 校验：只有在允许手动结束的情况下才可以结束回合
        if not self.allow_manual_end:
            self.show_temporary_message("需要先出牌、摸牌或发动技能", duration=1000)
            return
        # 结束回合
        player.game.turn_action_taken = True
        
        # 通知游戏继续循环
        self.game.notify_gui_continue_loop()

    def disable_action_buttons(self):
        """禁用所有操作按钮"""
        def safe_disable_button(button_name):
            try:
                if hasattr(self, button_name):
                    button = getattr(self, button_name)
                    if button and hasattr(button, 'setEnabled'):
                        button.setEnabled(False)
            except RuntimeError:
                # 按钮已被删除，忽略错误
                pass
        
        # 禁用所有操作按钮（除了技能说明按钮）
        safe_disable_button('play_btn')
        safe_disable_button('draw_btn')
        safe_disable_button('skill_btn')
        safe_disable_button('end_btn')
        # 技能说明按钮保持可用

    def enable_action_buttons(self):
        """启用操作按钮（仅在人类玩家当前回合且未行动时调用）"""
        def safe_enable_button(button_name):
            try:
                if hasattr(self, button_name):
                    button = getattr(self, button_name)
                    if button and hasattr(button, 'setEnabled'):
                        # 对结束回合按钮做特殊控制
                        if button_name == 'end_btn':
                            button.setEnabled(bool(self.allow_manual_end))
                        else:
                            button.setEnabled(True)
            except RuntimeError:
                pass
        safe_enable_button('play_btn')
        safe_enable_button('draw_btn')
        safe_enable_button('skill_btn')
        safe_enable_button('end_btn')

    def show_mode_dialog(self):
        """显示模式选择对话框"""
        dialog = ModeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            mode = dialog.selected_mode
            self.selected_mode = mode  # 保存选择的模式
            self.show_select_hero()

    def show_select_hero(self):
        """显示武将选择对话框"""
        select_dialog = SelectHeroDialog(self)
        select_dialog.exec_()

    def show_hero_dialog(self):
        """显示武将图鉴对话框"""
        from mr_cards import all_heroes
        dialog = QDialog(self)
        dialog.setWindowTitle('武将图鉴')
        dialog.setStyleSheet("background-color: white;")
        dialog.resize(1400, 900)

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
                img_label.setPixmap(pixmap.scaled(180, 252, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                img_label.setText("无图片")
                img_label.setFixedSize(180, 252)
            img_label.setAlignment(Qt.AlignCenter)
            hero_layout.addWidget(img_label)

            # 武将信息
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            
            name_label = QLabel(f"<b>{hero_card.name}</b> ({hero_card.team})")
            name_label.setStyleSheet("font-size: 18px;")
            
            skill_label = QLabel(hero_card.skill_description)
            skill_label.setWordWrap(True)
            skill_label.setAlignment(Qt.AlignTop)
            
            info_layout.addWidget(name_label)
            info_layout.addWidget(skill_label)
            
            # 特点信息
            if hasattr(hero_card, 'tags') and hero_card.tags:
                tags_label = QLabel(f"特点: {hero_card.tags}")
                tags_label.setStyleSheet("font-size: 20px; color: #222; font-weight: bold;")
                info_layout.addWidget(tags_label)
            
            # 图鉴页：在难度前标注“操作难度: ”并保留 x/10 文本
            if hasattr(hero_card, 'difficulty'):
                difficulty_label = QLabel(f"操作难度: {hero_card.difficulty}/10")
                difficulty_label.setStyleSheet("font-size: 20px; color: #222; font-weight: bold;")
                info_layout.addWidget(difficulty_label)
            info_layout.addStretch() # 将内容推到顶部

            hero_layout.addWidget(info_widget, stretch=1)
            grid_layout.addWidget(hero_box, row, col)

        scroll.setWidget(content_widget)

        # 集成“标签说明”到武将图鉴中（可展开/收起）
        tag_desc_text = (
            "标签说明\n"
            "爆发：快速减少自己的手牌数\n"
            "保护：使其他玩家被加牌数减少/不受控制效果影响\n"
            "博弈：与其他玩家进行博弈/技能有利有弊\n"
            "补益：帮助其他玩家进攻\n"
            "对策：针对某一类型的武将，使其技能效果削弱/失效\n"
            "额外行动：能够创造额外回合/回合外行动（出牌/弃牌）\n"
            "额外技能：可以获得/使用其他武将的技能\n"
            "反击：被加牌后可使其他玩家摸牌\n"
            "防御：使被加牌数减少\n"
            "辅助：帮助其他玩家减少手牌数\n"
            "干扰：改变其他玩家手牌\n"
            "过牌：通过弃置后摸牌调整手牌\n"
            "换位：可以改变玩家座位次序\n"
            "进攻：使其他玩家手牌数增加\n"
            "觉醒：拥有觉醒技\n"
            "控制：使其他玩家陷入异常状态而无法正常出牌/发动技能\n"
            "免疫：不受控制效果影响\n"
            "配合：需要与其他玩家合作才能发挥技能效果\n"
            "信息：可以得知牌堆/他人手牌信息\n"
            "削弱：使其他玩家无法进攻\n"
            "应变：可将手牌改变后打出/出牌要求放宽\n"
            "止损：被加牌后可弃牌\n"
            "追击：通过叠加加牌串加强进攻效果/使加牌同时对多个目标生效\n"
            "使命：拥有使命技（胜利条件改变）\n"
        )

        toggle_btn = QPushButton("标签说明 ▸")
        toggle_btn.setStyleSheet("font-size: 20px; font-weight: bold;")

        tag_desc_widget = QTextEdit()
        tag_desc_widget.setReadOnly(True)
        tag_desc_widget.setText(tag_desc_text)
        tag_desc_widget.setStyleSheet(
            "QTextEdit { background: rgba(255,255,255,210); color: #222; border: 1px solid #ccc; font-size: 18px; padding: 10px; }"
        )
        tag_desc_widget.setVisible(False)
        tag_desc_widget.setFixedHeight(260)

        def on_toggle():
            visible = not tag_desc_widget.isVisible()
            tag_desc_widget.setVisible(visible)
            toggle_btn.setText("标签说明 ▾" if visible else "标签说明 ▸")

        toggle_btn.clicked.connect(on_toggle)

        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(toggle_btn)
        main_layout.addWidget(tag_desc_widget)
        main_layout.addWidget(scroll)
        dialog.exec_()

    def show_rule_dialog(self):
        """显示游戏规则对话框"""
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

    def show_version_dialog(self):
        """显示版本信息对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("版本信息")
        dialog.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        
        # 创建文本显示区域
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: white;
                color: black;
                border: 1px solid #ccc;
                font-size: 22px;
                padding: 10px;
            }
        """)
        
        # 读取版本更新日志文件
        try:
            with open('版本更新日志.txt', 'r', encoding='utf-8') as f:
                content = f.read()
                text_edit.setText(content)
        except FileNotFoundError:
            text_edit.setText("版本更新日志文件未找到")
        except Exception as e:
            text_edit.setText(f"读取版本信息时出错: {str(e)}")
        
        layout.addWidget(text_edit)
        
        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def show_winner_and_exit(self, winner):
        """显示获胜者并退出游戏"""
        # 防止重复弹出对话框
        if hasattr(self, '_winner_dialog_shown') and self._winner_dialog_shown:
            return
        self._winner_dialog_shown = True
        
        dialog = QDialog(self)
        dialog.setWindowTitle("游戏结束")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # 显示获胜信息
        winner_label = QLabel(f"恭喜！{winner.mr_card.name} 获胜！")
        winner_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                text-align: center;
            }
        """)
        winner_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(winner_label)
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        review_btn = QPushButton("结算回顾")
        buttons_layout.addWidget(review_btn)
        buttons_layout.addWidget(ok_btn)

        # 绑定事件
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.clicked.connect(self._return_to_main_menu)
        review_btn.clicked.connect(lambda: self.show_post_game_review())
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def show_draw_and_exit(self, winners):
        """显示平局并退出游戏"""
        # 防止重复弹出对话框
        if hasattr(self, '_winner_dialog_shown') and self._winner_dialog_shown:
            return
        self._winner_dialog_shown = True
        
        dialog = QDialog(self)
        dialog.setWindowTitle("游戏结束")
        dialog.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        # 显示平局信息
        winner_names = [winner.mr_card.name for winner in winners]
        draw_label = QLabel(f"平局！\n获胜者: {', '.join(winner_names)}")
        draw_label.setStyleSheet("""
            QLabel {
                font-size: 20px;
                font-weight: bold;
                color: #2c3e50;
                text-align: center;
            }
        """)
        draw_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(draw_label)
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        review_btn = QPushButton("结算回顾")
        buttons_layout.addWidget(review_btn)
        buttons_layout.addWidget(ok_btn)

        # 绑定事件
        ok_btn.clicked.connect(dialog.accept)
        ok_btn.clicked.connect(self._return_to_main_menu)
        review_btn.clicked.connect(lambda: self.show_post_game_review())
        layout.addLayout(buttons_layout)

    def show_post_game_review(self):
        """显示游戏结束后的结算回顾界面"""
        if not hasattr(self, 'game') or not hasattr(self.game, 'stats'):
            self.show_message_box('提示', '无结算数据')
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('结算回顾')
        dialog.resize(760, 520)
        layout = QVBoxLayout(dialog)

        title = QLabel('傲视群雄')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('font-size: 28px; font-weight: 900; color: #d35400;')
        layout.addWidget(title)

        subtitle = QLabel('本局战绩一览')
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet('font-size: 16px; color: #7f8c8d;')
        layout.addWidget(subtitle)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(['玩家', '打出牌数', '摸牌数', '因你相邻玩家摸的牌', '发动技能次数'])
        table.setRowCount(len(self.game.player_list))
        table.verticalHeader().setVisible(False)
        table.setStyleSheet('QTableWidget { font-size: 16px; }')

        for row, p in enumerate(self.game.player_list):
            stats = self.game.stats.get(p, {
                'played_cards': 0,
                'drawn_cards': 0,
                'skills_used': 0,
                'caused_neighbor_draws': 0,
            })
            name = p.mr_card.name if p.mr_card else f'玩家{p.position+1}'
            values = [
                name,
                str(stats['played_cards']),
                str(stats['drawn_cards']),
                str(stats['caused_neighbor_draws']),
                str(stats['skills_used']),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() ^ Qt.ItemIsEditable)
                table.setItem(row, col, item)

        table.resizeColumnsToContents()
        layout.addWidget(table)

        # 底部按钮
        buttons = QHBoxLayout()
        close_btn = QPushButton('关闭')
        close_btn.clicked.connect(dialog.accept)
        buttons.addStretch()
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

        dialog.exec_()

    def on_cards_drawn(self, player, num_cards):
        """当玩家摸牌时更新界面"""
        # 更新摸牌堆数量显示
        self.update_draw_pile_count()
        
        # 更新玩家手牌显示
        self.update_player_hand_display(player)
        
        # 如果是当前玩家摸牌，刷新界面
        if player == self.game.get_current_player():
            self.show_game_round()

    def on_player_hand_changed(self, player):
        """当玩家手牌变化时更新界面"""
        # 更新玩家手牌显示
        self.update_player_hand_display(player)
        
        # 如果是当前玩家手牌变化，刷新界面
        if player == self.game.get_current_player():
            self.show_game_round()

    def on_draw_pile_changed(self):
        """当摸牌堆数量变化时更新界面"""
        self.update_draw_pile_count()

    #（重复定义已删除，保留前面的主实现）

    def on_game_state_changed(self):
        """当游戏状态变化时更新界面"""
        # 更新摸牌堆数量
        self.update_draw_pile_count()
        
        # 更新中央牌堆显示
        self.show_center_card_stack()
        
        # 更新信息区域
        self.render_info_area()
        
        # 如果是人类玩家回合，刷新操作按钮
        if self.game.is_current_player_human():
            self.show_game_round()

    def update_player_hand_display(self, player):
        """
        更新指定玩家的手牌数量显示
        """
        if player.position < len(self.player_widgets):
            player_widget = self.player_widgets[player.position]
            player_widget.update_info(player, is_current=(player.position == self.game.cur_location))

    def choose_color_dialog(self):
        """让玩家选择颜色的对话框"""
        colors = ['red', 'blue', 'green', 'yellow']
        color, ok = QInputDialog.getItem(self, "选择颜色", "请选择一种颜色:", colors, 0, False)
        if ok and color:
            return color
        return None

    def on_card_played(self, player, card):
        """当玩家出牌时更新界面"""
        # 更新中央牌堆显示
        self.show_center_card_stack()
        
        # 更新摸牌堆数量显示
        self.update_draw_pile_count()
        
        # 更新玩家手牌显示
        self.update_player_hand_display(player)
        
        # 如果是当前玩家出牌，刷新界面
        if player == self.game.get_current_player():
            self.show_game_round()

    def ask_yes_no_question(self, title, question):
        """弹出一个通用的"是/否"对话框"""
        # 重置选中的卡牌
        self.selected_card_idx = None
        
        reply = QMessageBox.question(self, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def keyPressEvent(self, event):
        """处理键盘事件"""
        if event.key() == Qt.Key_Escape:
            self.on_exit_game_key_pressed()
        else:
            super().keyPressEvent(event)

    def on_exit_game_clicked(self):
        """处理退出游戏按钮点击事件"""
        if self.ask_yes_no_question("退出游戏", "是否返回主界面？"):
            self.restart_to_main_menu()

    def on_exit_game_key_pressed(self):
        """处理Esc键退出游戏事件"""
        if self.ask_yes_no_question("退出游戏", "是否返回主界面？"):
            self.restart_to_main_menu()
    
    def _return_to_main_menu(self):
        """保持兼容的返回方法：改为彻底重启主界面。"""
        self.restart_to_main_menu()

    def restart_to_main_menu(self):
        """彻底销毁当前窗口并新建一个全新 MainWindow 显示主菜单。"""
        # 标记结束当前游戏
        try:
            if hasattr(self, 'game') and self.game:
                self.game.game_over = True
        except Exception:
            pass
        # 退出全屏
        try:
            if self.isFullScreen():
                self.showNormal()
        except Exception:
            pass
        # 关闭所有对话框
        self._force_close_all_dialogs()
        QApplication.processEvents()
        # 防止最后一个窗口关闭导致应用退出
        app = QApplication.instance()
        if app:
            try:
                app.setQuitOnLastWindowClosed(False)
            except Exception:
                pass
        # 使用单次定时回调在当前窗口关闭后创建新窗口，避免事件循环冲突
        def _create_new_window():
            try:
                new_window = MainWindow()
                if app:
                    try:
                        app._trino_main_window = new_window
                    except Exception:
                        pass
                new_window.show()
                try:
                    new_window.activateWindow()
                    new_window.raise_()
                except Exception:
                    pass
            except Exception:
                pass

        try:
            QTimer.singleShot(0, _create_new_window)
        except Exception:
            # 兜底：直接创建
            _create_new_window()

        # 关闭并释放当前窗口
        try:
            self.hide()
            self.close()
            self.deleteLater()
        except Exception:
            pass

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
        parent = self.parent()
        if parent and hasattr(parent, 'history_lines'):
            parent.history_lines.clear()
            # 同步清空 Game 内部历史（保持数据一致）
            if hasattr(parent, 'game') and parent.game and hasattr(parent.game, 'history_lines'):
                parent.game.history_lines.clear()
            # 刷新按钮计数
            if hasattr(parent, 'history_btn') and parent.history_btn:
                try:
                    parent.history_btn.setText('📜 历史 (0)')
                except RuntimeError:
                    pass

