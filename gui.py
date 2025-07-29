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
from PyQt5.QtGui import QIcon, QPixmap

def get_card_image_path(card):
    """全局函数，用于获取卡牌图片路径"""
    color = card.color
    type_ = card.type
    value = card.value
    base = os.path.join('images', 'uno_images')
    if hasattr(sys, '_MEIPASS'):
        base = os.path.join(sys._MEIPASS, 'images', 'uno_images')
    
    if type_ == 'number':
        return os.path.join(base, f'{color}_{value}.png')
    elif type_ == 'draw2':
        return os.path.join(base, f'{color}_+2.png')
    elif type_ == 'reverse':
        return os.path.join(base, f'{color}_reverse.png')
    elif type_ == 'skip':
        return os.path.join(base, f'{color}_skip.png')
    elif type_ == 'wild':
        return os.path.join(base, 'black_wildcard.png')
    elif type_ == 'wild_draw4':
        return os.path.join(base, 'black_+4.png')
    else:
        return os.path.join(base, 'back.png')

def get_faction_image_path(team):
    """获取势力图片的路径"""
    base = 'images'
    if hasattr(sys, '_MEIPASS'):
        base = os.path.join(sys._MEIPASS, 'images')
    
    path = os.path.join(base, f'{team}.png')
    # 检查文件是否存在，如果不存在，可以返回一个None或者默认图片路径
    if os.path.exists(path):
        return path
    return None

class PlayerInfoWidget(QWidget):
    """用于显示单个玩家信息的组件，模仿三国杀武将栏"""
    def __init__(self, player, is_current=False, parent=None):
        super().__init__(parent)
        self.player = player
        self.is_current = is_current
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(5)

        # --- 武将及势力图片区域 ---
        self.hero_image_container = QWidget()
        # 使用 QGridLayout 来允许小部件重叠
        hero_image_layout = QGridLayout(self.hero_image_container)
        hero_image_layout.setContentsMargins(0, 0, 0, 0)

        # 武将图片
        self.hero_image_label = QLabel()
        if player.mr_card and player.mr_card.image_path:
            pixmap = QPixmap(os.path.join('images', player.mr_card.image_path))
            self.hero_image_label.setPixmap(pixmap.scaled(120, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.hero_image_label.setAlignment(Qt.AlignCenter)
        hero_image_layout.addWidget(self.hero_image_label, 0, 0, Qt.AlignCenter)

        # 势力图片
        self.faction_image_label = QLabel()
        faction_path = get_faction_image_path(player.team)
        if faction_path:
            pixmap = QPixmap(faction_path)
            self.faction_image_label.setPixmap(pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.faction_image_label.setFixedSize(40, 40)
            # 将势力图片放在左上角
            hero_image_layout.addWidget(self.faction_image_label, 0, 0, Qt.AlignTop | Qt.AlignLeft)
            self.faction_image_label.setContentsMargins(0, 2, 0, 0) # 稍微留一点边距

        # 玩家信息
        self.name_label = QLabel(f"玩家{player.position + 1} ({player.mr_card.name})")
        self.hand_count_label = QLabel(f"手牌: {len(player.uno_list)}")

        for label in [self.name_label, self.hand_count_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 16px; color: white;")

        self.layout.addWidget(self.hero_image_container)
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.hand_count_label)

        self.update_style()

    def update_info(self, player, is_current):
        """更新信息"""
        self.player = player
        self.is_current = is_current
        self.hand_count_label.setText(f"手牌: {len(player.uno_list)}")
        self.update_style()

    def update_style(self):
        """根据是否为当前玩家更新样式"""
        if self.is_current:
            self.setStyleSheet("background-color: #8B0000; border: 3px solid #FFD700; border-radius: 10px;")
        else:
            self.setStyleSheet("background-color: #2c3e50; border: 2px solid #34495e; border-radius: 10px;")

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
        self.setWindowTitle('Trino 游戏')
        self.setGeometry(100, 100, 1600, 900)
        self.setStyleSheet("background-color: #34495e;")

        # 为所有对话框设置一个更明亮的全局样式
        QApplication.instance().setStyleSheet("""
            QDialog, QMessageBox, QInputDialog {
                background-color: #f0f0f0;
                color: black;
            }
            QDialog QLabel, QMessageBox QLabel, QInputDialog QLabel {
                color: black;
            }
            QDialog QPushButton, QMessageBox QPushButton, QInputDialog QPushButton {
                background-color: #e1e1e1;
                border: 1px solid #adadad;
                padding: 5px;
                min-width: 60px;
                border-radius: 3px;
                color: black;
            }
            QDialog QPushButton:hover, QMessageBox QPushButton:hover, QInputDialog QPushButton:hover {
                background-color: #cacaca;
            }
            QListWidget, QComboBox, QLineEdit {
                background-color: white;
                color: black;
            }
        """)

        self.main_layout = QVBoxLayout(self) # 先用QVBoxLayout容纳初始菜单
        self.game_widget = None # 游戏界面的主容器
        self.player_widgets = {}

        self.show_main_menu()

    def show_main_menu(self):
        """显示主菜单"""
        self.clear_window()
        
        menu_widget = QWidget()
        menu_layout = QVBoxLayout(menu_widget)
        menu_layout.setAlignment(Qt.AlignCenter)
        menu_layout.setSpacing(20)

        self.start_btn = QPushButton('开始游戏')
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
        """创建并设置游戏界面的布局，模仿三国杀"""
        self.clear_window()

        self.game_widget = QWidget()
        self.grid_layout = QGridLayout(self.game_widget)
        self.main_layout.addWidget(self.game_widget)

        # --- 布局划分 ---
        # (row, col, rowspan, colspan)
        # 顶部对手区域
        self.top_area = QHBoxLayout()
        self.grid_layout.addLayout(self.top_area, 0, 0, 1, 3)
        self.grid_layout.setRowStretch(0, 2) # 顶部占2份

        # 中间出牌区
        self.center_card_widget = QWidget()
        self.center_card_layout = QHBoxLayout(self.center_card_widget)
        self.center_card_layout.setAlignment(Qt.AlignCenter)
        self.grid_layout.addWidget(self.center_card_widget, 1, 1, 1, 1)
        self.grid_layout.setRowStretch(1, 3) # 中部占3份

        # 底部玩家区域
        self.bottom_area = QGridLayout()
        self.grid_layout.addLayout(self.bottom_area, 2, 0, 1, 3)
        self.grid_layout.setRowStretch(2, 4) # 底部占4份

        # --- 填充内容 ---
        # 玩家信息组件
        main_player_pos = 0 # 假设玩家总是0号位
        other_players = [p for p in self.game.player_list if p.position != main_player_pos]
        
        # 对手放顶部
        for p in other_players:
            player_widget = PlayerInfoWidget(p)
            self.player_widgets[p.position] = player_widget
            self.top_area.addWidget(player_widget, alignment=Qt.AlignCenter)

        # 玩家放底部左侧
        main_player = self.game.player_list[main_player_pos]
        main_player_widget = PlayerInfoWidget(main_player)
        self.player_widgets[main_player_pos] = main_player_widget
        self.bottom_area.addWidget(main_player_widget, 0, 0, 2, 1) # (row, col, rowspan, colspan)

        # 手牌区放底部中间
        self.card_area = QWidget()
        self.card_area_layout = QHBoxLayout(self.card_area)
        self.card_area_layout.setSpacing(10)
        self.card_area_layout.setAlignment(Qt.AlignCenter)
        self.bottom_area.addWidget(self.card_area, 0, 1, 2, 1)
        self.bottom_area.setColumnStretch(1, 5) # 手牌区占大头

        # 操作区放底部右侧
        self.action_area = QWidget()
        self.action_area_layout = QVBoxLayout(self.action_area)
        self.action_area_layout.setSpacing(15)
        self.action_area_layout.setAlignment(Qt.AlignCenter)
        self.bottom_area.addWidget(self.action_area, 0, 2)
        
        # 颜色标签
        self.color_label = QLabel()
        self.color_label.setAlignment(Qt.AlignCenter)
        self.color_label.setStyleSheet('font-size:24px;color:white;background:#2c3e50;border:2px solid #99c;border-radius:10px;min-width:120px;min-height:40px;')
        self.grid_layout.addWidget(self.color_label, 1, 2, alignment=Qt.AlignTop | Qt.AlignRight)

    def start_game(self, mode, player_hero, other_heros):
        from game import Game
        from player import Player
        from mr_cards import all_heroes
        
        num_players = 3
        self.game = Game(player_num=num_players, mode=mode)
        self.game.set_gui(self)

        player_list = []
        # 创建人类玩家
        player_mr_card = all_heroes.get(player_hero)
        p1 = Player(position=0, is_ai=False, team=player_mr_card.team)
        p1.mr_card = player_mr_card
        player_list.append(p1)

        # 创建AI玩家
        for i, hero_name in enumerate(other_heros):
            other_mr_card = all_heroes.get(hero_name)
            p = Player(position=i + 1, is_ai=True, team=other_mr_card.team)
            p.mr_card = other_mr_card
            player_list.append(p)

        for p in player_list:
            self.game.add_player(p)

        self.game.game_start()
        
        self.setup_game_ui() # 创建新的游戏UI
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
        self.game.clear_state()
        
        cur_idx, player, hand, draw_n, can_draw_chain = self.get_cur_player_info()
        human_player = self.game.player_list[0] # 总是获取人类玩家
        human_hand = human_player.uno_list # 总是获取人类玩家的手牌

        # 更新所有玩家信息栏
        for pos, widget in self.player_widgets.items():
            p = self.game.player_list[pos]
            widget.update_info(p, is_current=(pos == cur_idx))

        # 渲染通用UI元素
        self.show_center_card()
        self.render_color_label()
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

            self.render_action_area(draw_n=draw_n, can_draw_chain=can_draw_chain, end_enabled=False)

            if self.game.skip:
                QMessageBox.information(self, '禁牌', '你已被禁牌，跳过本回合！')
                self.play_btn.setEnabled(False)
                self.draw_btn.setEnabled(False)
                self.end_btn.setEnabled(True)
                return

            if draw_n and not can_draw_chain:
                self.play_btn.setEnabled(False)
                self.draw_btn.setEnabled(True)
                self.end_btn.setEnabled(False)
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
            icon = QIcon(get_card_image_path(card))
            card_button.setIcon(icon)
            card_button.setIconSize(QSize(75, 110))
            card_button.setStyleSheet("background-color: transparent; border: none;")
            if enable_click:
                card_button.clicked.connect(lambda _, idx=i: self.on_card_clicked(idx))
            self.card_buttons.append(card_button)
            self.card_area_layout.addWidget(card_button)

    def render_action_area(self, draw_n=0, can_draw_chain=False, end_enabled=False):
        """渲染操作按钮区域"""
        # 清空旧按钮
        while self.action_area_layout.count():
            item = self.action_area_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
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
        if draw_n > 0 and not can_draw_chain: # 必须摸牌
            self.play_btn.setEnabled(False)
            self.draw_btn.setEnabled(True)
            self.end_btn.setEnabled(False)
            self.skill_btn.setEnabled(False)
        else:
            self.play_btn.setEnabled(True)
            self.draw_btn.setEnabled(True)
            self.end_btn.setEnabled(end_enabled)
            self.skill_btn.setEnabled(bool(active_skills))

    def show_center_card(self):
        """显示中央出牌区的牌"""
        # 清空
        while self.center_card_layout.count():
            item = self.center_card_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        
        last_card = self.game.playedcards.get_one()
        if last_card:
            card_label = QLabel()
            pixmap = QPixmap(get_card_image_path(last_card)).scaled(150, 225, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            card_label.setPixmap(pixmap)
            self.center_card_layout.addWidget(card_label)

    def on_skill_button_clicked(self):
        """处理技能按钮点击事件"""
        player = self.game.player_list[self.game.cur_location]
        if not player.mr_card or not player.mr_card.skills:
            QMessageBox.information(self, "提示", "你没有技能。")
            return

        # 创建一个对话框来显示所有可用技能
        dialog = QDialog(self)
        dialog.setWindowTitle("选择技能")
        layout = QVBoxLayout(dialog)

        skill_buttons = []
        for skill in player.mr_card.skills:
            # 只显示可以在回合内主动发动的技能
            if skill.is_active_in_turn:
                btn = QPushButton(f"{skill.name}")
                btn.setToolTip(skill.description)  # 将描述作为工具提示
                btn.clicked.connect(lambda _, s=skill, d=dialog: self.activate_skill(s, d))
                layout.addWidget(btn)
                skill_buttons.append(btn)

        if not skill_buttons:
            QMessageBox.information(self, "提示", "当前没有可以主动发动的技能。")
            return
            
        dialog.exec_()

    def activate_skill(self, skill, dialog):
        """激活所选技能"""
        dialog.accept() # 关闭技能选择对话框
        player = self.game.player_list[self.game.cur_location]
        
        # --- 这里需要根据不同技能实现不同的逻辑 ---
        if skill.name == '武圣':
            # 1. 选择要使用的红色牌
            red_cards = [card for card in player.uno_list if card.color == 'red']
            if not red_cards:
                QMessageBox.warning(self, "技能发动失败", "你没有红色的牌可以发动【武圣】！")
                return
            
            card_to_use = self.choose_specific_card_dialog(player, red_cards, "选择一张红色牌发动【武圣】")
            if not card_to_use: return

            # 2. 检查打出虚拟的+2是否合法
            from card import UnoCard
            wusheng_card = UnoCard('draw2', 'red', 0)
            if not player.check_card(wusheng_card):
                QMessageBox.warning(self, '出牌无效', '当前无法打出【红+2】！')
                return

            # 3. 执行技能
            card_idx = player.uno_list.index(card_to_use)
            self.game.execute_skill_wusheng(player, card_idx)

            # 4. 检查胜利并进入下一回合
            if len(player.uno_list) == 0:
                self.show_winner_and_exit(player)
            else:
                self.game.next_player()
                self.show_game_round()

        elif skill.name == '反间':
            # 1. 选择目标玩家
            target = self.choose_target_player_dialog(exclude_self=True)
            if not target: return

            # 2. 选择要给出的牌
            card_to_give = self.choose_card_from_hand_dialog(player, "选择一张非黑色的牌交给对方")
            if not card_to_give or card_to_give.type in ['wild', 'wild_draw4']:
                QMessageBox.warning(self, "技能发动失败", "必须选择一张非黑色的手牌！")
                return
            
            # 3. 执行技能效果
            self.game.execute_skill(skill, player, target, card_to_give)
            
            # 4. 刷新界面
            self.show_game_round()
        else:
            QMessageBox.information(self, "提示", f"技能 [{skill.name}] 的界面交互尚未实现。")

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

    def render_color_label(self):
        """更新当前颜色指示器"""
        color = self.game.cur_color
        if color:
            color_map = {'red': '红色', 'blue': '蓝色', 'green': '绿色', 'yellow': '黄色'}
            self.color_label.setText(f"当前颜色: {color_map.get(color, '无')}")

    def on_play_card_clicked(self):
        """处理出牌按钮点击事件"""
        if self.selected_card_idx is None:
            QMessageBox.warning(self, '提示', '请先选择一张手牌！')
            return

        cur_idx, player, _, _, _ = self.get_cur_player_info()
        # 检查索引是否有效，防止列表变化导致错误
        if self.selected_card_idx >= len(player.uno_list):
            self.selected_card_idx = None
            QMessageBox.warning(self, '提示', '手牌已变化，请重新选择！')
            self.show_game_round()
            return
            
        card_to_play = player.uno_list[self.selected_card_idx]
        # --- 常规出牌流程 ---
        if not player.check_card(card_to_play):
            QMessageBox.warning(self, '出牌无效', '这张牌不符合出牌规则！')
            return

        # UNO 叫牌逻辑
        if len(player.uno_list) == 2:
            reply = QMessageBox.question(self, 'UNO', '你只剩一张牌了，要喊“UNO”吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.No:
                QMessageBox.information(self, '提示', '你因未喊UNO，被罚摸一张牌！')
                player.get_card(1)
                # 罚牌后需要刷新手牌显示，但不结束回合
                self.show_game_round() 
                return

        # 最后一张不能是黑牌
        if len(player.uno_list) == 1 and card_to_play.type in ['wild', 'wild_draw4']:
            QMessageBox.warning(self, '规则错误', '最后一张牌不能是万能牌或+4牌！你被罚摸一张牌。')
            player.get_card(1)
            self.game.next_player()
            self.show_game_round()
            return

        # 执行出牌
        color_choice = None
        card_type_before_play = card_to_play.type
        
        if card_type_before_play in ['wild', 'wild_draw4']:
            color_choice = self.choose_color_dialog()
            if not color_choice:
                return  # 用户取消选择

        player.play_a_hand(self.selected_card_idx, color_choice=color_choice)
        self.game.change_flag()

        # --- 出牌后技能处理（集智） ---
        has_jizhi = player.mr_card and any(skill.__class__.__name__ == 'JiZhi' for skill in player.mr_card.skills)
        if has_jizhi and card_type_before_play in ['draw2', 'wild_draw4', 'wild']:
            if self.ask_yes_no_question("发动技能", "是否发动【集智】弃置一张牌？"):
                card_to_discard = self.choose_card_from_hand_dialog(player, "请选择要弃置的牌")
                if card_to_discard:
                    # 找到这张牌的索引并弃掉
                    for i, c in enumerate(player.uno_list):
                        if c is card_to_discard:
                            player.fold_card([i])
                            QMessageBox.information(self, "提示", "【集智】发动成功！")
                            break
        
        # --- 回合结束 ---
        if len(player.uno_list) == 0:
            self.show_winner_and_exit(player)
            return

        self.game.next_player()
        self.show_game_round()

    def on_draw_card_clicked(self):
        """处理摸牌按钮点击事件"""
        cur_idx, player, _, draw_n, _ = self.get_cur_player_info()
        
        if draw_n > 0:
            player.get_card(draw_n)
            self.game.draw_n = 0
        else:
            player.get_card(1)

        # 摸牌后，通常回合就结束了
        self.game.next_player()
        self.show_game_round()

    def show_winner_and_exit(self, winner):
        """显示胜利者并返回主菜单"""
        QMessageBox.information(self, '游戏结束', f'玩家 {winner.position + 1} ({winner.mr_card.name}) 获胜！')
        self.show_main_menu()

    def choose_color_dialog(self):
        """弹窗让玩家选择颜色"""
        colors = ['red', 'blue', 'green', 'yellow']
        color, ok = QInputDialog.getItem(self, "选择颜色", "请选择一个颜色:", colors, 0, False)
        if ok and color:
            return color
        return None
    def on_end_turn_clicked(self):
        # 结束回合按钮：切换到下一玩家并刷新界面
        self.game.next_player()
        self.show_game_round()

    def ask_yes_no_question(self, title, question):
        """弹出一个通用的“是/否”对话框"""
        reply = QMessageBox.question(self, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        return reply == QMessageBox.Yes

    def ask_for_card_choice(self, title, message, cards):
        """弹出一个对话框让玩家从给定的卡牌中选择一张"""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout()
        
        label = QLabel(message)
        layout.addWidget(label)
        
        list_widget = QListWidget()
        for card in cards:
            item = QListWidgetItem(card.content) # Assuming card has a 'content' attribute
            list_widget.addItem(item)
        layout.addWidget(list_widget)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted and list_widget.currentItem():
            selected_index = list_widget.currentRow()
            return cards[selected_index]
        return None

    def highlight_selected_card(self, idx):
        # 高亮选中卡牌，取消其他卡牌高亮
        for i, btn in enumerate(self.card_buttons):
            if i == idx:
                # A more distinct highlight for the new theme
                btn.setStyleSheet('font-size:24px;background:#fffdc0;border:4px solid #f90;border-radius:16px;')
            else:
                # Reset to default style
                btn.setStyleSheet('font-size:24px;background:#fff;border:3px solid #333;border-radius:16px;')
        self.selected_card_idx = idx

    def on_card_clicked(self, idx):
        # 点击卡牌时，只高亮它
        self.highlight_selected_card(idx)

    def show_mode_dialog(self):
        dialog = ModeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            mode = dialog.selected_mode
            self.show_select_hero(mode)

    def show_select_hero(self, mode):
        select_dialog = SelectHeroDialog(mode, self)
        select_dialog.exec_()

    def get_player_card_index(self, player):
        # 弹窗让玩家选择出牌序号
        hand = '\n'.join([f'{i}: {str(card)}' for i, card in enumerate(player.uno_list)])
        idx, ok = QInputDialog.getInt(self, '出牌', f'你的手牌：\n{hand}\n请输入你要出的牌序号：', 0, 0, len(player.uno_list)-1, 1)
        return idx, ok

    def show_hero_dialog(self):
        from PyQt5.QtWidgets import QScrollArea, QTextEdit, QLabel, QVBoxLayout, QHBoxLayout, QDialog, QWidget
        from PyQt5.QtGui import QPixmap
        hero_infos = [
            # (武将名, 技能, 图片文件名)
            ('曹操', '奸雄 若场上打出的[+2]/[+4]牌对你生效且不由你打出，你可选择获得之。', 'caocao.jpg'),
            ('甄姬', '倾国 你的[蓝色]可以当作任意颜色打出，牌面不变。', 'zhenji.jpg'),
            ('郭嘉', '遗计 当你被加牌时，你可以观看牌堆顶的2张牌，将这些牌交给任意玩家。', 'guojia.jpg'),
            ('许褚', '裸衣 你亮出牌堆顶的3张牌，将其中所有[+2]/[+4]无视颜色打出，且摸牌数翻倍；若其中没有[+2]/[+4]，你获得这3张牌。', 'xuchu.jpg'),
            ('刘备', '仁德 你指定一名其他玩家令其交给你2张牌并视为打出1张虚拟的[换色]。', 'liubei.jpg'),
            ('刘禅', '放权 你摸1张牌后指定一名玩家代替你完成此回合。', 'liushan.jpg'),
            ('关羽', '武圣 你的[红色]可以当作[红+2]打出。', 'guanyu.jpg'),
            ('张飞', '咆哮 你可以将所有能连出的牌在一个回合内打出，[禁止]/[+2]只能作为结尾打出。', 'zhangfei.jpg'),
            ('赵云', '龙胆 你可以将[红色]当作[蓝色]打出，将[蓝色]当作[红色]打出，牌面不变。', 'zhaoyun.jpg'),
            ('诸葛亮', '观星 在你手牌数目增加前，你可以观看牌堆顶x张牌（x为剩余玩家数且最多为5），并以任意顺序置于牌堆顶或牌堆底。', 'zhuge.jpg'),
            ('孙权', '制衡 你弃置x张牌后摸x张牌；若你以此法弃置了全部手牌，则改为摸x+1张牌。', 'sunquan.jpg'),
            ('陆逊', '谦逊 [禁止]/[+2]/[+4]/[乐不思蜀]对你无效。', 'luxun.jpg'),
            ('甘宁', '奇袭 当你打出[绿色]时，你可以指定一名玩家摸1张牌。', 'ganning.jpg'),
            ('张昭张纮', '固政 你可以根据前两张打出的牌的要求出牌。', 'zhangzhao.jpg'),
            ('小乔', '天香 当你被加牌时，你可以弃置1张[红色]，将此加牌串转移给任意一名角色，且你跳过此回合。', 'xiaoqiao.jpg'),
            ('华雄', '耀武 你的手牌数上限调整为8。', 'huaxiong.jpg'),
            ('华佗', '急救 当有玩家喊出“UNO”时，你可以弃置1张[红色]，令其摸1张牌。', 'huatuo.jpg'),
            ('孙尚香', '结姻 当你跳牌时，你可以指定一名男性玩家，你与其各弃置1张牌。', 'sunshangxiang.jpg'),
            ('袁绍', '乱击 当你跳牌时，可以使用1张[万箭齐发]。', 'yuanshao.jpg'),
            ('司马懿', '鬼才 所有玩家的判定牌生效前，你可以用1张手牌替换之。', 'simayi.jpg'),
            ('大乔', '国色 当你打出[红色]时，可以对一名玩家使用1张[乐不思蜀]。', 'daqiao.jpg'),
            ('高顺', '陷阵 你指定一名玩家与之进行拼点：若你赢，你可以继续对本回合未成为【陷阵】目标的玩家使用此技能；反之你摸1张牌且此技能失效一回合。', 'gaoshun.jpg'),
        ]
        dialog = QDialog(self)
        dialog.setWindowTitle('武将图鉴')
        dialog.resize(2100, 1350)
        scroll = QScrollArea(dialog)
        scroll.setWidgetResizable(True)
        content = QWidget()
        vbox = QVBoxLayout(content)
        for name, skill, img in hero_infos:
            hbox = QHBoxLayout()
            img_path = fr'.\images\{img}'
            pix = QPixmap(img_path)
            img_label = QLabel()
            img_label.setPixmap(pix.scaled(530, 750) if not pix.isNull() else QPixmap(530, 750))
            hbox.addWidget(img_label)
            info_vbox = QVBoxLayout()
            info_vbox.addWidget(QLabel(f'<b>{name}</b>'))
            info_vbox.addWidget(QLabel(skill))
            # 预留胜率统计标签
            info_vbox.addWidget(QLabel('胜率：--%'))
            hbox.addLayout(info_vbox)
            vbox.addLayout(hbox)
        content.setLayout(vbox)
        scroll.setWidget(content)
        layout = QVBoxLayout()
        layout.addWidget(scroll)
        dialog.setLayout(layout)
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
        rule_dialog.resize(700, 800)
        vbox = QVBoxLayout(rule_dialog)
        label = QLabel(rule_text)
        label.setWordWrap(True)
        vbox.addWidget(label)
        rule_dialog.setLayout(vbox)
        rule_dialog.exec_()