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
        self.name_label = QLabel(f"<b>{player.mr_card.name}({player.position+1})</b>")
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
        
        # 历史记录按钮 (放在信息区下面)
        self.history_btn = QPushButton('📜 历史')
        self.history_btn.setFixedSize(150, 45)
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
        # 状态清理和跳过逻辑现在完全由 game.next_player() 处理
        
        # 注意：武圣状态不应该在这里重置，因为武圣激活后需要保持状态直到出牌或取消
        
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
            QTimer.singleShot(2000, self.game.execute_ai_turn)
        else:
            # 玩家回合
            if hasattr(self, 'ai_status_label'):
                self.ai_status_label.setVisible(False)

            # 回合开始时，检查手牌是否超限
            if len(player.uno_list) > player.hand_limit:
                # 手牌超限时，显示提示信息
                self.show_temporary_message(f"{player.mr_card.name} 手牌已达上限，不能再摸牌！", duration=3000)

            # 新增：检查玩家是否能出牌
            can_play = player.can_play_any_card()
            
            # 检查是否有加牌串待处理
            is_forced_draw_pending = draw_n > 0
            
            # 如果有加牌串，禁用出牌和技能按钮，只允许摸牌
            if is_forced_draw_pending:
                can_play = False
            
            # 由于现在出牌/摸牌/发动技能后会自动结束回合，结束回合按钮始终禁用
            self.render_action_area(is_forced_draw_pending=is_forced_draw_pending, can_play=can_play, end_enabled=False)

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

        # 技能按钮 - 在需要强制摸牌时禁用
        if active_skills:
            # 根据武圣状态设置按钮文本
            skill_btn_text = '取消武圣' if self.wusheng_active else '技能'
            self.skill_btn = QPushButton(skill_btn_text)
            btn_style = """
                QPushButton { font-size: 16px; font-weight: bold; color: white; background-color: #9b59b6; 
                              border: 2px solid #8e44ad; border-radius: 8px; padding: 8px 12px; min-height: 35px; }
                QPushButton:hover { background-color: #8e44ad; }
                QPushButton:disabled { background-color: #7f8c8d; border-color: #95a5a6; }
            """
            self.skill_btn.setStyleSheet(btn_style)
            self.skill_btn.clicked.connect(self.on_skill_button_clicked)
            # 在需要强制摸牌时禁用技能按钮
            self.skill_btn.setEnabled(not self.game.turn_action_taken and not is_forced_draw_pending)
            self.action_area_layout.addWidget(self.skill_btn)

        # 结束回合按钮
        self.end_btn = QPushButton('结束回合')
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
        # 检查是否武圣已激活，如果是则取消武圣状态
        if self.wusheng_active:
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
        
        if len(active_skills) == 1:
            # 如果只有一个主动技能，直接发动
            skill = active_skills[0]
            self.direct_activate_skill(skill)
            
            # 武圣技能不会自动结束回合，需要玩家选择牌
            if skill.name != '武圣':
                # 执行技能后，禁用所有行动按钮
                self.disable_action_buttons()
                # 自动结束回合
                self.game.next_player()
                self.show_game_round()
        elif len(active_skills) > 1:
            # 如果有多个主动技能，弹出选择对话框
            skill_names = [skill.name for skill in active_skills]
            skill_name, ok = QInputDialog.getItem(self, "选择技能", "请选择要发动的技能:", skill_names, 0, False)
            if ok and skill_name:
                selected_skill = next(skill for skill in active_skills if skill.name == skill_name)
                self.direct_activate_skill(selected_skill)
                
                # 武圣技能不会自动结束回合，需要玩家选择牌
                if selected_skill.name != '武圣':
                    # 执行技能后，禁用所有行动按钮
                    self.disable_action_buttons()
                    # 自动结束回合
                    self.game.next_player()
                    self.show_game_round()

    def direct_activate_skill(self, skill):
        """直接激活技能的最终执行逻辑"""
        player = self.game.player_list[self.game.cur_location]
        
        if skill.name == '反间':
            self.game.handle_skill_fanjian(player)
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
        player = self.game.player_list[self.game.cur_location]
        
        # 检查玩家是否有红色牌
        red_cards = [i for i, card in enumerate(player.uno_list) if card.color == 'red']
        
        if not red_cards:
            self.show_message_box("提示", "你没有红色牌，无法发动武圣技能。")
            return
        
        # 设置武圣状态为激活
        self.wusheng_active = True
        
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

        player = self.game.player_list[0]
        card = player.uno_list[self.selected_card_idx]
        
        # 检查武圣状态下的出牌
        if self.wusheng_active and card.color == 'red':
            # 武圣激活且选择了红色牌，执行武圣技能
            self.game.execute_skill_wusheng(player, self.selected_card_idx)
            # 重置武圣状态
            self.wusheng_active = False
        else:
            # 正常出牌
            self.game.handle_player_play(player, self.selected_card_idx, self.wusheng_active)
        
        # 执行出牌后，禁用所有行动按钮
        self.disable_action_buttons()
        # 自动结束回合
        self.game.next_player()
        self.show_game_round()

    def on_draw_card_clicked(self):
        player = self.game.player_list[0] # 假设人类玩家总是0号
        
        # 显示摸牌提示
        if self.game.draw_n > 0:
            self.show_temporary_message(f"{player.mr_card.name} 摸了 {self.game.draw_n} 张牌", duration=2000)
        else:
            self.show_temporary_message(f"{player.mr_card.name} 摸了 1 张牌", duration=2000)
        
        # 调用game.py中的核心逻辑
        self.game.handle_player_draw(player)
        # 执行摸牌后，禁用所有行动按钮
        self.disable_action_buttons()
        # 自动结束回合
        self.game.next_player()
        self.show_game_round()

    def on_end_turn_clicked(self):
        """处理结束回合按钮的点击"""
        self.game.next_player()
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