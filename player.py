from __future__ import annotations
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from game import Game
    from mr_cards import MrCard
from card import UnoCard
from util import PlayAction
from PyQt5.QtWidgets import QApplication

HAND_LIMIT = 20

class Player:
    """玩家基类，定义所有玩家共有的属性和方法"""
    
    def __init__(self, position: int, team: str = None):
        self.position = position
        self.uno_list: List[UnoCard] = []
        self.game: Game = None
        self.mr_card: MrCard = None
        self.team = team
        self.uno_state = False  # 添加uno状态，当手牌为1时激活

    @property
    def hand_limit(self):
        """获取玩家的手牌上限"""
        if self.mr_card and any(s.name == '自守' for s in self.mr_card.skills):
            return 8
        return HAND_LIMIT

    def update_uno_state(self):
        """更新uno状态：当手牌为1时激活，否则关闭"""
        new_uno_state = len(self.uno_list) == 1
        if new_uno_state != self.uno_state:
            self.uno_state = new_uno_state
            # 如果状态发生变化，可以在这里添加历史记录
            if self.game and new_uno_state:
                self.game.add_history(f"{self.mr_card.name} 只剩一张手牌！")
            elif self.game and not new_uno_state and self.uno_state:
                # 从uno状态退出（手牌从1变为其他数量）
                pass

    def execute_skill_jianxiong(self):
        """统一的奸雄技能处理入口 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def execute_skill_wusheng(self, card_idx):
        """统一的武圣技能处理入口 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def execute_skill(self, skill, *args):
        """统一的技能执行入口 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def handle_jump_card_effect(self, card):
        """处理跳牌效果 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def handle_jump_skills(self, jump_card):
        """处理跳牌技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def handle_post_play_skills(self, card):
        """处理出牌后技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def player_draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """玩家摸牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def player_handle_forced_draw(self):
        """玩家处理强制摸牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def player_play(self, card_idx: int, wusheng_active: bool = False):
        """玩家出牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """摸牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def handle_forced_draw(self):
        """处理强制摸牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def play(self, card_idx: int, wusheng_active: bool = False):
        """出牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def validate_play(self, card_idx: int, wusheng_active: bool):
        """验证出牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def activate_skill(self, skill_name: str):
        """激活技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def check_for_jump(self, last_card: UnoCard) -> List:
        """检查跳牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def play_a_hand(self, i: int):
        """打出一张手牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def play_card_object(self, card: UnoCard):
        """打出卡牌对象 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def fold_card(self, indices):
        """弃牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def fold_card_objects(self, cards_to_fold: List[UnoCard]):
        """弃置卡牌对象 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def check_card(self, card: UnoCard):
        """检查卡牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def can_play_any_card(self) -> bool:
        """检查是否可以出牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def choose_cards_to_discard(self, num_to_discard: int) -> List[int]:
        """选择要弃置的卡牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def choose_to_use_skill(self, skill_name: str) -> bool:
        """选择是否使用技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")
    
    def check_hand_limit_and_discard_if_needed(self):
        """检查手牌是否超限"""
        if len(self.uno_list) >= self.hand_limit:
            if self.game and self.game.gui:
                self.game.gui.show_temporary_message(f"{self.mr_card.name} 手牌已达上限，不能再摸牌！")
            return True
        return False

    def handle_jump_logic(self) -> bool:
        """在出牌后检查并处理跳牌逻辑。返回 True 如果发生了跳牌，否则返回 False。"""
        if not self.game:
            return False
            
        last_play_info = self.game.playedcards.get_last_play_info()
        if not last_play_info:
            return False

        last_card, _, _ = last_play_info
        players_to_check = self._get_players_to_check_for_jump()

        for jumper in players_to_check:
            if self._try_player_jump(jumper, last_card):
                return True

        return False

    def _get_players_to_check_for_jump(self):
        """获取需要检查跳牌的玩家列表"""
        if not self.game:
            return []
            
        players_to_check = []
        start_pos = self.game.cur_location 
        current_pos = start_pos  # 从当前玩家开始检查
        while len(players_to_check) < self.game.player_num:  # 检查所有玩家
            players_to_check.append(self.game.player_list[current_pos])
            current_pos = (current_pos + self.game.dir) % self.game.player_num
            if current_pos == start_pos:  # 如果回到起始位置，说明已经检查完所有玩家
                break
        return players_to_check

    def _try_player_jump(self, jumper, last_card):
        """尝试让指定玩家跳牌"""
        potential_jumps = jumper.check_for_jump(last_card)
        
        if not potential_jumps:
            return False

        chosen_jump_info = potential_jumps[0] 
        perform_jump = self._decide_jump_action(jumper, chosen_jump_info)

        if perform_jump:
            self._execute_jump(jumper, chosen_jump_info)
            return True

        return False

    def _decide_jump_action(self, jumper, chosen_jump_info):
        """决定是否执行跳牌"""
        from player import AIPlayer
        if isinstance(jumper, AIPlayer):
            return True  # AI总是跳牌
        elif self.game and self.game.gui:
            jump_card_display = str(chosen_jump_info['virtual_card'] or chosen_jump_info['original_card'])
            return self.game.gui.ask_yes_no_question("发现跳牌机会", f"是否使用 {jump_card_display} 进行跳牌？")
        return False

    def _execute_jump(self, jumper, chosen_jump_info):
        """执行跳牌动作"""
        if not self.game:
            return
            
        original_card = chosen_jump_info['original_card']
        virtual_card = chosen_jump_info['virtual_card']
        
        if self.game.gui:
            self.game.gui.show_message_box("跳牌！", f"玩家 {jumper.position+1} ({jumper.mr_card.name}) 跳牌！")

        # 重置加牌链
        if self.game.draw_n > 0:
            self.game.draw_n = 0
            self.game.draw_chain_cards.clear()

        # 添加跳牌历史记录（武圣跳牌有特殊的历史记录，这里不添加通用记录）
        jump_card_for_history = virtual_card if virtual_card else original_card
        # 检查是否是武圣跳牌，如果是则不添加通用跳牌历史记录
        is_wusheng_jump = (virtual_card and virtual_card.type == 'draw2' and virtual_card.color == 'red')
        if not is_wusheng_jump:
            self.game.add_history(f"{jumper.mr_card.name} 跳 [{jump_card_for_history}]")

        # 处理跳牌后的技能效果（在出牌前）
        if virtual_card:
            jumper.handle_jump_skills(virtual_card)
        else:
            jumper.handle_jump_skills(original_card)

        # 处理跳牌的出牌动作
        from util import PlayAction
        action = PlayAction(
            card=original_card,
            source=jumper,
            target=None,  # 让process_play_action处理目标玩家
            virtual_card=virtual_card
        )

        jumper.process_play_action(action, is_jump=True, original_player_position=self.game.cur_location)

    def process_play_action(self, action, is_jump: bool = False, original_player_position: int = None):
        """处理一个出牌动作的核心函数。所有出牌逻辑都应通过这里。"""
        if not self.game:
            return
            
        original_card = action.card
        effective_card = action.virtual_card if action.virtual_card else original_card

        # 1. 从玩家手牌中移除原始牌
        self.play_card_object(original_card)

        # 2. 将行动信息放入弃牌堆（跳牌时不添加）
        if not is_jump:
            self.game.playedcards.add_card(effective_card, self, original_card)

        # 3. 更新当前颜色
        self._update_color_after_play(effective_card, action.color_choice)

        # 4. 根据牌的效果更新游戏状态
        self.game.change_flag()

        # 5. 检查胜利条件
        if self.game.check_win_condition(self):
            return

        # 6. 处理出牌后可能触发的技能（优先处理）
        if not is_jump:
            self.handle_post_play_skills(original_card)

        # 7. 出牌后的回合处理（技能处理完成后再处理）
        if is_jump:
            # 跳牌历史记录已经在_execute_jump中处理了，这里不需要重复处理
            
            # 跳牌后自动结束回合，切换到下一个玩家
            self.game.turn_action_taken = True  # 标记回合已结束
            self.game.clear_state()
            self.game.turn_count += 1
            
            # skip效果现在在回合开始时处理，这里不需要处理
            
            # +2/+4效果应该在下一个玩家回合开始时处理，这里不处理
            
            # 跳牌后再次检查跳牌
            if self.handle_jump_logic():
                return
            
            # 跳牌后，下一个玩家应该是跳牌玩家的下家
            # 跳牌逻辑由游戏主循环处理，这里只需要刷新UI
            if self.game.gui:
                self.game.gui.show_game_round()
        else:
            # 非跳牌的正常出牌逻辑
            self.game.turn_action_taken = True  # 标记回合已结束
            self.game.clear_state()
            self.game.turn_count += 1
            
            # 检查是否有玩家可以跳牌
            if self.handle_jump_logic():
                return
            
            # 没有跳牌，正常切换到下一个玩家
            # 切换玩家逻辑由游戏主循环处理，这里只需要刷新UI
            if self.game.gui:
                self.game.gui.show_game_round()

    def _update_color_after_play(self, effective_card, color_choice):
        """更新出牌后的颜色"""
        if effective_card.type in ['wild', 'wild_draw4']:
            if color_choice:
                self.game.cur_color = color_choice
            elif isinstance(self, AIPlayer):
                self.game.cur_color = self._choose_ai_wild_color()
            else:
                self.game.cur_color = self._choose_player_wild_color()
        else:
            self.game.cur_color = effective_card.color

    def _choose_player_wild_color(self):
        """玩家选择万能牌颜色"""
        if self.game and self.game.gui:
            chosen_color = self.game.gui.choose_color_dialog()
            if chosen_color:
                return chosen_color
        import random
        return random.choice(['red', 'blue', 'yellow', 'green'])



    def check_shicai_skill(self):
        """检查恃才技能（UNO提醒）"""
        if not self.mr_card:
            return
        
        shicai_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'ShiCai'), None)
        if shicai_skill:
            result = shicai_skill.check_uno(self)
            if result:
                self.game.add_history(result)
                if self.game.gui:
                    self.game.gui.show_temporary_message(result)

    def execute_turn_content(self):
        """
        执行一个玩家在一个回合内的全部内容，不包括跳牌与切换至下一个玩家
        
        这个函数包含以下步骤：
        1. 回合开始时的检查（恃才技能、手牌上限检查）
        2. 处理强制摸牌（如果有的话）
        3. 获取玩家决策（摸牌或出牌）
        4. 执行玩家决策
        5. 处理出牌后的技能效果
        6. 更新游戏状态
        
        注意：出牌/摸牌/发动技能后，回合直接结束，不需要返回T/F
        """
        # 如果游戏已经结束，则不再继续
        if self.game.game_over:
            return
            
        # 1. 回合开始时的检查
        # 检查恃才技能（UNO提醒）
        self.check_shicai_skill()
        
        # 回合开始时检查手牌上限
        if len(self.uno_list) > self.hand_limit:
            num_to_discard = len(self.uno_list) - self.hand_limit
            cards_to_discard = self.choose_cards_to_discard(num_to_discard)
            self.fold_card_objects([self.uno_list[i] for i in cards_to_discard])
            discard_info = ', '.join(str(self.uno_list[i]) for i in cards_to_discard)
            message = f"玩家 {self.position+1} ({self.mr_card.name}) 回合开始时手牌超限，弃置了: {discard_info}"
            if self.game.gui:
                self.game.gui.show_message_box("操作", message)
            else:
                print(message)

        # 2. 处理强制摸牌（如果有的话）
        if self.game.draw_n > 0:
            print(f"玩家 {self.position+1} 摸 {self.game.draw_n} 张牌 (强制摸牌)")
            
            # 显示摸牌提示
            if self.game.gui:
                self.game.gui.show_temporary_message(f"{self.mr_card.name} 摸了 {self.game.draw_n} 张牌", duration=2000)
            
            self.handle_forced_draw()
            
            # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
            jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
            jianxiong_eligible_cards = [
                original_card for effective_card, original_card, source_player in self.game.draw_chain_cards
                if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != self
            ]
            if jianxiong_skill and jianxiong_eligible_cards:
                if self.game.ai_handler.decide_jianxiong(self, self.game.draw_chain_cards):
                    print(f"玩家 {self.position+1} 发动【奸雄】")
                    self.execute_skill_jianxiong()
            
            # 清除摸牌状态
            self.game.draw_n = 0
            self.game.draw_chain_cards.clear()
            
            # 强制摸牌后，回合结束
            self.game.turn_action_taken = True
            return

        # 3. 获取玩家决策（摸牌或出牌）
        action_type, action_value = self._get_player_decision()
        
        # 4. 执行玩家决策
        self._execute_player_decision(action_type, action_value)
        
        # 如果游戏已经结束，则不再继续
        if self.game.game_over:
            return
        
        # 5. 处理出牌后的技能效果
        if action_type == 'play' and self.game.turn_action_taken:
            # 获取最后打出的牌
            last_play_info = self.game.playedcards.get_last_play_info()
            if last_play_info:
                effective_card, original_card, source_player = last_play_info
                if source_player == self:
                    self.handle_post_play_skills(effective_card)
        
        # 6. 更新游戏状态
        # 标记回合已结束
        self.game.turn_action_taken = True

    def start_turn(self):
        """
        开始玩家回合的虚函数 - 子类可以重写此方法来自定义回合开始逻辑
        
        默认实现：
        1. 执行回合内容
        2. 处理回合结束后的逻辑（如跳牌检查）
        
        注意：出牌/摸牌/发动技能后，回合直接结束，不需要返回T/F
        """
        # 执行回合内容
        self.execute_turn_content()
        
        # 如果回合已结束，处理回合结束后的逻辑
        if self.game.turn_action_taken:
            # 非跳牌的正常出牌逻辑
            self.game.turn_action_taken = True  # 标记回合已结束
            self.game.clear_state()
            self.game.turn_count += 1
            
            # 检查是否有玩家可以跳牌
            if self.handle_jump_logic():
                return
            
            # 没有跳牌，正常切换到下一个玩家
            # 切换玩家逻辑由游戏主循环处理，这里只需要刷新UI
            if self.game.gui:
                self.game.gui.show_game_round()

    def _get_player_decision(self):
        """
        获取玩家决策 - 子类需要重写
        返回：(action_type, action_value)
        - action_type: 'play' 或 'draw'
        - action_value: 如果是play，则为卡牌索引；如果是draw，则为None
        """
        raise NotImplementedError("子类必须实现此方法")

    def _execute_player_decision(self, action_type, action_value):
        """
        执行玩家决策 - 子类需要重写
        """
        raise NotImplementedError("子类必须实现此方法")


class HumanPlayer(Player):
    """人类玩家类，继承自Player基类"""
    
    def __init__(self, position: int, team: str = None):
        super().__init__(position, team)

    def start_turn(self):
        """
        人类玩家的回合开始 - 通过GUI交互处理
        
        人类玩家的回合处理与AI不同，需要通过GUI按钮触发具体的行动
        因此这里只处理回合开始时的检查，具体的行动由GUI按钮处理
        """
        # 如果游戏已经结束，则不再继续
        if self.game.game_over:
            return False
            
        # 1. 回合开始时的检查
        # 检查恃才技能（UNO提醒）
        self.check_shicai_skill()
        
        # 回合开始时检查手牌上限
        if len(self.uno_list) > self.hand_limit:
            num_to_discard = len(self.uno_list) - self.hand_limit
            cards_to_discard = self.choose_cards_to_discard(num_to_discard)
            self.fold_card_objects([self.uno_list[i] for i in cards_to_discard])
            discard_info = ', '.join(str(self.uno_list[i]) for i in cards_to_discard)
            message = f"玩家 {self.position+1} ({self.mr_card.name}) 回合开始时手牌超限，弃置了: {discard_info}"
            if self.game.gui:
                self.game.gui.show_message_box("操作", message)
            else:
                print(message)

        # 2. 处理强制摸牌（如果有的话）
        if self.game.draw_n > 0:
            print(f"玩家 {self.position+1} 摸 {self.game.draw_n} 张牌 (强制摸牌)")
            
            # 显示摸牌提示
            if self.game.gui:
                self.game.gui.show_temporary_message(f"{self.mr_card.name} 摸了 {self.game.draw_n} 张牌", duration=2000)
            
            self.handle_forced_draw()
            
            # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
            jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
            jianxiong_eligible_cards = [
                original_card for effective_card, original_card, source_player in self.game.draw_chain_cards
                if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != self
            ]
            if jianxiong_skill and jianxiong_eligible_cards:
                if self.game.ai_handler.decide_jianxiong(self, self.game.draw_chain_cards):
                    print(f"玩家 {self.position+1} 发动【奸雄】")
                    self.execute_skill_jianxiong()
            
            # 清除摸牌状态
            self.game.draw_n = 0
            self.game.draw_chain_cards.clear()
            
            # 强制摸牌后，回合结束
            self.game.turn_action_taken = True
            return

        # 对于人类玩家，回合开始后等待GUI交互
        # 具体的行动（摸牌、出牌）由GUI按钮触发
        return

    def execute_skill_jianxiong(self):
        """人类玩家奸雄技能处理"""
        cards_to_gain = []
        # draw_chain_cards现在存储的是(effective_card, original_card, source_player)元组
        for _, original_card, _ in self.game.draw_chain_cards:
            cards_to_gain.append(original_card)
        
        for card in cards_to_gain:
            self.uno_list.append(card) # 直接加入手牌，绕过player_draws_cards
        # 更新uno状态
        self.update_uno_state()

        message = f"玩家 {self.position+1} 发动【奸雄】，获得了以下牌: {', '.join(str(c) for c in cards_to_gain)}"
        if self.game.gui:
            self.game.gui.show_message_box("技能发动", message)
        else:
            print(message)
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[奸雄]，获得了 {len(cards_to_gain)} 张牌")

        # 获得牌后，检查手牌上限
        self.check_hand_limit_and_discard_if_needed()

        self.game.draw_n = 0 # 罚牌数清零
        self.game.draw_chain_cards.clear() # 清空加牌链
        # 奸雄后是自己的回合，所以不需要next_player，只需要刷新UI
        if self.game.gui and not self.game.is_discard_mode:
            self.game.gui.show_game_round()

    def execute_skill_wusheng(self, card_idx):
        """人类玩家武圣技能处理"""
        from card import UnoCard
        original_card = self.uno_list.pop(card_idx)
        # 更新uno状态
        self.update_uno_state()
        wusheng_card = UnoCard('draw2', 'red', 0)
        self.game.playedcards.add_card(wusheng_card, self, original_card)
        self.game.cur_color = 'red'
        self.game.change_flag() # 触发+2效果
        print(f"玩家 {self.position+1} 发动【武圣】，将 {original_card} 当作 {wusheng_card} 打出")
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[武圣]，将 [{original_card}] 当作 [红+2] 打出")

    def execute_skill(self, skill, *args):
        """人类玩家技能执行"""
        print(f"玩家 {self.position+1} 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            self.player_draw_cards(1, is_skill_draw=True)
            # 2. 将牌从玩家手牌给目标
            self.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            if self.game.gui:
                self.game.gui.show_message_box("反间成功", f"玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            else:
                print(f"反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            # 添加历史记录
            self.game.add_history(f"{self.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if self.game.check_win_condition(self) or self.game.check_win_condition(target):
            return

    def handle_jump_card_effect(self, card):
        """人类玩家处理跳牌时的卡片效果"""
        # 跳牌时直接应用效果，不延迟
        if card.type == "draw2":
            self.game.draw_n += 2
            self.game.draw_chain_cards.append((card, card, self))
        elif card.type == "wild_draw4":
            self.game.draw_n += 4
            self.game.draw_chain_cards.append((card, card, self))
        elif card.type == "skip":
            self.game.skip = True
        elif card.type == "reverse":
            self.game.dir *= -1
            self.game.add_history("方向倒转！")

    def handle_jump_skills(self, jump_card):
        """人类玩家处理跳牌后的技能效果"""
        if not self.mr_card:
            return
        
        # 检查奇袭技能
        qixi_skill = next((s for s in self.mr_card.skills if s.name == '奇袭'), None)
        if qixi_skill and jump_card.color == 'green':
            self._handle_player_qixi(qixi_skill, jump_card)
        
        # 检查旋风技能
        xuanfeng_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'XuanFeng'), None)
        if xuanfeng_skill:
            self._handle_player_xuanfeng(xuanfeng_skill, jump_card)
        
        # 检查散谣技能
        sanyao_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'SanYao'), None)
        if sanyao_skill:
            self._handle_player_sanyao(sanyao_skill, jump_card)

    def handle_post_play_skills(self, card):
        """人类玩家处理出牌后可能触发的技能"""
        if not self.mr_card:
            return
        
        # 奇袭技能处理
        qixi_skill = next((s for s in self.mr_card.skills if s.name == '奇袭'), None)
        if qixi_skill and card.color == 'green':
            self._handle_player_qixi(qixi_skill, card)
        
        # 集智技能处理
        jizhi_skill = next((s for s in self.mr_card.skills if s.name == '集智'), None)
        if jizhi_skill and card.type in ['draw2', 'wild_draw4', 'wild']:
            self._handle_player_jizhi(jizhi_skill, card)

    def _handle_player_qixi(self, qixi_skill, card):
        """人类玩家奇袭技能处理"""
        if self.game.gui and self.game.gui.ask_yes_no_question("发动技能", "是否对一名其他角色发动【奇袭】？"):
            target_player = self.game.gui.choose_target_player_dialog(exclude_self=True)
            if target_player:
                # 添加历史记录
                self.game.add_history(f"{self.mr_card.name} 发动[奇袭]，令玩家 {target_player.position+1} 摸了一张牌")
                qixi_skill(card, self, target_player)
                # 更新目标玩家信息
                if self.game.gui.player_widgets.get(target_player.position):
                    self.game.gui.player_widgets[target_player.position].update_info(
                        target_player, 
                        self.game.cur_location == target_player.position
                    )

    def _handle_player_jizhi(self, jizhi_skill, card):
        """人类玩家集智技能处理"""
        if len(self.uno_list) >= 2:
            if self.game.gui and self.game.gui.ask_yes_no_question("发动技能", "是否发动【集智】弃置2张牌？"):
                cards_to_discard = self.choose_cards_to_discard(2)
                if cards_to_discard:
                    for card_idx in sorted(cards_to_discard, reverse=True):
                        self.fold_card(card_idx)
                    self.game.add_history(f"{self.mr_card.name} 发动[集智]，弃置了2张牌")
                    
                    # 更新玩家信息显示
                    if self.game.gui.player_widgets.get(self.position):
                        self.game.gui.player_widgets[self.position].update_info(
                            self, 
                            self.game.cur_location == self.position
                        )

    def _handle_player_xuanfeng(self, xuanfeng_skill, jump_card):
        """人类玩家旋风技能处理"""
        # 旋风技能的具体实现
        pass

    def _handle_player_sanyao(self, sanyao_skill, jump_card):
        """人类玩家散谣技能处理"""
        # 散谣技能的具体实现
        pass

    def player_draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """人类玩家摸牌的核心逻辑"""
        if not self.game:
            return

        cards_drawn = []
        if specific_cards:
            cards_drawn = specific_cards
        elif from_deck:
            for _ in range(num_to_draw):
                # 检查手牌上限，如果已达到上限则停止摸牌
                if len(self.uno_list) >= self.hand_limit:
                    print(f"玩家 {self.position+1} ({self.mr_card.name}) 手牌已达上限({self.hand_limit})，停止摸牌。")
                    # 记录到历史：达到手牌上限，停止摸牌（技能摸牌也记录，因为这是重要的游戏状态）
                    if self.game:
                        self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，停止摸牌")
                    break
                if self.game.unocard_pack:
                    cards_drawn.append(self.game.unocard_pack.pop())
                else:
                    break
        
        if not cards_drawn:
            return

        self.uno_list.extend(cards_drawn)
        # 更新uno状态
        self.update_uno_state()
        # 只有非技能摸牌才显示print信息和历史记录
        if not is_skill_draw:
            print(f"玩家 {self.position+1} 获得了 {len(cards_drawn)} 张牌。")
            # 历史记录：摸牌（技能发动的摸牌不记录，避免重复）
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 摸了 {len(cards_drawn)} 张牌")
        # 摸牌后，立即检查手牌上限
        self.check_hand_limit_and_discard_if_needed()
        
        # 通知GUI有玩家摸牌
        if self.game:
            self.game.notify_cards_drawn(self, len(cards_drawn))
            self.game.notify_player_hand_changed(self)
            self.game.notify_draw_pile_changed()

    def player_handle_forced_draw(self):
        """人类玩家处理被动响应摸牌（例如被+2/+4）"""
        # 先完成强制摸牌（遵守手牌上限）
        actual_draw_n = min(self.game.draw_n, self.hand_limit - len(self.uno_list))
        if actual_draw_n > 0:
            self.player_draw_cards(actual_draw_n)
            # 如果实际摸牌数少于要求的摸牌数，说明达到了手牌上限
            if actual_draw_n < self.game.draw_n:
                if self.game:
                    self.game.add_history(f"{self.mr_card.name} 强制摸牌时达到手牌上限({self.hand_limit})，只摸了 {actual_draw_n} 张牌")
        else:
            # 如果已经达到手牌上限，记录到历史
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，无法强制摸牌")
        
        # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        if jianxiong_skill and self.game.draw_chain_cards:
            if self.game.gui and self.game.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                self.execute_skill_jianxiong()
        
        self.game.draw_n = 0
        self.game.draw_chain_cards.clear()

    def player_play(self, card_idx: int, wusheng_active: bool = False):
        """人类玩家主动出牌"""
        is_valid, message, card_to_play, original_card = self.validate_play(card_idx, wusheng_active)
        if not is_valid:
            if self.game.gui:
                self.game.gui.show_message_box("提示", message)
            else:
                print(message)
            return

        color_choice = None
        if card_to_play.type in ['wild', 'wild_draw4']:
            if self.game.gui:
                color_choice = self.game.gui.choose_color_dialog()
                if not color_choice:
                    return # 玩家取消选择
            else:
                color_choice = 'red' # 非GUI模式默认为红色

        # 对于reverse卡牌，需要特殊处理target_player
        if original_card.type == 'reverse':
            # 计算方向改变后的下一个玩家
            new_dir = -self.game.dir  # 方向改变后的方向
            next_pos_after_reverse = (self.position + new_dir) % self.game.player_num
            target_player = self.game.player_list[next_pos_after_reverse]
        else:
            # 获取下一个玩家，但不切换回合
            target_player = self.game.get_next_player(self.position)
        
        action = PlayAction(
            card=original_card,
            source=self,
            target=target_player,
            color_choice=color_choice,
            virtual_card=card_to_play if wusheng_active and original_card.color == 'red' else None
        )
        # 历史记录：出牌信息
        base_record = f"{self.mr_card.name} - {original_card} -> {target_player.mr_card.name}"
        self.game.add_history(base_record)
        self.game.turn_action_taken = True
        self.process_play_action(action)
        
        # 检查是否是最后一张黑色牌，如果是则摸一张
        if hasattr(self, '_last_card_is_black') and self._last_card_is_black:
            self.player_draw_cards(1)
            self.game.add_history(f"{self.mr_card.name} 打出最后一张黑色牌，摸了一张牌")
            self._last_card_is_black = False  # 重置标记

    def draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """人类玩家摸牌入口"""
        self.player_draw_cards(num_to_draw, from_deck, specific_cards, is_skill_draw)

    def handle_forced_draw(self):
        """人类玩家强制摸牌入口"""
        self.player_handle_forced_draw()

    def play(self, card_idx: int, wusheng_active: bool = False):
        """人类玩家出牌入口"""
        self.player_play(card_idx, wusheng_active)

    def validate_play(self, card_idx: int, wusheng_active: bool):
        """人类玩家出牌验证"""
        if card_idx is None or card_idx >= len(self.uno_list):
            return False, "无效的卡牌索引。", None, None

        original_card = self.uno_list[card_idx]
        card_to_play = original_card
        if wusheng_active and original_card.color == 'red':
            from card import UnoCard
            card_to_play = UnoCard('draw2', 'red', 0)

        if not self.check_card(card_to_play):
            return False, "这张牌不符合出牌规则。", None, None

        if len(self.uno_list) == 2 and self.game.gui:
            # 可以在这里添加喊UNO的逻辑
            pass

        # 最后一张牌是黑色牌的特殊处理：允许出牌，但出牌后需要摸一张
        if len(self.uno_list) == 1 and card_to_play.type in ['wild', 'wild_draw4']:
            # 标记这是最后一张黑色牌，需要在出牌后摸一张
            self._last_card_is_black = True

        return True, "有效出牌", card_to_play, original_card

    def activate_skill(self, skill_name: str):
        """人类玩家技能发动"""
        if self.game:
            # 详细历史记录
            for skill in self.mr_card.skills:
                if skill.name == skill_name:
                    if hasattr(skill, 'use'):
                        # 武圣等主动技能
                        text = skill.use(self.uno_list[0]) if self.uno_list else None
                        if text:
                            self.game.add_history(text)
                    elif hasattr(skill, 'record_history'):
                        # 反间等特殊技能
                        # 具体参数在_fanjian流程中写入
                        pass
                    elif skill_name != '缔盟':  # 缔盟技能有自己的历史记录，不需要通用描述
                        self.game.add_history(f"{self.mr_card.name} 发动[{skill_name}] 效果：{skill.description}")
        if skill_name == '反间':
            self._activate_player_fanjian()
        elif skill_name == '缔盟':
            self._activate_player_dimeng()
        # ... 其他技能可以在此添加
        else:
            if self.game.gui:
                self.game.gui.show_message_box("提示", f"技能 [{skill_name}] 的逻辑尚未完全移至Player。")

    def _activate_player_fanjian(self):
        """人类玩家反间技能处理"""
        if not self.game.gui: return

        # 1. 摸一张牌（技能发动，不写入历史记录）
        self.player_draw_cards(1, is_skill_draw=True)
        self.game.gui.show_temporary_message(f"{self.mr_card.name} 发动【反间】，摸了一张牌。")
        
        # 2. 过滤出非黑色牌供选择（反间不能给黑色牌）
        non_black_cards = [card for card in self.uno_list if card.color != 'black']
        if not non_black_cards:
            self.game.gui.show_message_box("提示", "你的手牌中没有非黑色牌，无法发动【反间】")
            return
        
        # 3. 选择要"给"的牌，而不是"打出"
        card_to_give = self.game.gui.choose_specific_card_dialog(self, non_black_cards, "请选择一张你要交给对方的【反间】牌（不能选择黑色牌）")
        if not card_to_give: return
        # 3. 选择目标
        target = self.game.gui.choose_target_player_dialog(exclude_self=True)
        if not target: return
        # 4. 结算"给牌"动作
        self.uno_list.remove(card_to_give)
        target.uno_list.append(card_to_give)
        # 更新uno状态
        self.update_uno_state()
        target.update_uno_state()
        # 5. 目标弃牌 - 弃置所有与周瑜给与的牌相同颜色的手牌
        color_to_discard = card_to_give.color
        cards_to_discard_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
        if cards_to_discard_indices:
            discarded_cards = target.fold_card(cards_to_discard_indices)
        else:
            discarded_cards = []
        # 6. 如果弃掉的手牌数量>2（即三张及以上），周瑜额外摸一张牌
        if len(discarded_cards) > 2:
            self.player_draw_cards(1, is_skill_draw=True)
            self.game.gui.show_temporary_message(f"{self.mr_card.name} 因对手弃掉{len(discarded_cards)}张牌，额外摸了一张牌。")
            # 添加到历史记录
            self.game.add_history(f"{self.mr_card.name} 因对手弃掉{len(discarded_cards)}张牌，额外摸了一张牌")
        # 详细历史记录
        for skill in self.mr_card.skills:
            if skill.name == '反间' and hasattr(skill, 'record_history'):
                text = skill.record_history(self, target, card_to_give, discarded_cards)
                if text:
                    self.game.add_history(text)
        message = f"【反间】{target.mr_card.name} 弃掉了所有 {color_to_discard} 牌" if discarded_cards else f"【反间】{target.mr_card.name} 没有 {color_to_discard} 牌可弃。"
        self.game.gui.show_temporary_message(message, duration=3000)
        # 7. 检查目标胜利条件
        if len(target.uno_list) == 0:
            self.game.game_over = True
            self.game.gui.show_winner_and_exit(target)
            return
        # 8. 技能完成，结束回合
        # 注意：反间技能完成后，回合应该结束
        self.game.turn_action_taken = True  # 标记回合结束
        self.game.next_player()  # 切换到下一个玩家
        self.game.gui.show_game_round()

    def _activate_player_dimeng(self):
        """人类玩家缔盟技能处理"""
        if not self.game.gui: return

        # 1. 检查手牌数是否大于6（技能失效条件）
        if len(self.uno_list) > 6:
            self.game.gui.show_message_box("提示", "手牌数大于6，【缔盟】技能失效")
            return

        # 2. 选择两名其他玩家
        self.game.gui.show_message_box("提示", "请选择第一个目标玩家")
        target1 = self.game.gui.choose_target_player_dialog(exclude_self=True)
        if not target1: return
        
        self.game.gui.show_message_box("提示", "请选择第二个目标玩家（不能与第一个相同）")
        target2 = self.game.gui.choose_target_player_dialog(exclude_self=True)
        if not target2 or target2 == target1: return

        # 3. 计算手牌数之差
        hand_diff = abs(len(target1.uno_list) - len(target2.uno_list))
        
        # 4. 摸x张牌（x为手牌数之差）
        if hand_diff > 0:
            self.player_draw_cards(hand_diff, is_skill_draw=True)
            self.game.gui.show_temporary_message(f"{self.mr_card.name} 发动【缔盟】，摸了 {hand_diff} 张牌")

        # 5. 交换两名目标玩家的手牌
        temp_hand = target1.uno_list.copy()
        target1.uno_list = target2.uno_list.copy()
        target2.uno_list = temp_hand
        
        # 更新uno状态（手牌交换后需要重新检查）
        target1.update_uno_state()
        target2.update_uno_state()

        # 6. 记录历史
        self.game.add_history(f"{self.mr_card.name} 发动[缔盟]，{target1.mr_card.name} 和 {target2.mr_card.name} 交换了手牌")

        # 7. 检查胜利条件
        if len(target1.uno_list) == 0:
            self.game.game_over = True
            self.game.gui.show_winner_and_exit(target1)
            return
        if len(target2.uno_list) == 0:
            self.game.game_over = True
            self.game.gui.show_winner_and_exit(target2)
            return

        # 8. 技能完成，结束回合
        # 注意：缔盟技能完成后，回合应该结束
        self.game.turn_action_taken = True  # 标记回合结束
        self.game.next_player()  # 切换到下一个玩家
        self.game.gui.show_game_round()

    def check_for_jump(self, last_card: UnoCard) -> List:
        """人类玩家跳牌检查"""
        potential_jumps = []
        if not last_card:
            return potential_jumps

        for i, card in enumerate(self.uno_list):
            # 1. 标准跳牌: 颜色、类型、数值完全一致（黑色牌不能跳牌）
            if (card.color == last_card.color and card.type == last_card.type and card.value == last_card.value and 
                card.type not in ['wild', 'wild_draw4']):
                potential_jumps.append({'original_card': card, 'virtual_card': None})

            # 2. 武圣跳牌:  红色牌 跳 红色+2
            if last_card.type == 'draw2' and last_card.color == 'red':
                if self.mr_card and any(s.name == '武圣' for s in self.mr_card.skills):
                    if card.color == 'red' and card.type not in ['wild', 'wild_draw4']:
                        from card import UnoCard # 确保 UnoCard 被导入
                        virtual_card = UnoCard('draw2', 'red', 0)
                        potential_jumps.append({'original_card': card, 'virtual_card': virtual_card})
        
        return potential_jumps

    def play_a_hand(self, i: int):
        """人类玩家打牌"""
        card = self.uno_list.pop(i)
        # 更新uno状态
        self.update_uno_state()
        return card

    def play_card_object(self, card: UnoCard):
        """人类玩家打牌对象"""
        try:
            self.uno_list.remove(card)
            # 更新uno状态
            self.update_uno_state()
            # 通知GUI有玩家出牌
            if self.game:
                self.game.notify_card_played(self, card)
                self.game.notify_player_hand_changed(self)
        except ValueError:
            # 静默处理，不显示错误对话框
            pass

    def fold_card(self, indices):
        """人类玩家弃牌"""
        # 确保indices是列表
        if not isinstance(indices, list):
            indices = [indices]
        
        # 从大到小排序，防止删除时索引变化
        indices.sort(reverse=True)
        cards_folded = []
        for i in indices:
            if i < len(self.uno_list):
                cards_folded.append(self.uno_list.pop(i))
        # 更新uno状态
        self.update_uno_state()
        return cards_folded

    def fold_card_objects(self, cards_to_fold: List[UnoCard]):
        """人类玩家根据卡牌对象弃牌"""
        cards_folded = []
        for card in cards_to_fold:
            try:
                self.uno_list.remove(card)
                cards_folded.append(card)
            except ValueError:
                if self.game and self.game.gui:
                    self.game.gui.show_message_box("警告", f"尝试弃掉不存在的牌 {card}")
                else:
                    print(f"警告: 尝试弃掉不存在的牌 {card}")
        return cards_folded

    def check_card(self, card: UnoCard):
        """人类玩家卡牌检查"""
        last_card = self.game.playedcards.get_one()
        cur_color = self.game.cur_color
        
        # 检查+2/+4叠加规则：只有在draw_n > 0时才应用
        if self.game.draw_n > 0 and last_card:
            if last_card.type == 'draw2':
                # +2上只能叠+2或+4
                if card.type not in ['draw2', 'wild_draw4']:
                    return False
            elif last_card.type == 'wild_draw4':
                # +4上只能叠+4
                if card.type != 'wild_draw4':
                    return False
        
        # 检查倾国技能
        if self.mr_card:
            qingguo_skill = next((s for s in self.mr_card.skills if s.name == '倾国'), None)
            if qingguo_skill and card.color == 'blue':
                return True # 蓝色牌可以当任何颜色出

            # 检查龙胆技能
            longdan_skill = next((s for s in self.mr_card.skills if s.name == '龙胆'), None)
            if longdan_skill:
                if card.color == 'red' and cur_color == 'blue':
                    return True
                if card.color == 'blue' and cur_color == 'red':
                    return True

        if card.type == 'wild' or card.type == 'wild_draw4':
            return True
        if card.color == cur_color:
            return True
        if last_card and card.type == last_card.type and card.type != 'number':
            return True
        if last_card and card.type == 'number' and last_card.type == 'number' and card.value == last_card.value:
            return True
        return False

    def can_play_any_card(self) -> bool:
        """人类玩家检查手牌中是否有任何可以合法打出的牌"""
        for card in self.uno_list:
            if self.check_card(card):
                return True
        return False

    def choose_cards_to_discard(self, num_to_discard: int) -> List[int]:
        """人类玩家选择要弃置的牌（返回牌在uno_list中的索引列表）"""
        if len(self.uno_list) < num_to_discard:
            return None
        
        if self.game.gui:
            return self.game.gui.choose_cards_to_discard_dialog(self, num_to_discard)
        else:
            # 命令行模式下的简单实现
            print(f"请选择 {num_to_discard} 张牌来弃置（输入牌的位置，用空格分隔）：")
            for i, card in enumerate(self.uno_list):
                print(f"{i}: {card}")
            try:
                indices = list(map(int, input().split()))
                if len(indices) == num_to_discard and all(0 <= i < len(self.uno_list) for i in indices):
                    return indices
            except:
                pass
            return None

    def choose_to_use_skill(self, skill_name: str) -> bool:
        """人类玩家选择是否使用技能"""
        if self.game and self.game.gui:
            return self.game.gui.choose_to_use_skill_dialog(self, skill_name)
        else:
            # 命令行模式下的简单实现
            print(f"是否使用技能 {skill_name}？(y/n): ")
            return input().lower().startswith('y')

    def _get_player_decision(self):
        """
        获取人类玩家决策
        返回：(action_type, action_value)
        - action_type: 'play' 或 'draw'
        - action_value: 如果是play，则为卡牌索引；如果是draw，则为None
        """
        if self.game and self.game.gui:
            # GUI模式下，决策由GUI处理，这里返回默认值
            # 实际的决策逻辑在GUI中实现
            return 'draw', None
        else:
            # 命令行模式下的简单实现
            print(f"玩家 {self.position+1} 的手牌:")
            for i, card in enumerate(self.uno_list):
                print(f"{i}: {card}")
            
            print("选择操作: 1-摸牌, 2-出牌")
            choice = input().strip()
            
            if choice == '1':
                return 'draw', None
            elif choice == '2':
                print("选择要出的牌索引:")
                try:
                    card_idx = int(input())
                    if 0 <= card_idx < len(self.uno_list):
                        return 'play', card_idx
                except ValueError:
                    pass
            return 'draw', None

    def _execute_player_decision(self, action_type, action_value):
        """
        执行人类玩家决策
        """
        if action_type == 'play':
            try:
                self.play(action_value)
                # 出牌成功后设置行动标志
                self.game.turn_action_taken = True
            except Exception as e:
                print(f"出牌失败: {e}")
                # 出牌失败时摸牌
                if self.game.draw_n > 0:
                    self.handle_forced_draw()
                    self._check_jianxiong_after_draw()
                    self.game.draw_n = 0
                    self.game.draw_chain_cards.clear()
                else:
                    self.draw_cards(1)
        else:
            # 摸牌
            if self.game.draw_n > 0:
                self.handle_forced_draw()
                self.game._check_jianxiong_after_draw(self)
                self.game.draw_n = 0
                self.game.draw_chain_cards.clear()
            else:
                self.draw_cards(1)
            
class AIPlayer(Player):
    """AI玩家类，继承自Player基类，只负责执行AI决策"""
    
    def __init__(self, position: int, team: str = None):
        super().__init__(position, team)

    def execute_skill_jianxiong(self):
        """AI玩家奸雄技能处理"""
        cards_to_gain = []
        # draw_chain_cards现在存储的是(effective_card, original_card, source_player)元组
        for _, original_card, _ in self.game.draw_chain_cards:
            cards_to_gain.append(original_card)
        
        for card in cards_to_gain:
            self.uno_list.append(card) # 直接加入手牌，绕过player_draws_cards
        # 更新uno状态
        self.update_uno_state()

        message = f"AI 玩家 {self.position+1} ({self.mr_card.name}) 发动【奸雄】，获得了以下牌: {', '.join(str(c) for c in cards_to_gain)}"
        print(message)
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[奸雄]，获得了 {len(cards_to_gain)} 张牌")

        # 获得牌后，检查手牌上限
        self.check_hand_limit_and_discard_if_needed()

        self.game.draw_n = 0 # 罚牌数清零
        self.game.draw_chain_cards.clear() # 清空加牌链

    def execute_skill_wusheng(self, card_idx):
        """AI玩家武圣技能处理"""
        from card import UnoCard
        original_card = self.uno_list.pop(card_idx)
        # 更新uno状态
        self.update_uno_state()
        wusheng_card = UnoCard('draw2', 'red', 0)
        self.game.playedcards.add_card(wusheng_card, self, original_card)
        self.game.cur_color = 'red'
        self.game.change_flag() # 触发+2效果
        print(f"AI 玩家 {self.position+1} ({self.mr_card.name}) 发动【武圣】，将 {original_card} 当作 {wusheng_card} 打出")
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[武圣]，将 [{original_card}] 当作 [红+2] 打出")

    def execute_skill(self, skill, *args):
        """AI玩家技能执行"""
        print(f"AI 玩家 {self.position+1} ({self.mr_card.name}) 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            self.player_draw_cards(1, is_skill_draw=True)
            # 2. 将牌从玩家手牌给目标
            self.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            print(f"AI反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            # 添加历史记录
            self.game.add_history(f"{self.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if self.game.check_win_condition(self) or self.game.check_win_condition(target):
            return

    def handle_jump_card_effect(self, card):
        """AI玩家处理跳牌时的卡片效果"""
        # 跳牌时直接应用效果，不延迟
        if card.type == "draw2":
            self.game.draw_n += 2
            self.game.draw_chain_cards.append((card, card, self))
        elif card.type == "wild_draw4":
            self.game.draw_n += 4
            self.game.draw_chain_cards.append((card, card, self))
        elif card.type == "skip":
            self.game.skip = True
        elif card.type == "reverse":
            self.game.dir *= -1
            self.game.add_history("方向倒转！")

    def handle_jump_skills(self, jump_card):
        """AI玩家处理跳牌后的技能效果"""
        if not self.mr_card:
            return
        
        # 检查奇袭技能
        qixi_skill = next((s for s in self.mr_card.skills if s.name == '奇袭'), None)
        if qixi_skill and jump_card.color == 'green':
            self._handle_ai_qixi(qixi_skill, jump_card)
        
        # 检查旋风技能
        xuanfeng_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'XuanFeng'), None)
        if xuanfeng_skill:
            self._handle_ai_xuanfeng(xuanfeng_skill, jump_card)
        
        # 检查三要技能
        sanyao_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'SanYao'), None)
        if sanyao_skill:
            self._handle_ai_sanyao(sanyao_skill, jump_card)

    def handle_post_play_skills(self, card):
        """AI玩家处理出牌后的技能效果"""
        if not self.mr_card:
            return
        
        # 检查机智技能
        jizhi_skill = next((s for s in self.mr_card.skills if s.name == '机智'), None)
        if jizhi_skill and card.type == 'number':
            self._handle_ai_jizhi(jizhi_skill, card)

    def _handle_ai_qixi(self, qixi_skill, card):
        """AI奇袭技能处理"""
        # 使用AI处理器选择目标
        target_player = self.game.ai_handler.decide_qixi_target(self, self.game.player_list)
        if target_player and target_player != self:
            # 执行奇袭技能
            self.game.execute_skill_qixi(self, target_player)

    def _handle_ai_jizhi(self, jizhi_skill, card):
        """AI机智技能处理"""
        # 机智技能：出数字牌后摸一张牌
        self.player_draw_cards(1, is_skill_draw=True)
        print(f"AI 玩家 {self.position+1} ({self.mr_card.name}) 发动【机智】，摸了1张牌")
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[机智]，摸了1张牌")

    def _handle_ai_xuanfeng(self, xuanfeng_skill, jump_card):
        """AI旋风技能处理"""
        # 旋风技能：跳绿色牌后摸一张牌
        self.player_draw_cards(1, is_skill_draw=True)
        print(f"AI 玩家 {self.position+1} ({self.mr_card.name}) 发动【旋风】，摸了1张牌")
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[旋风]，摸了1张牌")

    def _handle_ai_sanyao(self, sanyao_skill, jump_card):
        """AI三要技能处理"""
        # 三要技能：跳牌后摸一张牌
        self.player_draw_cards(1, is_skill_draw=True)
        print(f"AI 玩家 {self.position+1} ({self.mr_card.name}) 发动【三要】，摸了1张牌")
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[三要]，摸了1张牌")

    # AI玩家使用基类的通用方法，不需要重写
    def player_draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """AI玩家摸牌"""
        if not self.game:
            return

        cards_drawn = []
        if specific_cards:
            cards_drawn = specific_cards
        elif from_deck:
            for _ in range(num_to_draw):
                # 检查手牌上限，如果已达到上限则停止摸牌
                if len(self.uno_list) >= self.hand_limit:
                    print(f"AI玩家 {self.position+1} ({self.mr_card.name}) 手牌已达上限({self.hand_limit})，停止摸牌。")
                    # 记录到历史：达到手牌上限，停止摸牌（技能摸牌也记录，因为这是重要的游戏状态）
                    if self.game:
                        self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，停止摸牌")
                    break
                if self.game.unocard_pack:
                    cards_drawn.append(self.game.unocard_pack.pop())
                else:
                    break
        
        if not cards_drawn:
            return

        self.uno_list.extend(cards_drawn)
        # 更新uno状态
        self.update_uno_state()
        # 只有非技能摸牌才显示print信息和历史记录
        if not is_skill_draw:
            print(f"AI玩家 {self.position+1} 获得了 {len(cards_drawn)} 张牌。")
            # 历史记录：摸牌（技能发动的摸牌不记录，避免重复）
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 摸了 {len(cards_drawn)} 张牌")
        # 摸牌后，立即检查手牌上限
        self.check_hand_limit_and_discard_if_needed()
        
        # 通知GUI有玩家摸牌
        if self.game:
            self.game.notify_cards_drawn(self, len(cards_drawn))
            self.game.notify_player_hand_changed(self)
            self.game.notify_draw_pile_changed()

    def player_handle_forced_draw(self):
        """AI玩家处理被动响应摸牌（例如被+2/+4）"""
        # 先完成强制摸牌（遵守手牌上限）
        actual_draw_n = min(self.game.draw_n, self.hand_limit - len(self.uno_list))
        if actual_draw_n > 0:
            self.player_draw_cards(actual_draw_n)
            # 如果实际摸牌数少于要求的摸牌数，说明达到了手牌上限
            if actual_draw_n < self.game.draw_n:
                if self.game:
                    self.game.add_history(f"{self.mr_card.name} 强制摸牌时达到手牌上限({self.hand_limit})，只摸了 {actual_draw_n} 张牌")
        else:
            # 如果已经达到手牌上限，记录到历史
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，无法强制摸牌")
        
        # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        if jianxiong_skill and self.game.draw_chain_cards:
            # AI决策是否发动奸雄
            if self.game.ai_handler.decide_jianxiong(self, self.game.draw_chain_cards):
                self.execute_skill_jianxiong()
        
        self.game.draw_n = 0
        self.game.draw_chain_cards.clear()

    def player_play(self, card_idx: int, wusheng_active: bool = False):
        """AI玩家主动出牌"""
        is_valid, message, card_to_play, original_card = self.validate_play(card_idx, wusheng_active)
        if not is_valid:
            print(f"AI出牌无效: {message}")
            return

        # 使用AI处理器选择颜色
        color_choice = self.game.ai_handler.choose_wild_color(self) if card_to_play.type in ['wild', 'wild_draw4'] else None

        # 对于reverse卡牌，需要特殊处理target_player
        if original_card.type == 'reverse':
            # 计算方向改变后的下一个玩家
            new_dir = -self.game.dir  # 方向改变后的方向
            next_pos_after_reverse = (self.position + new_dir) % self.game.player_num
            target_player = self.game.player_list[next_pos_after_reverse]
        else:
            # 获取下一个玩家，但不切换回合
            target_player = self.game.get_next_player(self.position)
        
        from util import PlayAction
        action = PlayAction(
            card=original_card,
            source=self,
            target=target_player,
            color_choice=color_choice,
            virtual_card=card_to_play if wusheng_active and original_card.color == 'red' else None
        )
        # 历史记录：出牌信息
        base_record = f"{self.mr_card.name} - {original_card} -> {target_player.mr_card.name}"
        self.game.add_history(base_record)
        self.game.turn_action_taken = True
        self.process_play_action(action)

    def _choose_ai_wild_color(self):
        """AI选择万能牌颜色"""
        # 使用AI处理器选择颜色
        return self.game.ai_handler.choose_wild_color(self)

    # 使用基类的通用方法
    def draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """AI玩家摸牌"""
        self.player_draw_cards(num_to_draw, from_deck, specific_cards, is_skill_draw)

    def handle_forced_draw(self):
        """AI玩家处理强制摸牌"""
        self.player_handle_forced_draw()

    def play(self, card_idx: int, wusheng_active: bool = False):
        """AI玩家出牌"""
        self.player_play(card_idx, wusheng_active)

    def validate_play(self, card_idx: int, wusheng_active: bool):
        """AI玩家出牌验证"""
        if card_idx is None or card_idx >= len(self.uno_list):
            return False, "无效的卡牌索引。", None, None

        original_card = self.uno_list[card_idx]
        card_to_play = original_card
        if wusheng_active and original_card.color == 'red':
            from card import UnoCard
            card_to_play = UnoCard('draw2', 'red', 0)

        if not self.check_card(card_to_play):
            return False, "这张牌不符合出牌规则。", None, None

        # 最后一张牌是黑色牌的特殊处理：允许出牌，但出牌后需要摸一张
        if len(self.uno_list) == 1 and card_to_play.type in ['wild', 'wild_draw4']:
            # 标记这是最后一张黑色牌，需要在出牌后摸一张
            self._last_card_is_black = True

        return True, "有效出牌", card_to_play, original_card

    def activate_skill(self, skill_name: str):
        """AI玩家技能发动"""
        if self.game:
            # 详细历史记录
            for skill in self.mr_card.skills:
                if skill.name == skill_name:
                    if hasattr(skill, 'use'):
                        # 武圣等主动技能
                        text = skill.use(self.uno_list[0]) if self.uno_list else None
                        if text:
                            self.game.add_history(text)
                    elif hasattr(skill, 'record_history'):
                        # 反间等特殊技能
                        # 具体参数在_fanjian流程中写入
                        pass
                    elif skill_name != '缔盟':  # 缔盟技能有自己的历史记录，不需要通用描述
                        self.game.add_history(f"{self.mr_card.name} 发动[{skill_name}] 效果：{skill.description}")
        
        # 使用AI处理器决定是否使用技能
        if self.game.ai_handler.ai_choose_to_use_skill(self, skill_name):
            if skill_name == '反间':
                self._activate_ai_fanjian()
            elif skill_name == '缔盟':
                self._activate_ai_dimeng()
            # ... 其他技能可以在此添加
        else:
            print(f"AI技能 [{skill_name}] 的逻辑尚未完全移至Player。")

    def _activate_ai_fanjian(self):
        """AI反间技能处理"""
        # 使用AI处理器选择卡牌和目标
        non_black_cards = [card for card in self.uno_list if card.color != 'black']
        if not non_black_cards:
            print(f"AI {self.mr_card.name} 没有非黑色牌，无法发动【反间】")
            return
        
        # 选择一张非黑色牌（AI选择第一张）
        card_to_give = non_black_cards[0]
        
        # 选择目标（AI选择手牌最少的对手）
        opponents = [p for p in self.game.player_list if p != self]
        if not opponents:
            print(f"AI {self.mr_card.name} 没有可选择的对手")
            return
        
        target = min(opponents, key=lambda p: len(p.uno_list))
        
        # 结算"给牌"动作
        self.uno_list.remove(card_to_give)
        target.uno_list.append(card_to_give)
        # 更新uno状态
        self.update_uno_state()
        target.update_uno_state()
        
        # 目标弃牌 - 弃置所有与周瑜给与的牌相同颜色的手牌
        color_to_discard = card_to_give.color
        cards_to_discard_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
        if cards_to_discard_indices:
            discarded_cards = target.fold_card(cards_to_discard_indices)
        else:
            discarded_cards = []
        
        # 如果弃掉的手牌数量>2（即三张及以上），周瑜额外摸一张牌
        if len(discarded_cards) > 2:
            self.player_draw_cards(1, is_skill_draw=True)
            print(f"AI {self.mr_card.name} 因对手弃掉{len(discarded_cards)}张牌，额外摸了一张牌。")
            # 添加到历史记录
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 因对手弃掉{len(discarded_cards)}张牌，额外摸了一张牌")
        
        # 记录历史
        message = f"AI {self.mr_card.name} 发动【反间】，将 {card_to_give} 给了 {target.mr_card.name}"
        print(message)
        if self.game:
            self.game.add_history(f"{self.mr_card.name} 发动[反间]，将 [{card_to_give}] 给了 {target.mr_card.name}")
        
        # 检查目标胜利条件
        if len(target.uno_list) == 0:
            self.game.game_over = True
            if self.game.gui:
                self.game.gui.show_winner_and_exit(target)
            return
        
        # 技能完成，结束回合
        # 注意：反间技能完成后，回合应该结束
        self.game.turn_action_taken = True  # 标记回合结束
        self.game.next_player()  # 切换到下一个玩家
        if self.game.gui:
            self.game.gui.show_game_round()

    def _activate_ai_dimeng(self):
        """AI缔盟技能处理"""
        # 1. 检查手牌数是否大于6（技能失效条件）
        if len(self.uno_list) > 6:
            print(f"AI {self.mr_card.name} 手牌数大于6，【缔盟】技能失效")
            return

        # 2. 选择两名其他玩家（AI选择手牌数差异最大的两个对手）
        opponents = [p for p in self.game.player_list if p != self]
        if len(opponents) < 2:
            print(f"AI {self.mr_card.name} 没有足够的对手，无法发动【缔盟】")
            return
        
        # 选择手牌数差异最大的两个对手
        opponents.sort(key=lambda p: len(p.uno_list))
        target1 = opponents[0]  # 手牌最少的
        target2 = opponents[-1]  # 手牌最多的

        # 3. 计算手牌数之差
        hand_diff = abs(len(target1.uno_list) - len(target2.uno_list))
        
        # 4. 摸x张牌（x为手牌数之差）
        if hand_diff > 0:
            self.player_draw_cards(hand_diff, is_skill_draw=True)
            print(f"AI {self.mr_card.name} 发动【缔盟】，摸了 {hand_diff} 张牌")

        # 5. 交换两名目标玩家的手牌
        temp_hand = target1.uno_list.copy()
        target1.uno_list = target2.uno_list.copy()
        target2.uno_list = temp_hand
        
        # 更新uno状态（手牌交换后需要重新检查）
        target1.update_uno_state()
        target2.update_uno_state()

        # 6. 记录历史
        message = f"AI {self.mr_card.name} 发动【缔盟】，{target1.mr_card.name} 和 {target2.mr_card.name} 交换了手牌"
        print(message)
        if self.game:
            self.game.add_history(f"{self.mr_card.name} 发动[缔盟]，{target1.mr_card.name} 和 {target2.mr_card.name} 交换了手牌")

        # 7. 检查胜利条件
        if len(target1.uno_list) == 0:
            self.game.game_over = True
            if self.game.gui:
                self.game.gui.show_winner_and_exit(target1)
            return
        if len(target2.uno_list) == 0:
            self.game.game_over = True
            if self.game.gui:
                self.game.gui.show_winner_and_exit(target2)
            return

        # 8. 技能完成，结束回合
        # 注意：缔盟技能完成后，回合应该结束
        self.game.turn_action_taken = True  # 标记回合结束
        self.game.next_player()  # 切换到下一个玩家
        if self.game.gui:
            self.game.gui.show_game_round()

    # 使用基类的通用方法，不需要重写
    def check_for_jump(self, last_card: UnoCard) -> List:
        """AI玩家检查跳牌"""
        potential_jumps = []
        if not last_card:
            return potential_jumps

        for i, card in enumerate(self.uno_list):
            # 1. 标准跳牌: 颜色、类型、数值完全一致（黑色牌不能跳牌）
            if (card.color == last_card.color and card.type == last_card.type and card.value == last_card.value and 
                card.type not in ['wild', 'wild_draw4']):
                potential_jumps.append({'original_card': card, 'virtual_card': None})

            # 2. 武圣跳牌:  红色牌 跳 红色+2
            if last_card.type == 'draw2' and last_card.color == 'red':
                if self.mr_card and any(s.name == '武圣' for s in self.mr_card.skills):
                    if card.color == 'red' and card.type not in ['wild', 'wild_draw4']:
                        from card import UnoCard # 确保 UnoCard 被导入
                        virtual_card = UnoCard('draw2', 'red', 0)
                        potential_jumps.append({'original_card': card, 'virtual_card': virtual_card})
        
        return potential_jumps

    def play_a_hand(self, i: int):
        """AI玩家打牌"""
        card = self.uno_list.pop(i)
        # 更新uno状态
        self.update_uno_state()
        return card

    def play_card_object(self, card: UnoCard):
        """AI玩家打牌对象"""
        try:
            self.uno_list.remove(card)
            # 更新uno状态
            self.update_uno_state()
        except ValueError:
            # 静默处理，不显示错误信息
            pass

    def fold_card(self, indices):
        """AI玩家弃牌"""
        # 从大到小排序，防止删除时索引变化
        indices.sort(reverse=True)
        cards_folded = []
        for i in indices:
            if i < len(self.uno_list):
                cards_folded.append(self.uno_list.pop(i))
        # 更新uno状态
        self.update_uno_state()
        return cards_folded

    def fold_card_objects(self, cards_to_fold: List[UnoCard]):
        """AI根据卡牌对象弃牌"""
        cards_folded = []
        for card in cards_to_fold:
            try:
                self.uno_list.remove(card)
                cards_folded.append(card)
            except ValueError:
                print(f"警告: AI尝试弃掉不存在的牌 {card}")
        return cards_folded

    def check_card(self, card: UnoCard):
        """AI玩家卡牌检查"""
        last_card = self.game.playedcards.get_one()
        cur_color = self.game.cur_color
        
        # 检查+2/+4叠加规则：只有在draw_n > 0时才应用
        if self.game.draw_n > 0 and last_card:
            if last_card.type == 'draw2':
                # +2上只能叠+2或+4
                if card.type not in ['draw2', 'wild_draw4']:
                    return False
            elif last_card.type == 'wild_draw4':
                # +4上只能叠+4
                if card.type != 'wild_draw4':
                    return False
        
        # 检查倾国技能
        if self.mr_card:
            qingguo_skill = next((s for s in self.mr_card.skills if s.name == '倾国'), None)
            if qingguo_skill and card.color == 'blue':
                return True # 蓝色牌可以当任何颜色出

            # 检查龙胆技能
            longdan_skill = next((s for s in self.mr_card.skills if s.name == '龙胆'), None)
            if longdan_skill:
                if card.color == 'red' and cur_color == 'blue':
                    return True
                if card.color == 'blue' and cur_color == 'red':
                    return True

        if card.type == 'wild' or card.type == 'wild_draw4':
            return True
        if card.color == cur_color:
            return True
        if last_card and card.type == last_card.type and card.type != 'number':
            return True
        if last_card and card.type == 'number' and last_card.type == 'number' and card.value == last_card.value:
            return True
        return False

    def can_play_any_card(self) -> bool:
        """AI检查手牌中是否有任何可以合法打出的牌"""
        for card in self.uno_list:
            if self.check_card(card):
                return True
        return False

    def choose_cards_to_discard(self, num_to_discard: int) -> List[int]:
        """AI选择要弃置的牌的逻辑。简单策略：优先弃置高点数数字牌。"""
        # 按点数降序排序，优先保留功能牌和低点数牌
        sorted_hand = sorted(self.uno_list, key=lambda c: c.value if c.type == 'number' else -1, reverse=True)
        selected_indices = []
        
        # 选择前num_to_discard张牌
        for i, card in enumerate(self.uno_list):
            if len(selected_indices) >= num_to_discard:
                break
            if card in sorted_hand[:num_to_discard]:
                selected_indices.append(i)
        
        return selected_indices if len(selected_indices) == num_to_discard else None

    def choose_to_use_skill(self, skill_name: str) -> bool:
        """AI玩家选择是否使用技能"""
        # 使用AI处理器决定是否使用技能
        return self.game.ai_handler.ai_choose_to_use_skill(self, skill_name)

    def _get_player_decision(self):
        """
        获取AI玩家决策
        返回：(action_type, action_value)
        - action_type: 'play' 或 'draw'
        - action_value: 如果是play，则为卡牌索引；如果是draw，则为None
        """
        # 使用AI处理器获取决策
        game_state = {
            'players': self.game.player_list,
            'last_card': self.game.playedcards.get_one(),
            'current_color': self.game.cur_color,
            'draw_n': self.game.draw_n,
            'game_direction': self.game.dir,
        }
        action_type, action_value = self.game.ai_handler.choose_action(self, game_state)
        print(f"AI ({self.mr_card.name}) 决定: {action_type} {action_value if action_value is not None else ''}")
        return action_type, action_value

    def _execute_player_decision(self, action_type, action_value):
        """
        执行AI玩家决策
        """
        if action_type == 'play':
            try:
                self.play(action_value)
                # AI出牌成功后设置行动标志
                self.game.turn_action_taken = True
            except Exception as e:
                print(f"AI出牌失败: {e}")
                # 出牌失败时摸牌
                if self.game.draw_n > 0:
                    self.handle_forced_draw()
                    self._check_jianxiong_after_draw()
                    self.game.draw_n = 0
                    self.game.draw_chain_cards.clear()
                else:
                    self.draw_cards(1)
        else:
            # 摸牌
            if self.game.draw_n > 0:
                self.handle_forced_draw()
                self._check_jianxiong_after_draw()
                self.game.draw_n = 0
                self.game.draw_chain_cards.clear()
            else:
                self.draw_cards(1)
        
    def check_hand_limit_and_discard_if_needed(self):
        """检查手牌上限并在必要时弃牌"""
        if len(self.uno_list) > self.hand_limit:
            num_to_discard = len(self.uno_list) - self.hand_limit
            cards_to_discard_indices = self.choose_cards_to_discard(num_to_discard)
            if cards_to_discard_indices:
                cards_to_discard = [self.uno_list[i] for i in cards_to_discard_indices]
                self.fold_card_objects(cards_to_discard)
                discard_info = ', '.join(str(c) for c in cards_to_discard)
                message = f"玩家 {self.position+1} 手牌超限，弃置了: {discard_info}"
                if self.game.gui:
                    self.game.gui.show_message_box("手牌超限", message)
                else:
                    print(message)

    def _check_jianxiong_after_draw(self):
        """摸牌后检查奸雄技能"""
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        jianxiong_eligible_cards = [
            original_card for effective_card, original_card, source_player in self.game.draw_chain_cards
            if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != self
        ]
        
        if jianxiong_skill and jianxiong_eligible_cards:
            if isinstance(self, AIPlayer):
                if self.game.ai_handler.decide_jianxiong(self, self.game.draw_chain_cards):
                    self.execute_skill_jianxiong()
            else:
                if self.game.gui and self.game.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                    self.execute_skill_jianxiong()
        