from player import Player, HumanPlayer, AIPlayer
from typing import List, Callable
from card import UnoCard
from util import PlayedCards, PlayAction
import random
from ai import AI
from PyQt5.QtWidgets import QMessageBox

#胜利条件
class Game:
    def __init__(self, player_num: int, mode: str):
        self.player_num = player_num
        self.playedcards = PlayedCards()
        self.mode = mode

        self.player_list: List[Player] = []
        self.unocard_pack:List[UnoCard] = []

        self.cur_location:int = None
        self.dir: int = 1  #每次加一个dir  1/-1  默认为++
        self.cur_color:str = None
        #flag
        self.draw_n:int = 0
        self.skip:bool = False
        self.gui = None # 添加GUI引用
        self.ai_handler = AI()

        # 当前的加牌链
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
        # 历史记录
        self.history_lines = []

    #创造牌组
    def create_unocard_pack(self):
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
        self.player_num = len(ai_hero_names) + 1

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

        # 3. 随机决定起始玩家
        self.cur_location = random.randint(0, self.player_num - 1)

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
        """选择初始颜色，根据是否有GUI调用不同方法"""
        if self.gui:
            # GUI模式下，弹出颜色选择对话框
            color = self.gui.choose_color_dialog()
            return color if color else random.choice(['red', 'blue', 'yellow', 'green'])
        else:
            # 非GUI模式下（例如测试），随机选择一个颜色
            color = random.choice(['red', 'blue', 'yellow', 'green'])
            print(f"随机选择颜色: {color}")
            return color

    #发牌！每人8张，起始玩家多一张
    def deal_cards(self):
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

    def execute_turn(self):
        """
        统一的回合执行方法 - 无论是AI还是人类玩家
        
        使用观察者模式：GUI作为观察者，不区分AI和人类回合
        """
        if self.game_over:
            return
            
        player = self.player_list[self.cur_location]
        
        # 通知GUI回合开始
        if self.gui:
            self.gui.on_turn_start(player)
        
        # 执行玩家的回合
        player.start_turn()
        
        # 通知GUI回合结束
        if self.gui:
            self.gui.on_turn_end(player)

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
        # 重置skip状态，避免错误跳过玩家
        self.skip = False

    def can_continue_draw_chain(self, player: Player) -> bool:
        """检查玩家是否可以续上+2/+4的链条"""
        if self.draw_n == 0:
            return False
        
        last_card = self.playedcards.get_one()
        if not last_card:
            return False

        last_type = last_card.type
        for card in player.uno_list:
            # 规则：+2上可叠+2或+4，+4上只能叠+4
            if last_type == 'draw2' and card.type in ['draw2', 'wild_draw4']:
                return True
            if last_type == 'wild_draw4' and card.type == 'wild_draw4':
                return True
        return False

    #+2/+4/skip
    def change_flag(self):
        play_info = self.playedcards.get_last_play_info()
        if not play_info:
            return
        
        effective_card, original_card, source_player = play_info
        cardtype = effective_card.type

        if cardtype == "draw2" or cardtype == "wild_draw4":
            self.draw_n += 2 if cardtype == "draw2" else 4
            # 存储完整出牌信息到加牌链
            self.draw_chain_cards.append(play_info)
        elif cardtype == "skip":
            self.skip = True
        elif cardtype == "reverse":
            self.dir *= -1
        else: # 如果打出的牌不是+2/+4，则清空加牌链
            self.draw_chain_cards.clear()
    def next_player(self):
        # 新回合开始，重置行动标志
        self.turn_action_taken = False
        # 新回合开始，清理上一回合的状态
        self.clear_state()
        # 回合开始前，回合数+1
        self.turn_count += 1

        # 正常切换到下一个玩家
        old_location = self.cur_location
        self.cur_location = (self.cur_location + self.dir) % self.player_num
        print(f"回合推进: {old_location} -> {self.cur_location} (方向: {self.dir})")

        # 检查是否需要跳过这个刚刚轮到的玩家
        if self.skip:
            skipped_player = self.player_list[self.cur_location] # 这是要被跳过的玩家
            print(f"跳过玩家: {skipped_player.position} ({skipped_player.mr_card.name})")
            # 记录跳过历史
            self.add_history(f"{skipped_player.mr_card.name} 被跳过！")
            if self.gui:
                # 在GUI中显示跳过信息
                self.gui.show_temporary_message(f"玩家 {skipped_player.position + 1} ({skipped_player.mr_card.name}) 被跳过！")
            
            self.skip = False # 消耗skip状态
            
            # 再次切换，实现跳过
            old_location = self.cur_location
            self.cur_location = (self.cur_location + self.dir) % self.player_num
            print(f"跳过后推进: {old_location} -> {self.cur_location}")

        if self.gui:
            self.gui.wusheng_active = False # 每回合开始时重置武圣状态
        
        # 检查胜利条件（在回合结束时）
        if self.check_win_condition_for_all_players():
            return

    # ==================== 技能处理函数 ====================
    def handle_post_play_skills(self, player: Player, card: UnoCard):
        """处理出牌后可能触发的技能，传递的是原始牌"""
        player.handle_post_play_skills(card)

    def get_next_player(self, current_player_pos: int) -> 'Player':
        """获取当前方向上的下一个玩家"""
        next_pos = (current_player_pos + self.dir) % self.player_num
        return self.player_list[next_pos]

    def add_history(self, text):
        # 只在Game类中维护历史记录，GUI会自动同步
        if self.gui:
            self.gui.add_history(text)

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

