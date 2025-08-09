from player import Player, HumanPlayer, AIPlayer
from typing import List, Callable
from card import UnoCard
from util import PlayedCards, PlayAction
import random
from ai import AI
from PyQt5.QtWidgets import QMessageBox

#胜利条件
class Game:
    def __init__(self, player_num: int, test_mode=False):
        self.player_num = player_num
        self.test_mode = test_mode
        self.playedcards = PlayedCards()

        self.player_list: List[Player] = []
        self.unocard_pack: List[UnoCard] = []

        self.cur_location: int = None
        self.dir: int = 1  # 回合方向 1/-1
        self.cur_color: str = None
        # flag
        self.draw_n: int = 0
        self.skip: bool = False
        self.gui = None  # GUI 引用
        self.ai_handler = AI()

        # 当前的+牌串
        self.draw_chain_cards: List[UnoCard] = []

        # 游戏是否结束的标志
        self.game_over = False
        # 回合内是否已行动
        self.turn_action_taken = False
        self.turn_count = 0
        # 弃牌模式相关状态
        self.is_discard_mode = False
        self.player_in_discard = None
        self.cards_to_draw_in_discard = []
        self.num_to_discard = 0
        # 历史记录（仅在Game维护，GUI被动刷新）
        self.history_lines = []  # list[str]
        self.max_history = 50
        # 跳牌后抑制下一条普通出牌历史标志（用于避免“跳牌！”后立刻出现常规出牌格式）
        self.suppress_next_play_history = False

        # 在强制摸牌后，禁止当前玩家再触发跳牌的保护标志
        self.skip_jump_after_forced_draw = False
        self.player_who_just_forced_draw = None

        # 仅在“有人真正出牌”后才开放跳牌窗口
        self.jump_window_open = False

        # 统计数据：每位玩家的结算回顾
        # 结构: { player: { 'played_cards': int, 'drawn_cards': int, 'skills_used': int, 'caused_neighbor_draws': int } }
        self.stats = {}

    def _ensure_player_stats(self, player):
        if player not in self.stats:
            self.stats[player] = {
                'played_cards': 0,
                'drawn_cards': 0,
                'skills_used': 0,
                'caused_neighbor_draws': 0,
            }

    def record_play(self, player):
        self._ensure_player_stats(player)
        self.stats[player]['played_cards'] += 1

    def record_draw(self, player, count):
        if count <= 0:
            return
        self._ensure_player_stats(player)
        self.stats[player]['drawn_cards'] += int(count)

    def record_skill(self, player, skill_name: str = None):
        self._ensure_player_stats(player)
        self.stats[player]['skills_used'] += 1

    def attribute_forced_draw(self, drawing_player, total_draw_count: int):
        """将强制摸牌数按+2/+4贡献者分摊到对应的来源玩家。"""
        if total_draw_count <= 0:
            return
        # 汇总每个来源玩家的贡献值
        contributions = []  # list[(source_player, contributed)]
        for effective_card, original_card, source_player in self.draw_chain_cards:
            if not source_player:
                continue
            contributed = 2 if effective_card.type == 'draw2' else 4 if effective_card.type == 'wild_draw4' else 0
            if contributed > 0:
                contributions.append((source_player, contributed))
        if not contributions:
            return
        remaining = int(total_draw_count)
        for source_player, contributed in contributions:
            if remaining <= 0:
                break
            alloc = min(contributed, remaining)
            self._ensure_player_stats(source_player)
            self.stats[source_player]['caused_neighbor_draws'] += alloc
            remaining -= alloc

    #创造牌组
    def create_unocard_pack(self):
        if self.test_mode:
            # 测试模式：创建固定的牌组，不洗牌
            self.unocard_pack = []
            # 每个玩家获得相同的8张牌：1张skip, 1张draw2, 1张reverse, 1张wild, 1张wild_draw4, 1张红1, 1张绿1, 1张蓝1
            test_cards = [
                UnoCard('skip', 'red', 0),
                UnoCard('draw2', 'blue', 0),
                UnoCard('reverse', 'green', 0),
                UnoCard('wild', 'wild', 10),
                UnoCard('wild_draw4', 'wild_draw4', 10),
                UnoCard('number', 'red', 1),
                UnoCard('number', 'green', 1),
                UnoCard('number', 'blue', 1)
            ]
            # 为三个玩家创建相同的牌组，再加上一张额外的牌作为初始牌
            for _ in range(3):
                self.unocard_pack.extend(test_cards)
            # 添加一张额外的牌作为初始牌（选择一张颜色牌）
            self.unocard_pack.append(UnoCard('number', 'yellow', 5))
            # 不洗牌，保持固定顺序
            print(f"测试模式：创建了 {len(self.unocard_pack)} 张牌，每个玩家8张相同的牌，外加1张初始牌")
        else:
            # 正常模式
            colors = ['red','blue','yellow','green']
            type = ['reverse','skip','draw2']*2
            numbers = [0] + 2*[i for i in range(1,10)]
            for color in colors:
                for number in numbers:
                    self.unocard_pack.append(UnoCard("number",color,number))
                for action in type:
                    self.unocard_pack.append(UnoCard(action,color,0))
            for _ in range(4):
                self.unocard_pack.append(UnoCard('wild','wild',10))
                self.unocard_pack.append(UnoCard('wild_draw4','wild_draw4',10))
            random.shuffle(self.unocard_pack)
        
    #将玩家加对对局中同时将game赋給玩家
    def add_player(self,player:Player):
        self.player_list.append(player)
        player.game = self

    def set_gui(self, gui):
        """设置GUI的引用"""
        self.gui = gui
        for player in self.player_list:
            player.game = self # 确保所有player的game实例都更新

    def initialize_players(self, player_hero_name: str, ai_hero_names: List[str]):
        """根据英雄名称创建和初始化所有玩家"""
        from player import HumanPlayer, AIPlayer
        from mr_cards import all_heroes

        self.player_list.clear()
        # 不要覆盖player_num，使用构造函数中设置的值
        # self.player_num = len(ai_hero_names) + 1

        # 创建人类玩家
        player_mr_card = all_heroes.get(player_hero_name)
        if player_mr_card:
            p1 = HumanPlayer(position=0, team=player_mr_card.team)
            p1.mr_card = player_mr_card
            self.add_player(p1)

        # 创建AI玩家
        for i, hero_name in enumerate(ai_hero_names):
            other_mr_card = all_heroes.get(hero_name)
            if other_mr_card:
                p = AIPlayer(position=i + 1, team=other_mr_card.team)
                p.mr_card = other_mr_card
                self.add_player(p)

    def game_start(self, player_hero_name: str, ai_hero_names: List[str]):
        """启动一个全新的游戏，可用于GUI或非GUI模式"""
        # 1. 初始化玩家
        self.initialize_players(player_hero_name, ai_hero_names)
        # 2. 完成剩余的设置
        self.finalize_setup()

    def finalize_setup(self):
        """创建牌组、发牌并开始游戏的第一回合。"""
        # 2. 创建和洗牌
        self.create_unocard_pack()

        # 3. 随机决定起始玩家 - 确保在玩家列表范围内
        actual_player_count = len(self.player_list)
        self.cur_location = random.randint(0, actual_player_count - 1)

        # 4. 发牌
        self.deal_cards()
        
        # 5. 翻开第一张牌，如果是黑色牌则重新翻牌直到是颜色牌
        while True:
            card = self.unocard_pack.pop()
            if card.type in ['wild', 'wild_draw4']:
                # 黑色牌置入弃牌堆
                print(f"游戏开始，第一张牌是黑色牌：{card}，置入弃牌堆")
                # 不加入playedcards，直接丢弃
            else:
                # 颜色牌，加入牌堆并确定颜色
                self.playedcards.add_card(card, source_player=None)
                self.cur_color = card.color
                print(f"游戏开始，揭示的第一张牌为：{card}")
                break

    def _choose_initial_color(self):
        """选择初始颜色"""
        if self.gui:
            # GUI模式下，弹出颜色选择对话框
            color = self.gui.choose_color_dialog()
            return color if color else random.choice(['red', 'blue', 'yellow', 'green'])
        else:
            # 如果没有GUI，随机选择一个颜色
            return random.choice(['red', 'blue', 'yellow', 'green'])

    #发牌！每人8张，起始玩家多一张
    def deal_cards(self):
        if self.test_mode:
            # 测试模式：每个玩家获得完全相同的8张牌
            for i, player in enumerate(self.player_list):
                cards_to_draw = min(8, player.hand_limit)
                player.draw_cards(cards_to_draw)
            print(f"测试模式：为 {len(self.player_list)} 个玩家各发了8张相同的牌")
        else:
            # 正常模式
            for i, player in enumerate(self.player_list):
                if i == self.cur_location:
                    # 第一个玩家摸牌时考虑手牌上限
                    cards_to_draw = min(9, player.hand_limit)
                    player.draw_cards(cards_to_draw)
                else:
                    # 其他玩家摸牌时考虑手牌上限
                    cards_to_draw = min(8, player.hand_limit)
                    player.draw_cards(cards_to_draw)
    
    # ==================== 技能处理函数 ====================


    def execute_skill_wusheng(self, player, card_idx):
        """统一的武圣技能处理入口"""
        player.execute_skill_wusheng(card_idx)

    def execute_skill(self, skill, player, *args):
        """统一的技能执行入口"""
        player.execute_skill(skill, *args)



    def notify_card_played(self, player, card):
        """通知GUI有玩家出牌"""
        if self.gui:
            self.gui.on_card_played(player, card)
    
    def notify_cards_drawn(self, player, num_cards):
        """通知GUI有玩家摸牌"""
        if self.gui:
            self.gui.on_cards_drawn(player, num_cards)
    
    def notify_player_hand_changed(self, player):
        """通知GUI玩家手牌数量变化"""
        if self.gui:
            self.gui.on_player_hand_changed(player)
    
    def notify_draw_pile_changed(self):
        """通知GUI摸牌堆数量变化"""
        if self.gui:
            self.gui.on_draw_pile_changed()
    
    def notify_history_updated(self, message):
        """通知GUI历史记录更新"""
        if self.gui:
            self.gui.on_history_updated(message)
    
    def notify_game_state_changed(self):
        """通知GUI游戏状态变化（通用）"""
        if self.gui:
            self.gui.on_game_state_changed()
               
    #结算所有状态（处理skip和draw2/draw4的移除）
    def clear_state(self):
        # 重置弃牌状态
        self.is_discard_mode = False
        self.player_in_discard = None
        self.cards_to_draw_in_discard.clear()
        self.num_to_discard = 0
        # 重置GUI相关的状态
        if self.gui:
            self.gui.wusheng_active = False
        # 注意：不要在此处重置 skip
        # skip 应在下一位玩家结算时消耗（见 _advance_to_next_player 或 Player._check_and_handle_skip）

    def can_continue_draw_chain(self, player: Player) -> bool:
        """检查玩家是否可以续上+2/+4的牌串"""
        if self.draw_n == 0:
            return False
        
        last_card = self.playedcards.get_one()
        if not last_card:
            return False

        last_type = last_card.type
        for card in player.uno_list:
            # 新规则：+2上可叠+2或+4，+4上只能叠+4
            if last_type == 'draw2' and card.type in ['draw2', 'wild_draw4']:
                return True
            if last_type == 'wild_draw4' and card.type == 'wild_draw4':
                return True
        return False

    #+2/+4/skip
    def change_flag(self, is_jump=False):
        play_info = self.playedcards.get_last_play_info()
        if not play_info:
            return
        
        effective_card, original_card, source_player = play_info
        cardtype = effective_card.type

        if cardtype == "draw2" or cardtype == "wild_draw4":
            self.draw_n += 2 if cardtype == "draw2" else 4
            # 存储完整出牌信息到+牌串
            self.draw_chain_cards.append(play_info)
        elif cardtype == "skip":
            self.skip = True
        elif cardtype == "reverse":
            self.dir *= -1
            # 跳牌时不记录方向反转的历史记录，因为reverse效果不生效
            if not is_jump:
                self.add_history("方向反转！")
        else: # 如果打出的牌不是+2/+4，则清空+牌串
            self.draw_chain_cards.clear()
            self.draw_n = 0


    # ==================== 技能处理函数 ====================
    def handle_post_play_skills(self, player: Player, card: UnoCard):
        """处理出牌后可能触发的技能，传递的是原始牌"""
        player.handle_post_play_skills(card)

    def add_history(self, text):
        """添加历史记录（Game层统一维护）。"""
        if not text:
            return
        self.history_lines.append(text)
        if len(self.history_lines) > self.max_history:
            self.history_lines = self.history_lines[-self.max_history:]
        # 通知GUI刷新（GUI读取 self.history_lines）
        if self.gui and hasattr(self.gui, 'on_history_updated'):
            try:
                self.gui.on_history_updated(text)
            except Exception:
                pass

    # ==================== 跳牌相关的技能触发 ====================
    def _trigger_jump_skills(self, player, jump_card):
        """跳牌后触发的技能（旋风 / 散谣等）。
        只在成功进入跳牌玩家特殊回合后调用一次。"""
        if not player or not player.mr_card or not jump_card:
            return
        for skill in player.mr_card.skills:
            cls_name = skill.__class__.__name__
            # 旋风：弃相同点数
            if cls_name == 'XuanFeng':
                try:
                    hist = skill(jump_card, player)
                    if hist:
                        self.add_history(hist)
                except Exception:
                    pass
            # 散谣：指定一人摸2
            if cls_name == 'SanYao':
                try:
                    # 目标选择：AI 预选（简单策略：选择手牌最多的其他玩家），人类由GUI弹框
                    target = None
                    if self._is_player_ai(player):
                        others = [p for p in self.player_list if p is not player]
                        if others:
                            target = max(others, key=lambda p: len(p.uno_list))
                    hist = skill(jump_card, player, target)
                    if hist:
                        self.add_history(hist)
                except Exception:
                    pass

    def check_win_condition(self, player):
        """检查胜利条件：手牌为0或牌堆拿完时先比较手牌数量，再比较点数之和"""
        # 检查手牌为0的胜利条件
        if len(player.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(player)
            return True
        
        # 检查牌堆拿完时的胜利条件
        if len(self.unocard_pack) == 0:
            # 收集所有玩家的手牌信息
            player_hand_info = {}
            for p in self.player_list:
                hand_count = len(p.uno_list)
                hand_value_sum = sum(card.value for card in p.uno_list if hasattr(card, 'value') and card.value is not None)
                player_hand_info[p] = (hand_count, hand_value_sum)
            
            # 找到手牌数量最少的玩家
            min_count = min(info[0] for info in player_hand_info.values())
            players_with_min_count = [p for p, (count, _) in player_hand_info.items() if count == min_count]
            
            if len(players_with_min_count) == 1:
                # 只有一个玩家手牌数量最少，直接获胜
                winner = players_with_min_count[0]
                self.game_over = True
                if self.gui:
                    self.gui.show_winner_and_exit(winner)
                return True
            else:
                # 多个玩家手牌数量相同且最少，比较点数之和
                min_value = min(player_hand_info[p][1] for p in players_with_min_count)
                winners = [p for p in players_with_min_count if player_hand_info[p][1] == min_value]
                
                if len(winners) == 1:
                    # 只有一个玩家点数之和最小，获胜
                    winner = winners[0]
                    self.game_over = True
                    if self.gui:
                        self.gui.show_winner_and_exit(winner)
                    return True
                else:
                    # 多个玩家点数之和相同且最小，平局
                    self.game_over = True
                    if self.gui:
                        self.gui.show_draw_and_exit(winners)
                    return True
        
        return False

    def check_win_condition_for_all_players(self):
        """检查所有玩家的胜利条件"""
        for player in self.player_list:
            if self.check_win_condition(player):
                return True
        return False

    def notify_gui_turn_start(self, player):
        """通知GUI回合开始"""
        if self.gui:
            self.gui.on_turn_start(player)

    def notify_gui_turn_end(self, player):
        """通知GUI回合结束"""
        if self.gui:
            self.gui.on_turn_end(player)

    def notify_gui_show_round(self):
        """通知GUI显示当前回合"""
        if self.gui:
            self.gui.show_game_round()

    def notify_gui_continue_loop(self):
        """通知GUI继续游戏循环"""
        if self.gui:
            self.gui.continue_game_loop()

    def start_gui_game_loop(self):
        """启动GUI模式的游戏循环"""
        if not self.gui:
            return
            
        # 显示第一个玩家的回合
        first_player = self.get_current_player()
        self._schedule_next_turn(first_player)

    def execute_gui_game_step(self):
        """执行GUI游戏循环的一个步骤"""
        if self.game_over:
            return
            
        # 获取当前玩家
        current_player = self.get_current_player()
        
        # 检查游戏是否结束
        if self.check_win_condition_for_all_players():
            return
            
        # 只有在“上一动作是出牌”时才检查跳牌
        jump_occurred = (self.jump_window_open and self.check_for_jump())
        
        if jump_occurred:
            # 处理跳牌逻辑
            self.handle_gui_jump_turn()
        else:
            # 正常执行玩家回合
            self._execute_player_turn(current_player)

    def continue_gui_game_loop(self):
        """继续GUI游戏循环"""
        # 检查当前玩家是否已完成回合
        current_player = self.get_current_player()
        
        if self.turn_action_taken:
            # 回合已完成，先检查是否有跳牌（新规则：每次回合结束后但下一个玩家回合开始前检查）
            if self.jump_window_open and self.check_for_jump():
                # 有跳牌，处理跳牌逻辑
                self.handle_gui_jump_turn()
            else:
                # 没有跳牌，移动到下一个玩家
                self._advance_to_next_player()
        else:
            # 回合未完成，继续等待
            self.gui.restart_game_loop()

    def handle_gui_jump_turn(self):
        """处理GUI模式下的跳牌玩家特殊回合（支持出牌者自跳）。"""
        last_play_info = self.playedcards.get_last_play_info()
        if not last_play_info:
            return
        effective_card, original_card, source_player = last_play_info

        # 从当前玩家开始，寻找第一个可以跳牌的玩家（包含当前玩家）
        chosen_pos = None
        start_pos = self.cur_location
        for i in range(len(self.player_list)):
            check_pos = (start_pos + i) % len(self.player_list)
            player = self.player_list[check_pos]
            if player.check_for_jump(effective_card):
                chosen_pos = check_pos
                break

        if chosen_pos is None:
            # 没有任何玩家可以跳牌，则进入下一位
            self._advance_to_next_player()
            return
        
        jump_player = self.player_list[chosen_pos]
        print(f"跳牌玩家特殊回合: {jump_player.mr_card.name}")
        # 记录跳牌历史（不再按普通出牌格式记录）
        self.add_history(f"{jump_player.mr_card.name} 跳牌！")
        # 抑制下一条普通出牌历史（下一次调用process_play_action的常规记录被跳过）
        self.suppress_next_play_history = True

        # 更新位置到跳牌玩家
        self.cur_location = chosen_pos
        
        # 安排跳牌玩家的特殊回合
        if self._is_player_ai(jump_player):
            # AI跳牌玩家，延迟执行并在执行前尝试触发跳牌技能
            self._trigger_jump_skills(jump_player, effective_card)
            self.gui.schedule_jump_player_turn(jump_player, 500)
        else:
            # 人类跳牌玩家：先触发可询问技能（在技能内部会弹窗），然后展示界面继续操作
            self._trigger_jump_skills(jump_player, effective_card)
            self.gui.show_game_round()

    def execute_jump_player_turn_gui(self, jump_player):
        """执行GUI模式下的跳牌玩家特殊回合"""
        # 执行跳牌玩家的特殊回合
        jump_player.jump_turn()
        
        # 跳牌玩家回合结束后，检查是否还有其他玩家可以跳牌
        if self.check_for_jump():
            # 还有其他玩家可以跳牌，继续处理跳牌
            self.handle_gui_jump_turn()
        else:
            # 没有其他玩家可以跳牌，进入最后一个跳牌玩家的下一个玩家的正常回合
            # 使用_advance_to_next_player来确保skip逻辑被正确处理
            self._advance_to_next_player()

    # ==================== 通用游戏逻辑方法 ====================
    def _get_next_player_pos(self, current_pos=None):
        """获取下一个玩家位置"""
        if current_pos is None:
            current_pos = self.cur_location
        return (current_pos + self.dir) % len(self.player_list)

    def _get_next_player(self, current_pos=None):
        """获取下一个玩家"""
        next_pos = self._get_next_player_pos(current_pos)
        return self.player_list[next_pos]

    def _is_player_ai(self, player):
        """检查玩家是否为AI"""
        from player import AIPlayer
        return isinstance(player, AIPlayer)

    def _is_player_human(self, player):
        """检查玩家是否为人类"""
        from player import HumanPlayer
        return isinstance(player, HumanPlayer)

    def _schedule_next_turn(self, next_player, delay_ms=300):
        """安排下一个玩家的回合"""
        if self._is_player_ai(next_player):
            # AI玩家，延迟执行
            self.gui.schedule_ai_turn(delay_ms)
        else:
            # 人类玩家，显示界面等待用户操作
            self.gui.show_game_round()

    def _calculate_draw_chain_total(self):
        """计算+牌串的总摸牌数"""
        return sum(2 if effective_card.type == 'draw2' else 4 for effective_card, original_card, source_player in self.draw_chain_cards)

    def _clear_draw_chain(self):
        """清空+牌串"""
        self.draw_chain_cards.clear()
        self.draw_n = 0

    def _handle_jump_chain_failure(self, jump_player):
        """处理+牌串失败的情况"""
        print(f"{jump_player.mr_card.name} 无法续上+牌串，需要摸牌")
        
        # 计算需要摸的牌数
        total_draw = self._calculate_draw_chain_total()
        jump_player.draw_cards(total_draw)
        
        # 清空+牌串
        self._clear_draw_chain()
        
        # 移动到下一个玩家
        self.cur_location = self._get_next_player_pos()  # 使用当前的cur_location（跳牌玩家的位置）
        next_player = self.player_list[self.cur_location]
        
        # 检查游戏是否结束
        if self.check_win_condition_for_all_players():
            return
        
        # 安排下一个玩家的回合
        self._schedule_next_turn(next_player)

    def _handle_jump_chain_success(self, jump_player):
        """处理+牌串成功的情况"""
        print(f"{jump_player.mr_card.name} 可以续上+牌串")
        
        # 安排跳牌玩家的回合
        if self._is_player_ai(jump_player):
            # AI跳牌玩家，延迟执行
            self.gui.schedule_jump_player_turn(jump_player, 500)
        else:
            # 人类跳牌玩家，显示界面等待用户操作
            self.gui.show_game_round()

    def _execute_player_turn(self, player):
        """执行玩家回合"""
        if self._is_player_ai(player):
            # AI玩家，直接执行回合
            player.turn()
            # AI出牌/行动后，停顿2秒再继续游戏循环
            self.gui.schedule_continue_loop(2000)
        else:
            # 人类玩家，停止游戏循环计时器，显示界面等待用户操作
            self.gui.stop_game_loop()
            self.gui.show_game_round()

    def _advance_to_next_player(self):
        """移动到下一个玩家"""
        self.cur_location = self._get_next_player_pos()
        next_player = self.player_list[self.cur_location]
        # 进入下一玩家回合时，清除“强制摸牌后禁止跳牌”的保护标志
        self.skip_jump_after_forced_draw = False
        self.player_who_just_forced_draw = None
        # 进入下一回合前关闭跳牌窗口，直到下一次出牌后再开启
        self.jump_window_open = False
        
        # 检查游戏是否结束
        if self.check_win_condition_for_all_players():
            return
        
        # 检查skip状态
        if self.skip:
            print(f"玩家 {next_player.position+1} ({next_player.mr_card.name}) 被跳过")
            self.add_history(f"{next_player.mr_card.name} 被跳过！")
            if self.gui:
                self.gui.show_temporary_message(f"玩家 {next_player.position + 1} ({next_player.mr_card.name}) 被跳过！")
            
            self.skip = False  # 消耗skip状态
            
            # 再次移动到下一个玩家（跳过当前玩家）
            self.cur_location = self._get_next_player_pos()
            next_player = self.player_list[self.cur_location]
            
            # 再次检查游戏是否结束
            if self.check_win_condition_for_all_players():
                return
        
        # 安排下一个玩家的回合
        self._schedule_next_turn(next_player)

    # ==================== 游戏状态管理器 ====================
    def get_current_player(self):
        """获取当前玩家"""
        return self.player_list[self.cur_location]

    def get_current_player_info(self):
        """获取当前玩家信息"""
        player = self.get_current_player()
        return {
            'player': player,
            'position': self.cur_location,
            'draw_n': self.draw_n,
            'can_draw_chain': self.can_continue_draw_chain(player),
            'is_forced_draw_pending': self.draw_n > 0,
            'can_play': len(player.uno_list) > 0
        }

    def get_game_state(self):
        """获取游戏状态"""
        return {
            'cur_location': self.cur_location,
            'dir': self.dir,
            'cur_color': self.cur_color,
            'draw_n': self.draw_n,
            'turn_action_taken': self.turn_action_taken,
            'game_over': self.game_over,
            'draw_pile_count': len(self.unocard_pack),
            'last_card': self.playedcards.get_one() if self.playedcards else None,
            'draw_chain_cards': self.draw_chain_cards
        }

    def get_player_list(self):
        """获取玩家列表"""
        return self.player_list

    def is_current_player_human(self):
        """检查当前玩家是否为人类玩家"""
        return self._is_player_human(self.get_current_player())

    def is_current_player_ai(self):
        """检查当前玩家是否为AI玩家"""
        return self._is_player_ai(self.get_current_player())

    def get_players_for_dialog(self, exclude_self=False):
        """获取用于对话框的玩家列表"""
        players = []
        for p in self.player_list:
            if exclude_self and p.position == self.cur_location:
                continue
            players.append(p)
        return players

    def check_for_jump(self) -> bool:
        """检测是否有玩家可以跳牌"""
        last_play_info = self.playedcards.get_last_play_info()
        if not last_play_info:
            return False
        
        effective_card, original_card, source_player = last_play_info
        
        # 检查source_player是否为None
        if source_player is None:
            return False
        
        # 从当前玩家的位置开始检查跳牌（允许出牌者自己跳）
        current_pos = self.cur_location
        for i in range(len(self.player_list)):
            # 从当前玩家开始，按顺序检查每个玩家
            check_pos = (current_pos + i) % len(self.player_list)
            # 如果上一动作是强制摸牌，则禁止“刚被强制摸牌的玩家”立刻跳牌
            if self.skip_jump_after_forced_draw and self.player_who_just_forced_draw is not None:
                if self.player_list[check_pos] is self.player_who_just_forced_draw:
                    continue
            player = self.player_list[check_pos]
            potential_jumps = player.check_for_jump(effective_card)
            if potential_jumps:
                return True
        
        return False

    def continue_game_after_jump_turn(self):
        """跳牌回合结束后继续游戏"""
        # 跳牌玩家回合结束后，检查是否还有其他玩家可以跳牌
        if self.check_for_jump():
            # 还有其他玩家可以跳牌，继续处理跳牌
            self.handle_gui_jump_turn()
        else:
            # 没有其他玩家可以跳牌，进入最后一个跳牌玩家的下一个玩家的正常回合
            # 使用_advance_to_next_player来确保skip逻辑被正确处理
            self._advance_to_next_player()



