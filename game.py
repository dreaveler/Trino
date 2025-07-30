from player import Player
from typing import List, Callable
from card import UnoCard
from util import PlayedCards, PlayAction
import random
from ai import AI
from PyQt5.QtWidgets import QMessageBox

#胜利条件
class Game:
    def check_jump(self):
        # TODO: Add a GUI-based mechanism for human players to jump.
        # TODO: Add AI logic for jumping.
        # For now, this feature is disabled in GUI mode.
        if not self.gui:
            # 跳牌逻辑：遍历所有玩家，查找能跳牌的玩家（除当前玩家）
            last_card = self.playedcards.get_one()
            for idx, player in enumerate(self.player_list):
                if idx == self.cur_location:
                    continue
                for i, card in enumerate(player.uno_list):
                    # 普通跳牌
                    if card.color == last_card.color and card.type == last_card.type and card.value == last_card.value:
                        print(f"玩家{idx+1}可以跳牌！手牌序号：{i}，牌：{card}")
                        choice = input(f"玩家{idx+1}是否跳牌？(y/n): ")
                        if choice.lower() == 'y':
                            player.play_a_hand(i)
                            print(f"玩家{idx+1}跳牌打出：{card}")
                            self.cur_location = idx
                            self.change_flag()
                            return True
                    # 关羽武圣跳红+2
                    if player.mr_card and any(skill.__class__.__name__ == 'WuSheng' for skill in player.mr_card.skills):
                        if card.color == 'red' and card.type == 'number' and last_card.type == 'draw2':
                            print(f"玩家{idx+1}可以用武圣跳牌！手牌序号：{i}，牌：{card}")
                            choice = input(f"玩家{idx+1}是否用武圣跳红+2？(y/n): ")
                            if choice.lower() == 'y':
                                from card import UnoCard
                                player.uno_list.pop(i)
                                new_card = UnoCard('draw2', 'red', 0)
                                self.playedcards.add_card(new_card)
                                print(f"玩家{idx+1}武圣跳牌打出：{new_card}")
                                self.cur_location = idx
                                self.change_flag()
                                return True
        return False
    def __init__(self,player_num:int,mode:str):
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
        from player import Player
        from mr_cards import all_heroes

        self.player_list.clear()
        self.player_num = len(ai_hero_names) + 1

        # 创建人类玩家
        player_mr_card = all_heroes.get(player_hero_name)
        if player_mr_card:
            p1 = Player(position=0, is_ai=False, team=player_mr_card.team)
            p1.mr_card = player_mr_card
            self.add_player(p1)

        # 创建AI玩家
        for i, hero_name in enumerate(ai_hero_names):
            other_mr_card = all_heroes.get(hero_name)
            if other_mr_card:
                p = Player(position=i + 1, is_ai=True, team=other_mr_card.team)
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
        
        # 5. 翻开第一张牌
        card = self.unocard_pack.pop()
        # 游戏开始的第一张牌没有来源
        self.playedcards.add_card(card, source_player=None)
        print(f"游戏开始，揭示的第一张牌为：{card}")

        # 6. 处理第一张牌是万能牌的情况
        if card.type in ['wild', 'wild_draw4']:
            if self.gui:
                # GUI模式下，弹出颜色选择对话框
                color = self.gui.choose_color_dialog()
                self.cur_color = color if color else random.choice(['red', 'blue', 'yellow', 'green'])
            else:
                # 非GUI模式下（例如测试），随机选择一个颜色
                self.cur_color = random.choice(['red', 'blue', 'yellow', 'green'])
                print(f"随机选择颜色: {self.cur_color}")
        else:
            self.cur_color = card.color

    #发牌！每人8张，起始玩家多一张
    def deal_cards(self):
        for i, player in enumerate(self.player_list):
            if i == self.cur_location:
                player.draw_cards(9)
            else:
                player.draw_cards(8)
    
    def execute_skill_jianxiong(self, player: Player):
        """处理奸雄技能，获得当前加牌链中的所有牌的原始牌"""
        cards_to_gain = []
        # draw_chain_cards现在存储的是(effective_card, original_card, source_player)元组
        for _, original_card, _ in self.draw_chain_cards:
            cards_to_gain.append(original_card)
            # 从弃牌堆中移除这些牌的记录
            # 注意：这里需要一个更鲁棒的方法来移除，因为playedcards.d是元组
            # 为了简化，我们假设奸雄后牌堆状态会被重置，所以暂时不从playedcards.d里移除
        
        for card in cards_to_gain:
            player.uno_list.append(card) # 直接加入手牌，绕过player_draws_cards

        message = f"玩家 {player.position+1} 发动【奸雄】，获得了以下牌: {', '.join(str(c) for c in cards_to_gain)}"
        if self.gui:
            self.gui.show_message_box("技能发动", message)
        else:
            print(message)

        # 获得牌后，检查手牌上限
        self.check_hand_limit_and_discard_if_needed(player)

        self.draw_n = 0 # 罚牌数清零
        self.draw_chain_cards.clear() # 清空加牌链
        self.turn_action_taken = True # 发动奸雄后，本回合不能再有其他动作

        # 奸雄后是自己的回合，所以不需要next_player，只需要刷新UI
        if self.gui and not self.is_discard_mode:
            self.gui.show_game_round()

    def execute_skill_wusheng(self, player, card_idx):
        """处理武圣技能"""
        original_card = player.uno_list.pop(card_idx)
        wusheng_card = UnoCard('draw2', 'red', 0)
        self.playedcards.add_card(wusheng_card)
        self.cur_color = 'red'
        self.change_flag() # 触发+2效果
        print(f"玩家 {player.position+1} 发动【武圣】，将 {original_card} 当作 {wusheng_card} 打出")

    def execute_skill(self, skill, player, *args):
        """统一的技能执行入口"""
        print(f"玩家 {player.position+1} 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            player.draw_cards(1)
            # 2. 将牌从玩家手牌给目标
            player.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            if self.gui:
                self.gui.show_message_box("反间成功", f"玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            else:
                print(f"反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")

        # 在这里添加其他技能的逻辑...

        # 检查胜利条件
        if len(player.uno_list) == 0:
            self.game_over = True
            self.gui.show_winner_and_exit(player)
            return
        if len(target.uno_list) == 0:
            self.game_over = True
            self.gui.show_winner_and_exit(target)
            return

    def execute_ai_turn(self):
        """执行AI玩家的回合"""
        player = self.player_list[self.cur_location]
        
        # AI回合开始时的检查，如果检查导致回合结束（如强制摸牌），则直接返回
        if self._ai_pre_turn_checks(player):
            return

        # 获取AI决策
        action_type, action_value = self._get_ai_action(player)
        
        # 执行AI决策
        self._execute_ai_action(player, action_type, action_value)

        # 如果游戏已经结束，则不再继续
        if self.game_over:
            return

    def _ai_pre_turn_checks(self, player):
        """AI回合开始前的检查，如是否必须摸牌。返回True表示回合已处理完毕。"""
        # 回合开始时检查手牌上限
        if len(player.uno_list) > player.hand_limit:
            num_to_discard = len(player.uno_list) - player.hand_limit
            # AI需要一个方法来决定弃掉哪些牌
            # 假设 player 对象有 choose_cards_to_discard 方法
            cards_to_discard = player.choose_cards_to_discard(num_to_discard)
            player.fold_card_objects(cards_to_discard)
            discard_info = ', '.join(str(c) for c in cards_to_discard)
            message = f"AI 玩家 {player.position+1} ({player.mr_card.name}) 回合开始时手牌超限，弃置了: {discard_info}"
            if self.gui:
                self.gui.show_message_box("AI操作", message)
            else:
                print(message)
            # 弃牌后，继续正常回合，所以不返回True

        if self.draw_n > 0 and not self.can_continue_draw_chain(player):
            jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)

            # AI 奸雄决策
            if jianxiong_skill and self.draw_chain_cards:
                last_card_in_chain = self.draw_chain_cards[-1]
                from_player = self.playedcards.get_card_source(last_card_in_chain)

                if from_player != player and self.ai_handler.decide_jianxiong(player, self.draw_chain_cards):
                    print(f"AI 玩家 {player.position+1} 发动【奸雄】")
                    self.execute_skill_jianxiong(player)
                    if self.gui:
                        self.gui.show_game_round()
                    return True # 技能发动，回合结束

            print(f"AI 玩家 {player.position+1} 无法续上加牌链，摸 {self.draw_n} 张牌")
            player.draw_cards(self.draw_n)
            self.draw_n = 0
            self.next_player()
            self.draw_chain_cards.clear() # 在确定下一位玩家后再清空加牌链
            if self.gui:
                self.gui.show_game_round()
            return True
        return False

    def _get_ai_action(self, player):
        """构造游戏状态并获取AI的决策。"""
        game_state = {
            'players': self.player_list,
            'last_card': self.playedcards.get_one(),
            'current_color': self.cur_color,
            'draw_n': self.draw_n,
            'game_direction': self.dir,
        }
        action_type, action_value = self.ai_handler.choose_action(player, game_state)
        print(f"AI ({player.mr_card.name}) 决定: {action_type} {action_value if action_value is not None else ''}")
        return action_type, action_value

    def _execute_ai_action(self, player, action_type, action_value):
        """根据AI的决策执行具体操作。"""
        played_successfully = False
        try:
            if action_type == 'play':
                # 尝试出牌，如果成功，_execute_ai_play会返回True
                played_successfully = self._execute_ai_play(player, action_value)
            # 如果AI决策是'draw'或其他，则played_successfully保持False，进入下面的摸牌逻辑
        except Exception as e:
            print(f"AI 执行时出错: {e}，改为摸牌。")
            played_successfully = False

        # 如果没有成功出牌（包括AI决策为摸牌、出牌无效、或发生错误）
        if not played_successfully:
            # 只有当轮到AI自己时，才执行自动摸牌并结束回合的逻辑
            if player.is_ai:
                player.draw_cards(1)
                self.turn_action_taken = True
                self.next_player()
                if self.gui:
                    self.gui.show_game_round()

    def _execute_ai_play(self, player, card_idx) -> bool:
        """
        执行AI出牌的具体逻辑。
        如果出牌成功，则返回 True，否则返回 False。
        """
        if card_idx >= len(player.uno_list):
            print(f"AI 决策无效 (手牌索引 {card_idx} 越界)，改为摸牌。")
            return False

        card_to_play = player.uno_list[card_idx]
        
        if player.check_card(card_to_play):
            action = PlayAction(
                card=card_to_play,
                source=player,
                target=self.get_next_player(player.position)
            )
            # process_play_action 会处理后续所有逻辑，包括next_player()和GUI刷新
            self.process_play_action(action)
            return True  # 出牌成功
        else:
            # AI决策无效，则返回False，由上层函数处理摸牌
            print(f"AI 决策无效 (牌 {card_to_play} 不符合规则)，改为摸牌。")
            return False # 出牌失败

    #结算skip
    def skip_player(self):
        if self.skip:
            self.skip = False
    #结算所有状态（处理skip和draw2/draw4的移除）
    def clear_state(self):
        self.skip_player()
        self.turn_action_taken = False
        # 重置弃牌状态
        self.is_discard_mode = False
        self.player_in_discard = None
        self.cards_to_draw_in_discard.clear()
        self.num_to_discard = 0
        # 重置GUI相关的状态
        if self.gui:
            self.gui.wusheng_active = False

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
        # 新回合开始，清理上一回合的状态
        self.clear_state()
        # 回合开始前，回合数+1
        self.turn_count += 1
        # 跳过玩家的逻辑移至回合开始时处理
        self.cur_location = (self.cur_location + self.dir) % self.player_num
        if self.gui:
            self.gui.wusheng_active = False # 每回合开始时重置武圣状态

    def handle_post_play_skills(self, player: Player, card: UnoCard):
        """处理玩家出牌后可能触发的技能"""
        # 奇袭
        qixi_skill = next((s for s in player.mr_card.skills if s.name == '奇袭'), None)
        if qixi_skill and card.color == 'green':
            if player.is_ai:
                # AI决定是否发动以及对谁发动
                target_player = self.ai_handler.decide_qixi_target(player, self.player_list)
                if target_player:
                    print(f"AI 玩家 {player.position+1} 对 {target_player.position+1} 发动【奇袭】")
                    qixi_skill(card, player, target_player)
            elif self.gui:
                # 询问人类玩家是否发动
                if self.gui.ask_yes_no_question("发动技能", "是否对一名其他角色发动【奇袭】？"):
                    # 选择目标
                    target_player = self.gui.choose_target_player_dialog(exclude_self=True)
                    if target_player:
                        qixi_skill(card, player, target_player)
                        # 更新目标玩家信息
                        if self.gui.player_widgets.get(target_player.position):
                            self.gui.player_widgets[target_player.position].update_info(
                                target_player, 
                                self.cur_location == target_player.position
                            )

    def handle_human_play(self, player, card_idx, wusheng_active):
        """
        处理人类玩家出牌的所有逻辑。
        新逻辑：此方法现在委托给 player.play()。
        """
        player.play(card_idx, wusheng_active)
        # UI刷新现在由GUI的事件处理器在调用此方法后执行

    def handle_human_draw(self, player):
        """
        处理人类玩家摸牌的所有逻辑。
        新逻辑：此方法现在委托给 player 对象。
        """
        # 检查是否可以出牌，如果可以，则不应该允许摸牌
        if player.can_play_any_card():
            if self.gui:
                self.gui.show_message_box("提示", "你有可以打出的牌，必须出牌。")
            else:
                print("你有可以打出的牌，必须出牌。")
            return

        draw_n = self.draw_n
        can_draw_chain = self.can_continue_draw_chain(player)
        
        # 情况一：被迫响应加牌链
        if draw_n > 0 and not can_draw_chain:
            player.handle_forced_draw()
        # 情况二：主动摸牌
        else:
            player.draw_cards(1)
            self.turn_action_taken = True
        # UI刷新现在由GUI的事件处理器在调用此方法后执行

    def handle_skill_fanjian(self, player):
        """处理反间技能的完整逻辑"""
        player.activate_skill('反间')
        # UI刷新现在由GUI的事件处理器在调用此方法后执行

    def get_next_player(self, current_player_pos: int) -> 'Player':
        """获取当前方向上的下一个玩家"""
        next_pos = (current_player_pos + self.dir) % self.player_num
        return self.player_list[next_pos]

    def process_play_action(self, action: PlayAction):
        """
        处理一个出牌动作的核心函数。
        所有出牌逻辑都应通过这里。
        """
        player = action.source
        original_card = action.card
        # 如果有虚拟牌（如武圣），则效果以虚拟牌为准，否则以实际牌为准
        effective_card = action.virtual_card if action.virtual_card else original_card

        # 1. 从玩家手牌中移除原始牌
        player.play_card_object(original_card)

        # 2. 将行动信息（包括生效牌和原始牌）放入弃牌堆
        self.playedcards.add_card(effective_card, player, original_card)

        # 3. 更新当前颜色（特别是万能牌）
        if effective_card.type in ['wild', 'wild_draw4']:
            if action.color_choice:
                self.cur_color = action.color_choice
            elif player.is_ai:
                self.cur_color = self.ai_handler.choose_wild_color(player)
                print(f"AI 将颜色变为 {self.cur_color}")
            else:
                # Fallback in case color is not pre-selected
                chosen_color = self.gui.choose_color_dialog()
                if chosen_color:
                    self.cur_color = chosen_color
                else: # 如果玩家取消，则随机选择一个颜色
                    self.cur_color = random.choice(['red', 'blue', 'yellow', 'green'])
        else:
            self.cur_color = effective_card.color

        # 4. 根据牌的效果更新游戏状态（如+2, +4, skip, reverse）
        self.change_flag()

        # 5. 处理出牌后可能触发的技能，传递的是原始牌
        self.handle_post_play_skills(player, original_card)

        # 6. 检查胜利条件
        if len(player.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(player)
            return # 游戏结束

        # 7. AI出牌后，自动结束回合
        if player.is_ai:
            if self.handle_jump_logic():
                self.gui.show_game_round()
                return
            self.next_player()
            if self.gui:
                self.gui.show_game_round()
        # 8. 人类玩家出牌后，不自动结束，等待“结束回合”按钮
        else:
            self.turn_action_taken = True
            # UI刷新由GUI的事件处理器负责
            # if self.gui:
            #     self.gui.show_game_round()

    def handle_jump_logic(self) -> bool:
        """
        在出牌后检查并处理跳牌逻辑。
        新逻辑：委托给每个 player 对象来检查跳牌可能性。
        返回 True 如果发生了跳牌，否则返回 False。
        """
        last_play_info = self.playedcards.get_last_play_info()
        if not last_play_info:
            return False

        last_card, _, _ = last_play_info

        # 从出牌者的下一家开始，按顺序检查所有其他玩家
        players_to_check = []
        start_pos = self.cur_location 
        current_pos = (start_pos + self.dir) % self.player_num
        while current_pos != start_pos:
            players_to_check.append(self.player_list[current_pos])
            current_pos = (current_pos + self.dir) % self.player_num

        for jumper in players_to_check:
            potential_jumps = jumper.check_for_jump(last_card)
            
            if not potential_jumps:
                continue

            # 简化逻辑：默认使用第一个可用的跳牌选项
            chosen_jump_info = potential_jumps[0] 
            
            perform_jump = False
            if jumper.is_ai:
                # AI决策逻辑 (简化：总是跳)
                perform_jump = True
            elif self.gui:
                # 人类玩家决策
                jump_card_display = str(chosen_jump_info['virtual_card'] or chosen_jump_info['original_card'])
                perform_jump = self.gui.ask_yes_no_question("发现跳牌机会", f"是否使用 {jump_card_display} 进行跳牌？")

            if perform_jump:
                original_card = chosen_jump_info['original_card']
                virtual_card = chosen_jump_info['virtual_card']
                
                self.gui.show_message_box("跳牌！", f"玩家 {jumper.position+1} ({jumper.mr_card.name}) 跳牌！")

                # 1. 重置加牌链 (如果存在)
                if self.draw_n > 0:
                    self.draw_n = 0
                    self.draw_chain_cards.clear()

                # 2. 切换当前玩家
                self.cur_location = jumper.position

                # 3. 使用 process_play_action 处理跳牌的出牌动作
                action = PlayAction(
                    card=original_card,
                    source=jumper,
                    target=self.get_next_player(jumper.position),
                    virtual_card=virtual_card
                )
                self.process_play_action(action) 
                
                return True # 跳牌发生，中断原流程

        return False

    def check_hand_limit_and_discard_if_needed(self, player: Player):
        """
        检查指定玩家的手牌是否超限，如果超限则启动弃牌流程。
        这是一个集中的处理函数，可以在任何玩家获得牌后调用。
        """
        if len(player.uno_list) > player.hand_limit:
            num_to_discard = len(player.uno_list) - player.hand_limit
            
            if player.is_ai:
                # AI 自动弃牌
                cards_to_discard = player.choose_cards_to_discard(num_to_discard)
                player.fold_card_objects(cards_to_discard)
                if self.gui:
                    discard_info = ', '.join(str(c) for c in cards_to_discard)
                    self.gui.show_temporary_message(f"AI {player.position+1} 手牌超限，弃置了: {discard_info}")
            else:
                # 人类玩家进入弃牌模式
                self.is_discard_mode = True
                self.player_in_discard = player
                self.num_to_discard = num_to_discard
                if self.gui:
                    self.gui.enter_discard_mode(player, num_to_discard)
            return True # 表示需要弃牌
        return False # 表示不需要弃牌

    def player_confirms_discard(self, player: Player, cards_to_discard: List[UnoCard]):
        """
        当人类玩家在GUI上确认弃牌后，调用此方法。
        新逻辑：只负责弃牌和清理游戏状态，不调用GUI。
        """
        if not self.is_discard_mode or player != self.player_in_discard:
            return

        # 1. 弃掉选择的牌
        player.fold_card_objects(cards_to_discard)
        
        # 2. 清理并退出弃牌模式的游戏状态
        self.is_discard_mode = False
        self.player_in_discard = None
        self.cards_to_draw_in_discard.clear()
        self.num_to_discard = 0
