import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QMessageBox, QDialog, QHBoxLayout, QLabel, QComboBox, QListWidget, QListWidgetItem,QInputDialog
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

class MainWindow(QWidget):
    def render_color_label(self):
        """渲染当前卡牌颜色标签"""
        self.color_label = QLabel(f"当前颜色：{self.game.cur_color}")
        self.color_label.setAlignment(Qt.AlignCenter)
        self.color_label.setStyleSheet('font-size:24px;color:#007;background:#eef;border:2px solid #99c;border-radius:10px;min-width:120px;min-height:40px;')
        self.main_layout.addWidget(self.color_label)

    def clear_areas(self):
        """统一销毁所有动态区域"""
        for area in ['card_area', 'action_area', 'player_info_area', 'color_label', 'center_card_label']:
            if hasattr(self, area) and getattr(self, area):
                self.main_layout.removeWidget(getattr(self, area))
                getattr(self, area).deleteLater()
                setattr(self, area, None)

    def get_cur_player_info(self):
        """获取当前玩家、手牌、draw_n、can_draw_chain"""
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        hand = player.uno_list
        draw_n = self.game.draw_n
        can_draw_chain = False
        if draw_n:
            last_type = self.game.playedcards.get_one().type
            for card in hand:
                if (last_type == 'draw2' and card.type in ['draw2', 'wild_draw4']) or (last_type == 'wild_draw4' and card.type == 'wild_draw4'):
                    can_draw_chain = True
                    break
        return cur_idx, player, hand, draw_n, can_draw_chain
    def render_player_info_area(self):
        """渲染玩家信息区"""
        self.player_info_area = QWidget()
        info_layout = QHBoxLayout(self.player_info_area)
        for idx, p in enumerate(self.game.player_list):
            info = f"玩家{idx+1} ({p.team})\n卡牌数: {len(p.uno_list)}"
            label = QLabel(info)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('font-size:20px;background:#eef;border:2px solid #99c;border-radius:10px;min-width:120px;min-height:60px;')
            if idx == self.game.cur_location:
                label.setStyleSheet('font-size:22px;background:#ffe;border:3px solid #c93;border-radius:12px;min-width:140px;min-height:70px;')
            info_layout.addWidget(label)
        self.main_layout.addWidget(self.player_info_area)
    def render_action_area(self, draw_n=None, can_draw_chain=None, end_enabled=False, draw_n_mode=False, only_end=False):
        """渲染操作按钮区，统一出牌/摸牌/结束回合按钮"""
        self.action_area = QWidget()
        action_layout = QHBoxLayout(self.action_area)
        if only_end:
            self.end_btn = QPushButton('结束回合')
            self.end_btn.setFixedSize(120, 60)
            self.end_btn.setStyleSheet('font-size:22px;background:#e6e6ff;border:2px solid #339;border-radius:10px;')
            self.end_btn.clicked.connect(self.on_end_turn_clicked)
            self.end_btn.setEnabled(True)
            action_layout.addWidget(self.end_btn)
            self.main_layout.addWidget(self.action_area)
            return
        if draw_n_mode and draw_n:
            self.draw_n_btn = QPushButton(f'摸{draw_n}张牌')
            self.draw_n_btn.setFixedSize(180, 60)
            self.draw_n_btn.setStyleSheet('font-size:22px;background:#ffe6e6;border:2px solid #933;border-radius:10px;')
            self.draw_n_btn.clicked.connect(self.on_draw_n_clicked)
            action_layout.addWidget(self.draw_n_btn)
        self.play_btn = QPushButton('出牌')
        self.play_btn.setFixedSize(120, 60)
        self.play_btn.setStyleSheet('font-size:22px;background:#e6ffe6;border:2px solid #393;border-radius:10px;')
        self.play_btn.clicked.connect(self.on_play_clicked)
        self.draw_btn = QPushButton('摸牌')
        self.draw_btn.setFixedSize(120, 60)
        self.draw_btn.setStyleSheet('font-size:22px;background:#ffe6e6;border:2px solid #933;border-radius:10px;')
        self.draw_btn.clicked.connect(self.on_draw_clicked)
        # draw2/draw4串时，只允许摸牌（不能出牌）
        if draw_n and not can_draw_chain:
            self.play_btn.setEnabled(False)
            self.draw_btn.setEnabled(False)
        action_layout.addWidget(self.play_btn)
        action_layout.addWidget(self.draw_btn)
        self.end_btn = QPushButton('结束回合')
        self.end_btn.setFixedSize(120, 60)
        self.end_btn.setStyleSheet('font-size:22px;background:#e6e6ff;border:2px solid #339;border-radius:10px;')
        self.end_btn.clicked.connect(self.on_end_turn_clicked)
        self.end_btn.setEnabled(end_enabled)
        action_layout.addWidget(self.end_btn)
        self.main_layout.addWidget(self.action_area)
    def render_hand_area(self, hand, draw_n, can_draw_chain, enable_click=True):
        """渲染手牌区，生成卡牌按钮，手牌过多时自动重叠显示"""
        from PyQt5.QtGui import QPixmap
        from PyQt5.QtWidgets import QStackedLayout, QLayout, QSpacerItem, QSizePolicy
        self.card_area = QWidget()
        card_layout = QHBoxLayout(self.card_area)
        self.card_buttons = []
        card_width = 180
        max_area_width = 1200  # 可视区域最大宽度
        overlap = 0
        n_cards = len(hand)
        # 计算重叠距离
        if n_cards * card_width > max_area_width:
            overlap = int((n_cards * card_width - max_area_width) / (n_cards - 1))
        for i, card in enumerate(hand):
            img_path = self.get_card_image_path(card)
            btn = QPushButton()
            pix = QPixmap(img_path)
            btn.setIcon(QIcon(pix))
            btn.setIconSize(pix.size() if not pix.isNull() else QSize(card_width, 260))
            btn.setFixedSize(card_width, 260)
            btn.setStyleSheet('font-size:24px;background:#fff;border:3px solid #333;border-radius:16px;')
            btn.setToolTip(str(card))
            # 跳牌/强制加牌/skip后，所有卡牌不可点击
            if not enable_click:
                btn.setEnabled(False)
            # draw2/draw4串时，只允许出可叠加的牌
            elif draw_n and not can_draw_chain:
                btn.setEnabled(False)
            elif draw_n and can_draw_chain:
                last_type = self.game.playedcards.get_one().type
                if not ((last_type == 'draw2' and card.type in ['draw2', 'wild_draw4']) or (last_type == 'wild_draw4' and card.type == 'wild_draw4')):
                    btn.setEnabled(False)
            btn.clicked.connect(lambda _, idx=i: self.on_card_clicked(idx))
            self.card_buttons.append(btn)
            if overlap > 0 and i > 0:
                card_layout.addSpacing(-overlap)
            card_layout.addWidget(btn)
        self.main_layout.addWidget(self.card_area)
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Trino 游戏启动界面')
        self.setGeometry(300, 200, 600, 400)
        self.main_layout = QVBoxLayout()

        self.start_btn = QPushButton('开始游戏')
        self.hero_btn = QPushButton('武将图鉴')
        self.rule_btn = QPushButton('游戏规则')
        self.exit_btn = QPushButton('退出游戏')

        self.btns = [self.start_btn, self.hero_btn, self.rule_btn, self.exit_btn]
        for btn in self.btns:
            self.main_layout.addWidget(btn)
        self.setLayout(self.main_layout)

        self.start_btn.clicked.connect(self.show_mode_dialog)
        self.exit_btn.clicked.connect(self.close)
        self.rule_btn.clicked.connect(self.show_rule_dialog)
        self.hero_btn.clicked.connect(self.show_hero_dialog)

        self.card_area = None  # 卡牌展示区
        self.center_card_label = None  # 屏幕中央展示出的牌

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

    def choose_color_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('选择颜色')
        layout = QHBoxLayout(dialog)
        colors = ['red', 'blue', 'yellow', 'green']
        result = {'color': None}
        def set_color(c):
            result['color'] = c
            dialog.accept()
        for c in colors:
            btn = QPushButton(c)
            btn.setStyleSheet(f'background:{c};font-size:22px;min-width:80px;min-height:40px;')
            btn.clicked.connect(lambda _, cc=c: set_color(cc))
            layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec_()
        return result['color']

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

    def show_mode_dialog(self):
        dialog = ModeDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            mode = dialog.selected_mode
            self.show_select_hero(mode)

    def start_game(self, mode, player_hero, other_heros):
        # 隐藏主界面按钮
        for btn in self.btns:
            btn.hide()
        from game import Game
        from player import Player
        # from ai import DeepSeekAI
        num_players = 3
        # ai_player_idx = [1, 2]
        # ai = DeepSeekAI(api_key="sk-d072d2e34a2b42e5ba3ab148b098ca5a")
        self.game = Game(player_num=num_players, mode=mode)
        # 玩家
        self.game.add_player(Player(position=0, team=player_hero))
        # 其余玩家也为手动操作
        for i, hero in enumerate(other_heros, start=1):
            self.game.add_player(Player(position=i, team=hero))
        # self.game.ai = ai
        # 首轮抽牌只设定颜色，不产生效果
        self.game.create_unocard_pack()
        self.game.cur_location = 0
        self.game.deal_cards()
        # 首轮揭示的牌只用于设定颜色，不加入弃牌堆
        card = self.game.unocard_pack.pop()
        if card.type in ['wild', 'wild_draw4']:
            color = self.choose_color_dialog()
            self.game.cur_color = color if color else 'red'
        else:
            self.game.cur_color = card.color
        # 弃牌堆为空，首轮出牌不受揭示牌影响
        self.show_center_card()
        self.show_game_round(first_round=True)

    def get_card_image_path(self, card):
        import sys, os
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

    def show_center_card(self, card=None):
        # 屏幕中央展示所有弃牌堆卡牌（历史区），全部以图片形式呈现
        if self.center_card_label:
            self.main_layout.removeWidget(self.center_card_label)
            self.center_card_label.deleteLater()
        self.center_card_label = QWidget()
        hbox = QHBoxLayout(self.center_card_label)
        # 获取所有弃牌堆卡牌（兼容属性名变化）
        cards = []
        if hasattr(self.game.playedcards, 'd'):
            cards = list(self.game.playedcards.d)
        elif hasattr(self.game.playedcards, 'cards'):
            cards = list(self.game.playedcards.cards)
        if cards:
            from PyQt5.QtGui import QPixmap
            for c in cards:
                img_path = self.get_card_image_path(c)
                label = QLabel()
                pix = QPixmap(img_path)
                label.setPixmap(pix.scaled(80, 120) if not pix.isNull() else QPixmap(80, 120))
                label.setAlignment(Qt.AlignCenter)
                label.setToolTip(str(c))
                hbox.addWidget(label)
        else:
            label = QLabel('暂无出牌')
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('font-size:24px;color:#999;background:#eee;border:2px solid #ccc;border-radius:12px;min-width:80px;min-height:120px;')
            hbox.addWidget(label)
        self.center_card_label.setLayout(hbox)
        self.main_layout.insertWidget(0, self.center_card_label)

    def show_game_round(self, first_round=False):
        self.game.clear_state()
        self.clear_areas()
        self.render_player_info_area()
        cur_idx, player, hand, draw_n, can_draw_chain = self.get_cur_player_info()
        # skip判定：手牌不可点击，只显示结束回合按钮
        if self.game.skip:
            QMessageBox.information(self, '禁牌', '你已被禁牌，跳过本回合！')
            self.clear_areas()
            self.render_player_info_area()
            self.render_hand_area(hand, draw_n, can_draw_chain, enable_click=False)
            self.show_center_card()
            self.render_color_label()
            self.render_action_area(only_end=True)
            self.can_end_turn = True
            return
        # draw2/draw4强制摸牌判定：手牌不可点击，只显示摸牌和结束回合按钮
        last_type = self.game.playedcards.get_one().type if draw_n else None
        if draw_n and not can_draw_chain:
            self.clear_areas()
            self.render_player_info_area()
            self.render_action_area(draw_n=draw_n, can_draw_chain=can_draw_chain, end_enabled=True, draw_n_mode=True)
            self.render_hand_area(hand, draw_n, can_draw_chain, enable_click=False)
            self.show_center_card()
            self.render_color_label()
            self.can_end_turn = True
            self.check_jump_gui()
            return
        # 正常流程，手牌可点击高亮，点击“出牌”按钮直接打出高亮卡牌
        self.render_action_area(draw_n=draw_n, can_draw_chain=can_draw_chain, end_enabled=False)
        self.render_hand_area(hand, draw_n, can_draw_chain, enable_click=True)
        self.show_center_card()
        self.render_color_label()
        self.selected_card_idx = None
    def on_draw_n_clicked(self):
        # 强制摸n张牌
        self.clear_areas()
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        n = self.game.draw_n
        player.get_card(n)
        # 只在玩家摸牌后清理flag，避免提前清零导致加牌失效
        self.game.draw_n = 0
        self.game.clear_state()
        # 只渲染玩家区、手牌区、当前颜色和结束回合按钮
        self.render_player_info_area()
        self.render_hand_area(player.uno_list, 0, False)
        self.show_center_card()
        self.render_color_label()
        # 只显示结束回合按钮
        self.action_area = QWidget()
        action_layout = QHBoxLayout(self.action_area)
        self.end_btn = QPushButton('结束回合')
        self.end_btn.setFixedSize(120, 60)
        self.end_btn.setStyleSheet('font-size:22px;background:#e6e6ff;border:2px solid #339;border-radius:10px;')
        self.end_btn.clicked.connect(self.on_end_turn_clicked)
        self.end_btn.setEnabled(True)
        action_layout.addWidget(self.end_btn)
        self.main_layout.addWidget(self.action_area)
        self.can_end_turn = True
    def check_jump_gui(self):
        # 跳牌：遍历其他玩家，查找能跳牌的牌
        last_card = self.game.playedcards.get_one()
        for idx, player in enumerate(self.game.player_list):
            if idx == self.game.cur_location:
                continue
            for i, card in enumerate(player.uno_list):
                if card.color == last_card.color and card.type == last_card.type and card.value == last_card.value:
                    reply = QMessageBox.question(self, f"玩家{idx+1}跳牌", f"玩家{idx+1}可以跳牌（{card}），是否跳牌？", QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        player.play_a_hand(i)
                        self.game.cur_location = idx
                        self.game.change_flag()
                        # 跳牌后只能结束回合
                        self.clear_areas()
                        self.render_player_info_area()
                        self.render_hand_area(player.uno_list, self.game.draw_n, False)
                        self.show_center_card()
                        self.render_color_label()
                        self.action_area = QWidget()
                        action_layout = QHBoxLayout(self.action_area)
                        self.end_btn = QPushButton('结束回合')
                        self.end_btn.setFixedSize(120, 60)
                        self.end_btn.setStyleSheet('font-size:22px;background:#e6e6ff;border:2px solid #339;border-radius:10px;')
                        self.end_btn.clicked.connect(self.on_end_turn_clicked)
                        self.end_btn.setEnabled(True)
                        action_layout.addWidget(self.end_btn)
                        self.main_layout.addWidget(self.action_area)
                        self.can_end_turn = True
                        return
    def on_play_clicked(self):
        # 出牌按钮：直接打出高亮卡牌
        idx = getattr(self, 'selected_card_idx', None)
        if idx is None:
            QMessageBox.warning(self, '未选中', '请先点击你要出的手牌高亮！')
            return
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        if not player.check_card(player.uno_list[idx]):
            QMessageBox.warning(self, '出牌不合法', '该牌不能出，请选择其他牌！')
            return
        card = player.uno_list[idx]
        if card.type in ['wild', 'wild_draw4']:
            color = self.choose_color_dialog()
            self.game.cur_color = color if color else 'red'
        player.play_a_hand(idx)
        self.game.change_flag()
        self.check_jump_gui()
        self.play_btn.setEnabled(False)
        self.draw_btn.setEnabled(False)
        self.can_end_turn = True
        self.end_btn.setEnabled(True)
        if len(player.uno_list) == 0:
            QMessageBox.information(self, '游戏结束', f"玩家{cur_idx+1}（{player.team}）获胜！")
            self.back_to_menu()
            return

    def on_draw_clicked(self):
        # 摸牌按钮：玩家主动摸一张牌，摸牌后需点击结束回合
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        player.get_card(1)
        # 摸牌后禁用摸牌和出牌按钮，需点击结束回合
        self.play_btn.setEnabled(False)
        self.draw_btn.setEnabled(False)
        self.can_end_turn = True
        self.end_btn.setEnabled(True)
    def show_center_card(self, card=None):
        # 屏幕中央展示所有出过的牌（出牌历史）
        if self.center_card_label:
            self.main_layout.removeWidget(self.center_card_label)
            self.center_card_label.deleteLater()
        self.center_card_label = QWidget()
        hbox = QHBoxLayout(self.center_card_label)
        # 获取所有出过的牌，安全处理空牌堆
        cards = []
        if hasattr(self.game.playedcards, 'cards'):
            cards = list(self.game.playedcards.cards)
        else:
            try:
                one = self.game.playedcards.get_one()
                if one:
                    cards = [one]
            except Exception:
                cards = []
        if cards:
            for c in cards:
                label = QLabel(str(c))
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet('font-size:24px;color:#222;background:#ffe;border:2px solid #c93;border-radius:12px;min-width:80px;min-height:120px;')
                hbox.addWidget(label)
        else:
            label = QLabel('暂无出牌')
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet('font-size:24px;color:#999;background:#eee;border:2px solid #ccc;border-radius:12px;min-width:80px;min-height:120px;')
            hbox.addWidget(label)
        self.center_card_label.setLayout(hbox)
        self.main_layout.insertWidget(0, self.center_card_label)

    def highlight_selected_card(self, idx):
        # 高亮选中卡牌，取消其他卡牌高亮
        for i, btn in enumerate(self.card_buttons):
            if i == idx:
                btn.setStyleSheet('font-size:24px;background:#fffdc0;border:4px solid #f90;border-radius:16px;')
            else:
                btn.setStyleSheet('font-size:24px;background:#fff;border:3px solid #333;border-radius:16px;')
        self.selected_card_idx = idx

    def on_card_clicked(self, idx):
        # 直接高亮选中卡牌
        self.highlight_selected_card(idx)
        self.selected_card_idx = idx
    def on_confirm_play_clicked(self):
        # 确认出牌按钮：真正打出高亮卡牌
        idx = getattr(self, 'selected_card_idx', None)
        if idx is None:
            QMessageBox.warning(self, '未选中', '请先点击你要出的手牌高亮！')
            return
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        if not player.check_card(player.uno_list[idx]):
            QMessageBox.warning(self, '出牌不合法', '该牌不能出，请选择其他牌！')
            return
        card = player.uno_list[idx]
        # wild/wild_draw4 选色
        if card.type in ['wild', 'wild_draw4']:
            color = self.choose_color_dialog()
            self.game.cur_color = color if color else 'red'
        player.play_a_hand(idx)
        self.game.change_flag()
        self.check_jump_gui()
        self.play_btn.setEnabled(False)
        self.draw_btn.setEnabled(False)
        self.confirm_btn.setEnabled(False)
        self.can_end_turn = True
        self.end_btn.setEnabled(True)
        # 游戏结束判断
        if len(player.uno_list) == 0:
            QMessageBox.information(self, '游戏结束', f"玩家{cur_idx+1}（{player.team}）获胜！")
            self.back_to_menu()
            return
    def back_to_menu(self):
        # 回到主菜单，清空所有动态区，显示主界面按钮
        self.clear_areas()
        for btn in self.btns:
            btn.show()
        self.setWindowTitle('Trino 游戏启动界面')

    def on_end_turn_clicked(self):
        # 结束回合按钮：切换到下一玩家
        self.game.next_player()
        self.show_game_round()

    def get_player_card_index(self, player):
        # 弹窗让玩家选择出牌序号
        hand = '\n'.join([f'{i}: {str(card)}' for i, card in enumerate(player.uno_list)])
        idx, ok = QInputDialog.getInt(self, '出牌', f'你的手牌：\n{hand}\n请输入你要出的牌序号：', 0, 0, len(player.uno_list)-1, 1)
        return idx, ok

    def show_select_hero(self, mode):
        select_dialog = SelectHeroDialog(mode, self)
        select_dialog.exec_()

class ModeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('选择游戏模式')
        self.selected_mode = None
        layout = QVBoxLayout()
        self.combo = QComboBox()
        self.combo.addItems(['1v1', '2v2', '4人混战'])
        layout.addWidget(QLabel('请选择模式：'))
        layout.addWidget(self.combo)
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton('确定')
        cancel_btn = QPushButton('取消')
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        ok_btn.clicked.connect(self.accept_mode)
        cancel_btn.clicked.connect(self.reject)

    def accept_mode(self):
        self.selected_mode = self.combo.currentText()
        self.accept()

class SelectHeroDialog(QDialog):
    def on_ready(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, '提示', '请选择一个武将！')
            return
        player_hero = selected_items[0].text()
        other_heros = [h for h in self.hero_list if h != player_hero]
        QMessageBox.information(self, '准备完成', f'你选择了：{player_hero}\n电脑玩家分配武将：{other_heros}')
        self.parent().start_game(self.mode, player_hero, other_heros)
        self.accept()
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle('选择武将')
        self.mode = mode
        layout = QVBoxLayout()
        self.hero_list = self.get_random_heros(3)
        layout.addWidget(QLabel(f'请从以下武将中选择一位：'))
        self.list_widget = QListWidget()
        for hero in self.hero_list:
            item = QListWidgetItem(hero)
            self.list_widget.addItem(item)
        layout.addWidget(self.list_widget)
        self.ready_btn = QPushButton('准备')
        layout.addWidget(self.ready_btn)
        self.setLayout(layout)
        self.ready_btn.clicked.connect(self.on_ready)

    def get_random_heros(self, n):
        all_heros = [
            '曹操', '甄姬', '郭嘉', '许褚', '刘备', '刘禅', '关羽', '张飞', '赵云', '诸葛亮',
            '孙权', '陆逊', '甘宁', '张昭张纮', '小乔', '华雄', '华佗', '孙尚香', '袁绍', '司马懿',
            '大乔', '高顺'
        ]
        return random.sample(all_heros, n)

    def on_draw_n_clicked(self):
        # 强制摸n张牌
        self.clear_areas()
        cur_idx = self.game.cur_location
        player = self.game.player_list[cur_idx]
        n = self.game.draw_n
        player.get_card(n)
        self.game.draw_n = 0
        # 只渲染玩家区、手牌区、当前颜色和结束回合按钮
        self.render_player_info_area()
        self.render_hand_area(player.uno_list, 0, False)
        self.show_center_card()
        self.render_color_label()
        # 只显示结束回合按钮
        self.action_area = QWidget()
        action_layout = QHBoxLayout(self.action_area)
        self.end_btn = QPushButton('结束回合')
        self.end_btn.setFixedSize(120, 60)
        self.end_btn.setStyleSheet('font-size:22px;background:#e6e6ff;border:2px solid #339;border-radius:10px;')
        self.end_btn.clicked.connect(self.on_end_turn_clicked)
        self.end_btn.setEnabled(True)
        action_layout.addWidget(self.end_btn)
        self.main_layout.addWidget(self.action_area)
        self.can_end_turn = True