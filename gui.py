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
            self.font_size_hand = "16px"
        else: # 其他玩家，更紧凑
            self.layout = QVBoxLayout(self)
            self.layout.setContentsMargins(5, 5, 5, 5)
            self.hero_image_size = (100, 140)
            self.faction_image_size = (30, 30)
            self.font_size_name = "16px"
            self.font_size_hand = "14px"
            
        self.layout.setSpacing(5)

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
        self.name_label = QLabel(f"<b>{player.mr_card.name}</b>")
        self.hand_count_label = QLabel(f"手牌: {len(player.uno_list)}")
        
        self.name_label.setAlignment(Qt.AlignCenter)
        self.hand_count_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet(f"font-size: {self.font_size_name}; color: white; font-weight: bold; background: transparent;")
        self.hand_count_label.setStyleSheet(f"font-size: {self.font_size_hand}; color: white; background: transparent;")
        
        self.layout.addWidget(self.hero_image_container)

        if self.is_main_player:
            # 主玩家信息在右侧
            info_widget = QWidget()
            info_layout = QVBoxLayout(info_widget)
            info_layout.setContentsMargins(0,0,0,0)
            info_layout.setAlignment(Qt.AlignCenter)
            info_layout.addWidget(self.name_label)
            info_layout.addWidget(self.hand_count_label)
            info_layout.addStretch()
            self.layout.addWidget(info_widget)
        else: # 其他玩家信息在图片下方
            self.layout.addWidget(self.name_label)
            self.layout.addWidget(self.hand_count_label)

        # 调整组件大小策略，使其紧凑
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.update_style()

    def update_info(self, player, is_current):
        """更新信息"""
        self.player = player
        self.is_current = is_current
        self.hand_count_label.setText(f"手牌: {len(player.uno_list)}")
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
        self.main_window = parent
        self.mode = mode
        self.all_heroes = list(all_heroes.keys())
        
        self.setWindowTitle('选择你的武将')
        self.setStyleSheet("background-color: white;")
        self.setMinimumSize(300, 400)
        layout = QVBoxLayout(self)
        
        label = QLabel('请选择你的武将:')
        self.hero_list = QListWidget()
        for hero in self.all_heroes:
            self.hero_list.addItem(hero)
        
        start_button = QPushButton('开始游戏')
        start_button.clicked.connect(self.start_game_action)
        
        layout.addWidget(label)
        layout.addWidget(self.hero_list)
        layout.addWidget(start_button)

    def start_game_action(self):
        selected_items = self.hero_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '提示', '请选择一个武将！')
            return
        player_hero = selected_items[0].text()
        
        remaining_heroes = self.all_heroes[:]
        remaining_heroes.remove(player_hero)
        
        # 根据模式确定对手数量，这里暂时写死为2
        num_others = 2 
        if len(remaining_heroes) < num_others:
            # 如果不够，允许重复选择
            other_heros = random.choices(remaining_heroes, k=num_others)
        else:
            other_heros = random.sample(remaining_heroes, num_others)
            
        self.main_window.start_game(self.mode, player_hero, other_heros)
        self.accept()

class MainWindow(QWidget):
    def choose_fanjian_color_dialog(self):
        """为反间技能选择一个花色"""
        colors = ['red', 'blue', 'green', 'yellow']
        color_map = {'red': '红色', 'blue': '蓝色', 'green': '绿色', 'yellow': '黄色'}
        display_colors = list(color_map.values())
        chosen_display_color, ok = QInputDialog.getItem(self, "反间", "请为【反间】选择一个花色:", display_colors, 0, False)
        if ok and chosen_display_color:
            for en_color, zh_color in color_map.items():
                if zh_color == chosen_display_color:
                    return en_color
        return None
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Trino 游戏')
        self.setGeometry(100, 100, 1600, 900)
        self.setAutoFillBackground(True) # 允许窗口自动填充背景
        self.wusheng_active = False # 武圣技能状态
        # 弃牌模式状态
        self.is_in_discard_mode = False
        self.cards_to_discard_indices = set()
        self.num_to_discard = 0

        # 为所有对话框设置一个更明亮的全局样式
        QApplication.instance().setStyleSheet("""
            QDialog, QMessageBox, QInputDialog {
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

    def resizeEvent(self, event):
        """处理窗口大小改变事件，重新设置背景"""
        self._init_background()
        super().resizeEvent(event)

    def _init_background(self):
        """初始化并设置窗口背景图片"""
        palette = QPalette()
        pixmap = QPixmap(resource_path(os.path.join('images', 'background.jpg')))
        if not pixmap.isNull():
            # QBrush.NoBrush 表示不填充任何内容，这样背景图片才能显示
            # QPalette.WindowText 是前景色的角色，通常是文本颜色
            # QPalette.Window 是背景色的角色
            # QPalette.Base 是文本输入小部件的背景色
            # QPalette.AlternateBase 是视图中交替行的颜色
            # QPalette.ToolTipBase 是工具提示的背景色
            # QPalette.ToolTipText 是工具提示的文本颜色
            # QPalette.Text 是与 QPalette.Base 兼容的前景色
            # QPalette.Button 是按钮的背景色
            # QPalette.ButtonText 是按钮的前景色
            # QPalette.BrightText 是用于在深色背景上绘制文本的颜色，以使其突出
            # QPalette.Link 是超链接的颜色
            # QPalette.Highlight 是所选项目的背景色
            # QPalette.HighlightedText 是所选项目的前景色
            
            # 创建一个画刷，使用 pixmap 作为纹理
            # scaled() 方法可以调整图片大小以适应窗口，Qt.IgnoreAspectRatio 会拉伸图片填满窗口
            # Qt.KeepAspectRatio 会保持图片比例进行缩放
            # Qt.KeepAspectRatioByExpanding 会保持比例放大图片，直到完全覆盖窗口，可能会裁剪图片
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
            btn.setFixedSize(200, 50)
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
        info_layout = QVBoxLayout(self.info_area_widget)
        info_layout.setAlignment(Qt.AlignCenter)
        self.info_label = QLabel() # 之前是 color_label
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet('font-size:20px;color:white;background:rgba(44, 62, 80, 0.8);border:2px solid #99c;border-radius:10px;padding:10px;min-width:150px;')
        self.info_label.setWordWrap(True)
        info_layout.addWidget(self.info_label)
        self.grid_layout.addWidget(self.info_area_widget, 1, 4, alignment=Qt.AlignCenter)

        # 设置行和列的伸展系数
        self.grid_layout.setRowStretch(0, 2) # 顶部
        self.grid_layout.setRowStretch(1, 4) # 中部
        self.grid_layout.setRowStretch(2, 4) # 底部
        self.grid_layout.setColumnStretch(0, 1) # 牌堆
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 2) # 中心弃牌区
        self.grid_layout.setColumnStretch(3, 1)
        self.grid_layout.setColumnStretch(4, 1) # 信息区

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
        self.action_area_layout.setSpacing(15)
        self.action_area_layout.setAlignment(Qt.AlignCenter)
        
        self.my_skill_label = QLabel()
        self.my_skill_label.setWordWrap(True)
        self.my_skill_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.my_skill_label.setStyleSheet("""
            font-size: 15px; color: white; background: rgba(0,0,0,0.6); 
            border: 1px solid #99c; border-radius: 8px; padding: 8px; min-height: 100px;
        """)
        
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

    def start_game(self, mode, player_hero, other_heros):
        from game import Game
        
        num_players = len(other_heros) + 1
        self.game = Game(player_num=num_players, mode=mode)
        self.game.set_gui(self)

        # 1. 初始化玩家，这会填充 self.game.player_list
        self.game.initialize_players(player_hero_name=player_hero, ai_hero_names=other_heros)
        
        # 2. 现在 player_list 已经有数据，可以安全地设置UI了
        self.setup_game_ui() 
        
        # 3. 完成剩下的游戏设置（发牌、翻开第一张牌等）
        self.game.finalize_setup()
        
        # 4. 显示第一回合
        self.show_game_round(first_round=True)

    def get_cur_player_info(self):
        """获取当前玩家的相关信息"""
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        hand = player.uno_list
        draw_n = self.game.draw_n
        can_draw_chain = self.game.can_continue_draw_chain(player)
        return cur_idx, player, hand, draw_n, can_draw_chain

    def show_game_round(self, first_round=False):
        # --- 回合开始前的状态检查 ---
        if not first_round and self.game.skip:
            self.game.skip = False # 重置skip状态
            
            # 创建一个临时标签来显示跳过信息，而不是弹窗
            skip_label = QLabel(f"玩家 {self.game.player_list[self.game.cur_location].mr_card.name} 被禁，跳过！", self.game_widget)
            skip_label.setStyleSheet("font-size: 30px; color: #f1c40f; background-color: rgba(0, 0, 0, 0.7); border-radius: 15px; padding: 20px;")
            skip_label.setAlignment(Qt.AlignCenter)
            
            # 将其放置在游戏窗口的中央
            skip_label.adjustSize() # 调整大小以适应文本
            skip_label.move(self.game_widget.rect().center() - skip_label.rect().center())
            skip_label.show()
            skip_label.raise_()

            # 玩家被禁，延迟后进入下一位玩家的回合，并移除提示
            def next_turn_action():
                skip_label.deleteLater()
                self.game.next_player()
                self.show_game_round()

            QTimer.singleShot(1500, next_turn_action) # 显示1.5秒
            return

        # 状态清理仅在 game.next_player() 中进行，这里不再处理
        
        cur_idx, player, hand, draw_n, can_draw_chain = self.get_cur_player_info()
        human_player = self.game.player_list[0] # 总是获取人类玩家
        human_hand = human_player.uno_list # 总是获取人类玩家的手牌

        # 更新所有玩家信息栏
        for pos, widget in self.player_widgets.items():
            p = self.game.player_list[pos]
            is_main = (p.position == 0)
            widget.update_info(p, is_current=(pos == cur_idx))
            if is_main:
                widget.is_main_player = True # 确保主玩家的标志正确
                # 更新主玩家的技能描述
                skill_desc = p.mr_card.skill_description if p.mr_card else "无技能"
                self.my_skill_label.setText(f"<b>{p.mr_card.name} - 技能</b><br>{skill_desc}")

        # 渲染通用UI元素
        self.show_center_card_stack()
        self.render_info_area()
        self.update_draw_pile_count()
        self.selected_card_idx = None

        # 总是渲染人类玩家的手牌，但根据当前回合玩家决定是否可点击
        is_human_turn = not player.is_ai
        self.render_hand_area(human_hand, draw_n, can_draw_chain, enable_click=is_human_turn)

        if player.is_ai:
            # AI回合
            self.render_action_area(end_enabled=False) # 禁用所有操作按钮
            if hasattr(self, 'play_btn'): self.play_btn.setEnabled(False)
            if hasattr(self, 'draw_btn'): self.draw_btn.setEnabled(False)
            if hasattr(self, 'end_btn'): self.end_btn.setEnabled(False)
            
            # 增加一个状态标签，提示是AI的回合
            if not hasattr(self, 'ai_status_label'):
                self.ai_status_label = QLabel(f"AI ({player.mr_card.name}) 正在思考...")
                self.ai_status_label.setStyleSheet("font-size: 20px; color: yellow;")
                self.grid_layout.addWidget(self.ai_status_label, 1, 0, alignment=Qt.AlignCenter)
            self.ai_status_label.setText(f"AI ({player.mr_card.name}) 正在思考...")
            self.ai_status_label.setVisible(True)

            # 延迟后执行AI操作
            QTimer.singleShot(1500, self.game.execute_ai_turn)
        else:
            # 玩家回合
            if hasattr(self, 'ai_status_label'):
                self.ai_status_label.setVisible(False)

            # 回合开始时，检查手牌是否超限
            if len(player.uno_list) > player.hand_limit:
                num_to_discard = len(player.uno_list) - player.hand_limit
                self.enter_discard_mode(player, num_to_discard)
                return # 进入弃牌模式，不执行后续渲染

            # 新增：检查玩家是否能出牌
            can_play = player.can_play_any_card()
            self.render_action_area(draw_n=draw_n, can_draw_chain=can_draw_chain, end_enabled=self.game.turn_action_taken, can_play=can_play)

            # 必须响应加牌链的逻辑优先级更高
            if draw_n and not can_draw_chain:
                self.play_btn.setEnabled(False)
                self.draw_btn.setEnabled(True)
                self.end_btn.setEnabled(False)
                # 奸雄技能可能依然可用
                jianxiong_available = any(s.name == '奸雄' for s in player.mr_card.skills if s.is_active_in_turn)
                self.skill_btn.setEnabled(jianxiong_available)
                return

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

    def render_action_area(self, draw_n=0, can_draw_chain=False, end_enabled=False, can_play=True):
        """渲染操作按钮区域"""
        # 清空旧按钮
        while self.action_area_layout.count():
            item = self.action_area_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        # Clear old references to prevent accessing deleted widgets
        for attr in ['play_btn', 'draw_btn', 'end_btn', 'skill_btn', 'confirm_discard_btn']:
            if hasattr(self, attr):
                delattr(self, attr)

        if self.is_in_discard_mode:
            # 弃牌模式下的特殊UI
            discard_label = QLabel(f"手牌超限，请选择 {self.num_to_discard} 张牌弃置")
            discard_label.setStyleSheet("font-size: 16px; color: #f1c40f; font-weight: bold;")
            self.action_area_layout.addWidget(discard_label)

            self.confirm_discard_btn = QPushButton('确认弃牌')
            btn_style = """
                QPushButton { font-size: 18px; color: white; background-color: #27ae60; 
                              border: 2px solid #2ecc71; border-radius: 8px; padding: 10px; }
                QPushButton:hover { background-color: #2ecc71; }
                QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
            """
            self.confirm_discard_btn.setStyleSheet(btn_style)
            self.confirm_discard_btn.clicked.connect(self.on_confirm_discard_clicked)
            # Initially disabled until the correct number of cards are selected
            self.confirm_discard_btn.setEnabled(False)
            self.action_area_layout.addWidget(self.confirm_discard_btn)
            return

        cur_player = self.game.player_list[self.game.cur_location]
        
        active_skills = []
        if not cur_player.is_ai and cur_player.mr_card and cur_player.mr_card.skills:
            active_skills = [s for s in cur_player.mr_card.skills if s.is_active_in_turn]

        skill_button_text = " / ".join([s.name for s in active_skills]) if active_skills else "技能"

        self.play_btn = QPushButton('出牌')
        self.draw_btn = QPushButton('摸牌')
        self.end_btn = QPushButton('结束回合')
        self.skill_btn = QPushButton(skill_button_text)

        btn_style = """
            QPushButton { font-size: 18px; color: white; background-color: #c0392b; 
                          border: 2px solid #e74c3c; border-radius: 8px; padding: 10px; }
            QPushButton:hover { background-color: #e74c3c; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """
        for btn in [self.play_btn, self.draw_btn, self.end_btn]:
            btn.setStyleSheet(btn_style)
            self.action_area_layout.addWidget(btn)

        # 技能按钮用不同颜色
        self.skill_btn.setStyleSheet("""
            QPushButton { font-size: 18px; color: white; background-color: #8e44ad; 
                          border: 2px solid #9b59b6; border-radius: 8px; padding: 10px; }
            QPushButton:hover { background-color: #9b59b6; }
            QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
        """)
        self.action_area_layout.addWidget(self.skill_btn)

        self.play_btn.clicked.connect(self.on_play_card_clicked)
        self.draw_btn.clicked.connect(self.on_draw_card_clicked)
        self.end_btn.clicked.connect(self.on_end_turn_clicked)
        self.skill_btn.clicked.connect(self.on_skill_button_clicked)

        # 根据游戏状态设置按钮可用性
        action_taken = end_enabled # 直接使用传递的参数
        if action_taken: # 如果本回合已经行动过
            self.play_btn.setEnabled(False)
            self.draw_btn.setEnabled(False)
            self.skill_btn.setEnabled(False)
            self.end_btn.setEnabled(True)
        elif draw_n > 0 and not can_draw_chain: # 必须响应加牌链
            self.play_btn.setEnabled(False)
            self.draw_btn.setEnabled(True)
            self.end_btn.setEnabled(False)
            # 奸雄是响应技能，应该可用
            jianxiong_available = any(s.name == '奸雄' for s in active_skills)
            self.skill_btn.setEnabled(jianxiong_available)
        else: # 正常回合
            self.play_btn.setEnabled(can_play)
            self.draw_btn.setEnabled(not can_play) # 如果能出牌，则不能摸牌
            self.end_btn.setEnabled(False) # 回合开始时，结束按钮总是禁用的
            # 技能按钮的可用性独立于出牌/摸牌
            self.skill_btn.setEnabled(bool(active_skills))

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
        """处理技能按钮点击事件，优化单技能武将的体验"""
        player = self.game.player_list[self.game.cur_location]
        if not player.mr_card or not player.mr_card.skills:
            self.show_message_box("提示", "你没有技能。")
            return

        # 筛选出所有可以在回合内主动发动的技能
        active_skills = [s for s in player.mr_card.skills if s.is_active_in_turn]

        # 特殊处理武圣技能的切换逻辑
        wusheng_skill = next((s for s in active_skills if s.name == '武圣'), None)
        if wusheng_skill:
            # 如果点击技能按钮的意图是切换武圣状态
            self.wusheng_active = not self.wusheng_active
            self.render_hand_area(player.uno_list, self.game.draw_n, self.game.can_continue_draw_chain(player))
            # 如果是关闭武圣，并且没有其他主动技能，则操作结束
            if not self.wusheng_active and len(active_skills) == 1:
                return
            # 如果激活武圣后，没有其他技能可选，也直接结束
            if self.wusheng_active and len(active_skills) == 1:
                return

        # 移除武圣，因为它已经处理过了，我们只关心其他主动技能
        other_active_skills = [s for s in active_skills if s.name != '武圣']

        if len(other_active_skills) == 0:
            if not wusheng_skill: # 如果连武圣都没有，那就是真的没技能了
                self.show_message_box("提示", "当前没有可以主动发动的技能。")
            # 如果有武圣，但没有其他技能，此时武圣已经切换完毕，直接返回即可
            return
        
        elif len(other_active_skills) == 1:
            # 如果只有一个其他主动技能，直接发动
            self.direct_activate_skill(other_active_skills[0])
        
        else:
            # 如果有多个其他主动技能，创建对话框供选择
            dialog = QDialog(self)
            dialog.setWindowTitle("选择技能")
            dialog.setStyleSheet("background-color: white;")
            layout = QVBoxLayout(dialog)

            for skill in other_active_skills:
                btn = QPushButton(f"{skill.name}")
                btn.setToolTip(skill.description)
                # 注意：这里的lambda现在调用一个新的方法，不再需要传递dialog
                btn.clicked.connect(lambda _, s=skill, d=dialog: self.dialog_activate_skill(s, d))
                layout.addWidget(btn)
            
            dialog.exec_()

    def dialog_activate_skill(self, skill, dialog):
        """从对话框中选择并激活技能"""
        if dialog:
            dialog.accept()
        self.direct_activate_skill(skill)

    def direct_activate_skill(self, skill):
        """直接激活技能的最终执行逻辑"""
        player = self.game.player_list[self.game.cur_location]
        
        if skill.name == '反间':
            self.game.handle_skill_fanjian(player)
            # 反间技能有自己的UI流程和刷新，这里不需要再调用show_game_round
        else:
            self.show_message_box("提示", f"技能 [{skill.name}] 的界面交互尚未实现。")
            # 如果其他技能也需要刷新，可以在这里统一处理
            self.show_game_round()

    def activate_skill(self, skill, dialog):
        """激活所选技能"""
        dialog.accept() # 关闭技能选择对话框
        player = self.game.player_list[self.game.cur_location]
        
        # --- 这里需要根据不同技能实现不同的逻辑 ---
        if skill.name == '反间':
            self.game.handle_skill_fanjian(player)
            # 动作结束后，由GUI强制刷新一次以更新按钮状态
            self.show_game_round()
        else:
            self.show_message_box("提示", f"技能 [{skill.name}] 的界面交互尚未实现。")

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

    def update_draw_pile_count(self):
        """更新牌堆数量标签"""
        count = len(self.game.unocard_pack)
        self.draw_pile_count.setText(f"{count}")

    def render_info_area(self):
        """更新右侧信息区的文本，使其更清晰"""
        color = self.game.cur_color
        color_map = {'red': '红色', 'blue': '蓝色', 'green': '绿色', 'yellow': '黄色'}
        color_text = f"当前颜色: <b>{color_map.get(color, '无')}</b>"

        direction_text = f"游戏方向: {'顺序' if self.game.dir == 1 else '逆序'}"

        last_card = self.game.playedcards.get_one()
        card_info_text = "上一张牌: 无"
        if last_card:
            card_display_str = ""
            # 使用更详细的卡牌描述
            if last_card.type == 'number':
                card_display_str = f"{color_map.get(last_card.color, '')} <b>{last_card.value}</b>"
            elif last_card.type in ['wild', 'wild_draw4']:
                type_map = {'wild': '万能牌', 'wild_draw4': '王牌+4'}
                card_display_str = f"<b>{type_map.get(last_card.type)}</b>"
            else:
                type_map = {'draw2': '+2', 'reverse': '反转', 'skip': '跳过'}
                card_display_str = f"{color_map.get(last_card.color, '')} <b>{type_map.get(last_card.type, '')}</b>"
            
            card_info_text = f"上一张牌: {card_display_str}"

        # 使用HTML换行<br>以获得更好的控制
        self.info_label.setText(
            f"回合: {self.game.turn_count}<br><br>"
            f"{color_text}<br>"
            f"{direction_text}<br>"
            f"{card_info_text}"
        )

    def show_temporary_message(self, message, duration=1500):
        """在屏幕中央显示一个临时的、带样式的消息"""
        if not self.game_widget:
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

    def choose_color_dialog(self):
        """让玩家选择颜色的对话框"""
        colors = ['red', 'blue', 'green', 'yellow']
        color, ok = QInputDialog.getItem(self, "选择颜色", "请选择一种颜色:", colors, 0, False)
        if ok and color:
            return color
        return None
    
    def on_play_card_clicked(self):
        if self.selected_card_idx is None:
            self.show_message_box('提示', '请先选择一张牌！')
            return

        player = self.game.player_list[0] # 假设人类玩家总是0号
        
        # 调用 game.py 中的核心逻辑
        self.game.handle_human_play(player, self.selected_card_idx, self.wusheng_active)
        # 动作结束后，由GUI强制刷新一次以更新按钮状态
        self.show_game_round()

    def on_draw_card_clicked(self):
        player = self.game.player_list[0] # 假设人类玩家总是0号
        # 调用game.py中的核心逻辑
        self.game.handle_human_draw(player)
        # 动作结束后，由GUI强制刷新一次以更新按钮状态
        self.show_game_round()

    def on_end_turn_clicked(self):
        # 结束回合按钮：先处理跳牌，再切换到下一玩家
        if self.game.handle_jump_logic():
            # 如果发生了跳牌，handle_jump_logic 内部已经处理了后续流程
            # 并且 show_game_round 也会被调用，所以这里直接返回
            self.show_game_round()
            return

        self.game.next_player()
        self.show_game_round()

    def on_confirm_discard_clicked(self):
        """处理确认弃牌按钮的点击事件"""
        if not self.is_in_discard_mode:
            return
        
        player = self.game.player_in_discard
        if not player or len(self.cards_to_discard_indices) != self.num_to_discard:
            return

        # 获取要弃置的卡牌对象
        # 注意：这里必须从 player.uno_list 获取，因为 self.card_buttons 可能属于其他玩家
        cards_to_discard = [player.uno_list[i] for i in sorted(list(self.cards_to_discard_indices), reverse=True)]
        
        # 调用game中的核心逻辑
        self.game.player_confirms_discard(player, cards_to_discard)
        
        # 确认弃牌后，由GUI自己手动退出弃牌模式并刷新界面，避免循环调用
        self.exit_discard_mode()

    def enter_discard_mode(self, player, num_to_discard):
        """
        进入弃牌模式。
        新逻辑：不再接收 cards_to_draw，因为牌已经直接在玩家手上了。
        """
        self.is_in_discard_mode = True
        # game.py中已经设置了 self.game.player_in_discard
        self.num_to_discard = num_to_discard
        self.cards_to_discard_indices.clear()
        
        # 重新渲染UI以反映弃牌模式
        self.render_action_area()
        # 渲染玩家当前的所有手牌
        self.render_hand_area(player.uno_list, 0, False, enable_click=True)
        
        # 移除弹窗，改为在界面上提示
        # message = f"你的手牌已超过上限！\n请选择 {num_to_discard} 张手牌弃置。"
        # self.show_message_box("手牌超限", message)

    def exit_discard_mode(self):
        """退出弃牌模式"""
        self.is_in_discard_mode = False
        self.num_to_discard = 0
        self.cards_to_discard_indices.clear()
        self.game.player_in_discard = None
        # 退出弃牌模式后，应该刷新一下主游戏界面
        self.show_game_round()

    def ask_yes_no_question(self, title, question):
        """弹出一个通用的“是/否”对话框"""
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
        for i, btn in enumerate(self.card_buttons):
            # 在弃牌模式下，高亮逻辑由 on_card_clicked 直接处理
            if self.is_in_discard_mode:
                if i in self.cards_to_discard_indices:
                    btn.setStyleSheet("border: 4px solid #e74c3c; border-radius: 5px;")
                else:
                    btn.setStyleSheet("border: none;")
            else: # 正常模式
                if i == idx:
                    btn.setStyleSheet("border: 3px solid #f1c40f; border-radius: 5px;")
                else:
                    btn.setStyleSheet("border: none;")
        if not self.is_in_discard_mode:
            self.selected_card_idx = idx

    def on_card_clicked(self, idx):
        if self.is_in_discard_mode:
            if idx in self.cards_to_discard_indices:
                self.cards_to_discard_indices.remove(idx)
            else:
                if len(self.cards_to_discard_indices) < self.num_to_discard:
                    self.cards_to_discard_indices.add(idx)
            
            # 更新高亮
            self.highlight_selected_card(None) # 调用高亮函数刷新所有卡牌状态
            
            # 更新确认按钮状态
            if hasattr(self, 'confirm_discard_btn'):
                self.confirm_discard_btn.setEnabled(len(self.cards_to_discard_indices) == self.num_to_discard)
            return

        self.highlight_selected_card(idx)
        
        cur_player_idx = self.game.cur_location
        player = self.game.player_list[cur_player_idx]
        if player.is_ai:
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
            info_layout.addStretch() # 将内容推到顶部

            hero_layout.addWidget(info_widget, stretch=1)
            grid_layout.addWidget(hero_box, row, col)

        scroll.setWidget(content_widget)
        
        main_layout = QVBoxLayout(dialog)
        main_layout.addWidget(scroll)
        dialog.exec_()

    def show_rule_dialog(self):
        rule_text = (
            "1. 你的回合内，若被强制加牌或选择摸牌，则不可以发动技能或出牌；\n"
            "2. 仅剩余1张牌时，须喊“UNO”，否则若被抓需要摸1张牌；\n"
            "3. 仅剩余1张牌时回合内的主动技能失效；\n"
            "4. 黑色牌不能当作最后一张牌打出，否则需再摸1张牌；\n"
            "5. [+2]可以叠[+2]，[+2]可以叠[+4]，[+4]可以叠[+4]，[+4]不可以叠[+2]；\n"
            "6. 手牌数上限通常为20张，达到上限后剩余加牌不再生效；\n"
            "7. 跳牌：颜色和牌面完全相同时可以跳过其余玩家回合抢先打出该牌；黑色牌不能跳牌；\n"
            "8. 跳牌时功能牌只生效后1张，且跳牌优先级大于[禁止]，即：加牌串被跳牌后只生效最后1张[+2]；由1号玩家打出[禁止]后若2号玩家有相同颜色的[禁止]可进行跳牌，然后跳过3号玩家的回合；\n"
            "9. 通过技能发动的跳牌优先级低于未发动技能的跳牌；相同优先级的跳牌按照游戏内出牌顺序执行；\n"
            "10. 拼点：[禁止]/[转向]/[+2]点数视为0，[黑色]点数视为10；拼点结束后，点数小的人获得双方的拼点牌，若点数相同则各自收回；“UNO”的人不能被拼点。"
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