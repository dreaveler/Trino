from player import Player
from typing import List, Callable
from card import UnoCard
from util import PlayedCards, PlayAction
import random
from ai import AI, AIPlayer
from PyQt5.QtWidgets import QMessageBox

#胜利条件
class Game:
    def check_jump(self):
        """统一的跳牌检查入口，根据玩家类型调用对应函数"""
        return self._check_jump_internal()

    def _check_jump_internal(self):
        """跳牌检查内部实现"""
        # 跳牌逻辑：遍历所有玩家，查找能跳牌的玩家（除当前玩家）
        last_card = self.playedcards.get_one()
        for idx, player in enumerate(self.player_list):
            if idx == self.cur_location:
                continue
            for i, card in enumerate(player.uno_list):
                # 普通跳牌（黑色牌不能跳牌）
                if (card.color == last_card.color and card.type == last_card.type and card.value == last_card.value and 
                    card.type not in ['wild', 'wild_draw4']):
                    if player.is_ai:
                        return self._handle_ai_jump(player, i, card, idx)
                    else:
                        return self._handle_player_jump(player, i, card, idx)
                # 关羽武圣跳红+2
                if player.mr_card and any(skill.__class__.__name__ == 'WuSheng' for skill in player.mr_card.skills):
                    if card.color == 'red' and card.type == 'number' and last_card.type == 'draw2':
                        if player.is_ai:
                            return self._handle_ai_wusheng_jump(player, i, card, idx)
                        else:
                            return self._handle_player_wusheng_jump(player, i, card, idx)
        return False

    def _handle_ai_jump(self, player, card_idx, card, player_idx):
        """AI普通跳牌处理"""
        print(f"AI玩家{player_idx+1}可以跳牌！手牌序号：{card_idx}，牌：{card}")
        # AI总是选择跳牌
        # 从手牌移除卡牌（不进入playedcards）
        played_card = player.play_a_hand(card_idx)
        print(f"AI玩家{player_idx+1}跳牌打出：{played_card}")
        self.cur_location = player_idx
        # 处理跳牌后的技能效果
        self._handle_jump_skills(player, played_card)
        # 跳牌时，+2/+4牌的效果延迟到下一个玩家回合开始时处理
        self._handle_jump_card_effect(played_card)
        return True

    def _handle_player_jump(self, player, card_idx, card, player_idx):
        """玩家普通跳牌处理"""
        print(f"玩家{player_idx+1}可以跳牌！手牌序号：{card_idx}，牌：{card}")
        
        # GUI模式下使用对话框，非GUI模式下使用控制台输入
        if self.gui:
            choice = self.gui.ask_yes_no_question("跳牌", f"是否跳牌打出 {card}？")
        else:
            choice = input(f"玩家{player_idx+1}是否跳牌？(y/n): ")
            choice = choice.lower() == 'y'
        
        if choice:
            # 从手牌移除卡牌（不进入playedcards）
            played_card = player.play_a_hand(card_idx)
            print(f"玩家{player_idx+1}跳牌打出：{played_card}")
            self.cur_location = player_idx
            # 处理跳牌后的技能效果
            self._handle_jump_skills(player, played_card)
            # 跳牌时，+2/+4牌的效果延迟到下一个玩家回合开始时处理
            self._handle_jump_card_effect(played_card)
            return True
        return False

    def _handle_ai_wusheng_jump(self, player, card_idx, card, player_idx):
        """AI武圣跳牌处理"""
        print(f"AI玩家{player_idx+1}可以用武圣跳牌！手牌序号：{card_idx}，牌：{card}")
        # AI总是选择武圣跳牌
        from card import UnoCard
        player.uno_list.pop(card_idx)
        new_card = UnoCard('draw2', 'red', 0)
        self.playedcards.add_card(new_card)
        print(f"AI玩家{player_idx+1}武圣跳牌打出：{new_card}")
        # 添加武圣跳牌历史记录（在跳牌动作执行后）
        history_text = f"{player.mr_card.name} 发动武圣将红色牌作为红+2打出从而干扰跳牌"
        print(f"添加历史记录: {history_text}")
        self.add_history(history_text)
        self.cur_location = player_idx
        # 处理跳牌后的技能效果
        self._handle_jump_skills(player, new_card)
        # 跳牌时，+2/+4牌的效果延迟到下一个玩家回合开始时处理
        self._handle_jump_card_effect(new_card)
        return True

    def _handle_player_wusheng_jump(self, player, card_idx, card, player_idx):
        """玩家武圣跳牌处理"""
        print(f"玩家{player_idx+1}可以用武圣跳牌！手牌序号：{card_idx}，牌：{card}")
        
        # GUI模式下使用对话框，非GUI模式下使用控制台输入
        if self.gui:
            choice = self.gui.ask_yes_no_question("武圣跳牌", f"是否用武圣将 {card} 当作红+2打出？")
        else:
            choice = input(f"玩家{player_idx+1}是否用武圣跳红+2？(y/n): ")
            choice = choice.lower() == 'y'
        
        if choice:
            from card import UnoCard
            player.uno_list.pop(card_idx)
            new_card = UnoCard('draw2', 'red', 0)
            self.playedcards.add_card(new_card)
            print(f"玩家{player_idx+1}武圣跳牌打出：{new_card}")
            # 添加武圣跳牌历史记录
            self.add_history(f"{player.mr_card.name} 发动武圣将红色牌作为红+2打出从而干扰跳牌")
            self.cur_location = player_idx
            # 处理跳牌后的技能效果
            self._handle_jump_skills(player, new_card)
            # 跳牌时，+2/+4牌的效果延迟到下一个玩家回合开始时处理
            self._handle_jump_card_effect(new_card)
            return True
        return False

    def _handle_jump_card_effect(self, card):
        """处理跳牌时的卡片效果，延迟到下一个玩家回合开始时"""
        if card.type == "draw2" or card.type == "wild_draw4":
            # 对于+2/+4牌，不立即增加draw_n，而是标记为延迟效果
            # 这个效果将在下一个玩家回合开始时通过_pre_turn_checks处理
            from card import UnoCard
            # 创建延迟效果记录：(effective_card, original_card, source_player)
            effective_card = UnoCard(card.type, card.color, card.value)
            original_card = UnoCard(card.type, card.color, card.value)
            source_player = self.player_list[self.cur_location]
            self.pending_jump_draw_effect.append((effective_card, original_card, source_player))
        elif card.type == "skip":
            self.skip = True
        elif card.type == "reverse":
            self.dir *= -1
        # 注意：这里不调用change_flag()，因为+2/+4的效果要延迟处理

    def _handle_jump_skills(self, player, jump_card):
        """处理跳牌后的技能效果"""
        if not player.mr_card:
            return
        
        # 检查旋风技能
        xuanfeng_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'XuanFeng'), None)
        if xuanfeng_skill:
            if player.is_ai:
                self._handle_ai_xuanfeng(player, xuanfeng_skill, jump_card)
            else:
                self._handle_player_xuanfeng(player, xuanfeng_skill, jump_card)
        
        # 检查散谣技能
        sanyao_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'SanYao'), None)
        if sanyao_skill:
            if player.is_ai:
                self._handle_ai_sanyao(player, sanyao_skill, jump_card)
            else:
                self._handle_player_sanyao(player, sanyao_skill, jump_card)

    def _handle_ai_xuanfeng(self, player, xuanfeng_skill, jump_card):
        """AI旋风技能处理"""
        # AI总是发动旋风技能
        result = xuanfeng_skill(jump_card, player)
        if result:
            self.add_history(result)

    def _handle_player_xuanfeng(self, player, xuanfeng_skill, jump_card):
        """玩家旋风技能处理"""
        # 直接调用技能，技能内部会处理选择逻辑
        result = xuanfeng_skill(jump_card, player)
        if result:
            self.add_history(result)

    def _handle_ai_sanyao(self, player, sanyao_skill, jump_card):
        """AI散谣技能处理"""
        # AI选择手牌最少的对手作为目标
        opponents = [p for p in self.player_list if p != player]
        if opponents:
            target = min(opponents, key=lambda p: len(p.uno_list))
            result = sanyao_skill(jump_card, player, target)
            if result:
                self.add_history(result)

    def _handle_player_sanyao(self, player, sanyao_skill, jump_card):
        """玩家散谣技能处理"""
        # 让玩家选择目标
        if player.game and player.game.gui:
            target = player.game.gui.choose_target_player_dialog(exclude_self=True)
            if target:
                result = sanyao_skill(jump_card, player, target)
                if result:
                    self.add_history(result)

    def _check_shicai_skill(self, player):
        """检查恃才技能（UNO提醒）"""
        if not player.mr_card:
            return
        
        shicai_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'ShiCai'), None)
        if shicai_skill:
            result = shicai_skill.check_uno(player)
            if result:
                self.add_history(result)
                if self.gui:
                    self.gui.show_temporary_message(result)

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

        # 延迟的+2/+4效果（用于跳牌）
        self.pending_jump_draw_effect: List[tuple] = []

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
    def execute_skill_jianxiong(self, player: Player):
        """统一的奸雄技能处理入口，根据玩家类型调用对应函数"""
        if player.is_ai:
            self._execute_ai_skill_jianxiong(player)
        else:
            self._execute_player_skill_jianxiong(player)

    def _execute_ai_skill_jianxiong(self, player: Player):
        """AI奸雄技能处理"""
        cards_to_gain = []
        # draw_chain_cards现在存储的是(effective_card, original_card, source_player)元组
        for _, original_card, _ in self.draw_chain_cards:
            cards_to_gain.append(original_card)
        
        for card in cards_to_gain:
            player.uno_list.append(card) # 直接加入手牌，绕过player_draws_cards

        message = f"AI 玩家 {player.position+1} ({player.mr_card.name}) 发动【奸雄】，获得了以下牌: {', '.join(str(c) for c in cards_to_gain)}"
        print(message)
        # 添加历史记录
        self.add_history(f"{player.mr_card.name} 发动[奸雄]，获得了 {len(cards_to_gain)} 张牌")

        # 获得牌后，检查手牌上限
        self.check_hand_limit_and_discard_if_needed(player)

        self.draw_n = 0 # 罚牌数清零
        self.draw_chain_cards.clear() # 清空加牌链

    def _execute_player_skill_jianxiong(self, player: Player):
        """玩家奸雄技能处理"""
        cards_to_gain = []
        # draw_chain_cards现在存储的是(effective_card, original_card, source_player)元组
        for _, original_card, _ in self.draw_chain_cards:
            cards_to_gain.append(original_card)
        
        for card in cards_to_gain:
            player.uno_list.append(card) # 直接加入手牌，绕过player_draws_cards

        message = f"玩家 {player.position+1} 发动【奸雄】，获得了以下牌: {', '.join(str(c) for c in cards_to_gain)}"
        if self.gui:
            self.gui.show_message_box("技能发动", message)
        else:
            print(message)
        # 添加历史记录
        self.add_history(f"{player.mr_card.name} 发动[奸雄]，获得了 {len(cards_to_gain)} 张牌")

        # 获得牌后，检查手牌上限
        self.check_hand_limit_and_discard_if_needed(player)

        self.draw_n = 0 # 罚牌数清零
        self.draw_chain_cards.clear() # 清空加牌链
        # 奸雄后是自己的回合，所以不需要next_player，只需要刷新UI
        if self.gui and not self.is_discard_mode:
            self.gui.show_game_round()

    def execute_skill_wusheng(self, player, card_idx):
        """统一的武圣技能处理入口，根据玩家类型调用对应函数"""
        if player.is_ai:
            self._execute_ai_skill_wusheng(player, card_idx)
        else:
            self._execute_player_skill_wusheng(player, card_idx)

    def _execute_ai_skill_wusheng(self, player, card_idx):
        """AI武圣技能处理"""
        original_card = player.uno_list.pop(card_idx)
        wusheng_card = UnoCard('draw2', 'red', 0)
        self.playedcards.add_card(wusheng_card, player, original_card)
        self.cur_color = 'red'
        self.change_flag() # 触发+2效果
        print(f"AI 玩家 {player.position+1} ({player.mr_card.name}) 发动【武圣】，将 {original_card} 当作 {wusheng_card} 打出")
        # 添加历史记录
        self.add_history(f"{player.mr_card.name} 发动[武圣]，将 [{original_card}] 当作 [红+2] 打出")

    def _execute_player_skill_wusheng(self, player, card_idx):
        """玩家武圣技能处理"""
        original_card = player.uno_list.pop(card_idx)
        wusheng_card = UnoCard('draw2', 'red', 0)
        self.playedcards.add_card(wusheng_card, player, original_card)
        self.cur_color = 'red'
        self.change_flag() # 触发+2效果
        print(f"玩家 {player.position+1} 发动【武圣】，将 {original_card} 当作 {wusheng_card} 打出")
        # 添加历史记录
        self.add_history(f"{player.mr_card.name} 发动[武圣]，将 [{original_card}] 当作 [红+2] 打出")

    def execute_skill(self, skill, player, *args):
        """统一的技能执行入口，根据玩家类型调用对应函数"""
        if player.is_ai:
            self._execute_ai_skill(skill, player, *args)
        else:
            self._execute_player_skill(skill, player, *args)

    def _execute_ai_skill(self, skill, player, *args):
        """AI技能执行"""
        print(f"AI 玩家 {player.position+1} ({player.mr_card.name}) 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            AIPlayer.ai_draw_cards(player, 1, is_skill_draw=True)
            # 2. 将牌从玩家手牌给目标
            player.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            print(f"AI反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            # 添加历史记录
            self.add_history(f"{player.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if len(player.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(player)
            return
        if len(target.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(target)
            return

    def _execute_player_skill(self, skill, player, *args):
        """玩家技能执行"""
        print(f"玩家 {player.position+1} 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            player.player_draw_cards(1, is_skill_draw=True)
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
            # 添加历史记录
            self.add_history(f"{player.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if len(player.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(player)
            return
        if len(target.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(target)
            return

    # ==================== AI回合处理函数 ====================
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
        # 首先处理延迟的+2/+4效果（来自跳牌）
        if self.pending_jump_draw_effect:
            for effective_card, original_card, source_player in self.pending_jump_draw_effect:
                # 将延迟效果添加到正常的draw_chain_cards中
                self.draw_chain_cards.append((effective_card, original_card, source_player))
                # 增加draw_n
                if effective_card.type == "draw2":
                    self.draw_n += 2
                elif effective_card.type == "wild_draw4":
                    self.draw_n += 4
            # 清空延迟效果
            self.pending_jump_draw_effect.clear()
        
        # 检查恃才技能（UNO提醒）
        self._check_shicai_skill(player)
        
        # 回合开始时检查手牌上限
        if len(player.uno_list) > player.hand_limit:
            num_to_discard = len(player.uno_list) - player.hand_limit
            cards_to_discard = AIPlayer.ai_choose_cards_to_discard(player, num_to_discard)
            player.fold_card_objects(cards_to_discard)
            discard_info = ', '.join(str(c) for c in cards_to_discard)
            message = f"AI 玩家 {player.position+1} ({player.mr_card.name}) 回合开始时手牌超限，弃置了: {discard_info}"
            if self.gui:
                self.gui.show_message_box("AI操作", message)
            else:
                print(message)

        if self.draw_n > 0: # If there's any pending draw penalty
            # Perform the forced draw
            print(f"AI 玩家 {player.position+1} 摸 {self.draw_n} 张牌 (强制摸牌)")
            
            # 显示AI摸牌提示
            if self.gui:
                self.gui.show_temporary_message(f"{player.mr_card.name} 摸了 {self.draw_n} 张牌", duration=2000)
            
            player.handle_forced_draw() # This performs the actual draw based on draw_n and hand_limit
            
            # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
            jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
            jianxiong_eligible_cards = [
                original_card for effective_card, original_card, source_player in self.draw_chain_cards
                if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != player
            ]
            if jianxiong_skill and jianxiong_eligible_cards:
                if self.ai_handler.decide_jianxiong(player, self.draw_chain_cards):
                    print(f"AI 玩家 {player.position+1} 发动【奸雄】")
                    self.execute_skill_jianxiong(player)
            
            # Clear draw state after handling forced draw and potential JianXiong
            self.draw_n = 0
            self.draw_chain_cards.clear()
            self.next_player() # End turn after forced draw
            if self.gui:
                self.gui.show_game_round()
            return True
        return False

    # ==================== AI决策处理函数 ====================
    def _get_ai_action(self, player):
        """统一的AI决策获取入口，根据玩家类型调用对应函数"""
        if player.is_ai:
            return self._get_ai_action_internal(player)
        else:
            return self._get_player_action(player)

    def _get_ai_action_internal(self, player):
        """AI决策获取内部实现"""
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

    def _get_player_action(self, player):
        """玩家决策获取 - 由GUI处理，这里返回默认值"""
        # 玩家的决策由GUI处理，这里只是占位
        return 'draw', None

    def _execute_ai_action(self, player, action_type, action_value):
        """统一的AI决策执行入口，根据玩家类型调用对应函数"""
        if player.is_ai:
            self._execute_ai_action_internal(player, action_type, action_value)
        else:
            self._execute_player_action(player, action_type, action_value)

    def _execute_ai_action_internal(self, player, action_type, action_value):
        """AI决策执行内部实现"""
        played_successfully = False
        try:
            if action_type == 'play':
                played_successfully = self._execute_ai_play(player, action_value)
        except Exception as e:
            print(f"AI 执行时出错: {e}，改为摸牌。")
            played_successfully = False

        # 如果没有成功出牌（包括AI决策为摸牌、出牌无效、或发生错误）
        if not played_successfully:
            if self.draw_n > 0: # If there's any pending draw penalty
                # AI chooses to take the penalty.
                
                # 显示AI强制摸牌提示
                if self.gui:
                    self.gui.show_temporary_message(f"{player.mr_card.name} 摸了 {self.draw_n} 张牌", duration=2000)
                
                player.handle_forced_draw() # This performs the actual draw based on draw_n and hand_limit
                
                # After drawing, check for JianXiong
                jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
                jianxiong_eligible_cards = [
                    original_card for effective_card, original_card, source_player in self.draw_chain_cards
                    if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != player
                ]

                if jianxiong_skill and jianxiong_eligible_cards:
                    if self.ai_handler.decide_jianxiong(player, self.draw_chain_cards):
                        self.execute_skill_jianxiong(player) # This method will gain the cards from draw_chain_cards

                # Clear draw state after handling forced draw and potential JianXiong
                self.draw_n = 0
                self.draw_chain_cards.clear()
            else: # Voluntary draw (draw_n == 0)
                # 显示AI主动摸牌提示
                if self.gui:
                    self.gui.show_temporary_message(f"{player.mr_card.name} 摸了 1 张牌", duration=2000)
                
                AIPlayer.ai_draw_cards(player, 1)
            
            self.next_player()
            if self.gui:
                self.gui.show_game_round()

    def _execute_ai_play(self, player, card_idx):
        """AI出牌执行"""
        try:
            AIPlayer.ai_play(player, card_idx)
            return True
        except Exception as e:
            print(f"AI出牌失败: {e}")
            return False

    def _execute_player_action(self, player, action_type, action_value):
        """玩家决策执行 - 由GUI处理，这里只是占位"""
        # 玩家的决策执行由GUI处理，这里只是占位
        pass

    # ==================== 玩家回合处理函数 ====================
    def execute_player_turn(self):
        """执行玩家回合 - 由GUI事件触发，这里只是占位"""
        pass

    def _player_pre_turn_checks(self, player):
        """玩家回合开始前的检查，如是否必须摸牌。返回True表示回合已处理完毕。"""
        # 首先处理延迟的+2/+4效果（来自跳牌）
        if self.pending_jump_draw_effect:
            for effective_card, original_card, source_player in self.pending_jump_draw_effect:
                # 将延迟效果添加到正常的draw_chain_cards中
                self.draw_chain_cards.append((effective_card, original_card, source_player))
                # 增加draw_n
                if effective_card.type == "draw2":
                    self.draw_n += 2
                elif effective_card.type == "wild_draw4":
                    self.draw_n += 4
            # 清空延迟效果
            self.pending_jump_draw_effect.clear()
        
        # 检查恃才技能（UNO提醒）
        self._check_shicai_skill(player)
        
        if self.draw_n > 0: # If there's any pending draw penalty
            # Perform the forced draw
            print(f"玩家 {player.position+1} 摸 {self.draw_n} 张牌 (强制摸牌)")
            
            # 显示玩家强制摸牌提示
            if self.gui:
                self.gui.show_temporary_message(f"{player.mr_card.name} 摸了 {self.draw_n} 张牌", duration=2000)
            
            player.handle_forced_draw() # This performs the actual draw based on draw_n and hand_limit
            
            # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
            jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
            jianxiong_eligible_cards = [
                original_card for effective_card, original_card, source_player in self.draw_chain_cards
                if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != player
            ]
            if jianxiong_skill and jianxiong_eligible_cards:
                if self.gui and self.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                    self.execute_skill_jianxiong(player)
            
            # Clear draw state after handling forced draw and potential JianXiong
            self.draw_n = 0
            self.draw_chain_cards.clear()
            self.next_player() # End turn after forced draw
            if self.gui:
                self.gui.show_game_round()
            return True
        return False

    def handle_player_play(self, player, card_idx, wusheng_active):
        """处理玩家出牌"""
        player.player_play(card_idx, wusheng_active)

    def handle_player_draw(self, player):
        """处理玩家摸牌"""
        if self.draw_n > 0: # If there's any pending draw penalty
            # Player chooses to take the penalty.
            
            # 显示玩家强制摸牌提示
            if self.gui:
                self.gui.show_temporary_message(f"{player.mr_card.name} 摸了 {self.draw_n} 张牌", duration=2000)
            
            player.handle_forced_draw() # This performs the actual draw based on draw_n and hand_limit
            
            # After drawing, check for JianXiong
            jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
            jianxiong_eligible_cards = [
                original_card for effective_card, original_card, source_player in self.draw_chain_cards
                if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != player
            ]

            if jianxiong_skill and jianxiong_eligible_cards:
                if self.gui and self.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                    self.execute_skill_jianxiong(player) # This method will gain the cards from draw_chain_cards

            # Clear draw state after handling forced draw and potential JianXiong
            self.draw_n = 0
            self.draw_chain_cards.clear()
        else: # Voluntary draw (draw_n == 0)
            player.player_draw_cards(1)
        
        self.turn_action_taken = True # Drawing counts as an action
        if self.gui:
            self.gui.show_game_round()
        self.next_player() # End turn after drawing (voluntary or forced)

    def handle_player_skill(self, player, skill_name):
        """处理玩家技能"""
        if skill_name == '反间':
            player.activate_skill('反间')
        # 其他技能可以在这里添加

    def handle_skill_fanjian(self, player):
        """处理反间技能的统一入口"""
        player.activate_skill('反间')

    #结算所有状态（处理skip和draw2/draw4的移除）
    def clear_state(self):
        # 重置弃牌状态
        self.is_discard_mode = False
        self.player_in_discard = None
        self.cards_to_draw_in_discard.clear()
        self.num_to_discard = 0
        # 清空延迟的+2/+4效果
        self.pending_jump_draw_effect.clear()
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
        # 新回合开始，重置行动标志
        self.turn_action_taken = False
        # 新回合开始，清理上一回合的状态
        self.clear_state()
        # 回合开始前，回合数+1
        self.turn_count += 1

        # 正常切换到下一个玩家
        self.cur_location = (self.cur_location + self.dir) % self.player_num

        # 检查是否需要跳过这个刚刚轮到的玩家
        if self.skip:
            skipped_player = self.player_list[self.cur_location] # 这是要被跳过的玩家
            # 记录跳过历史
            self.add_history(f"{skipped_player.mr_card.name} 被跳过！")
            if self.gui:
                # 在GUI中显示跳过信息
                self.gui.show_temporary_message(f"玩家 {skipped_player.position + 1} ({skipped_player.mr_card.name}) 被跳过！")
            
            self.skip = False # 消耗skip状态
            
            # 再次切换，实现跳过
            self.cur_location = (self.cur_location + self.dir) % self.player_num

        if self.gui:
            self.gui.wusheng_active = False # 每回合开始时重置武圣状态

    # ==================== 技能处理函数 ====================
    def handle_post_play_skills(self, player: Player, card: UnoCard):
        """处理出牌后可能触发的技能，传递的是原始牌"""
        # 奇袭技能处理
        qixi_skill = next((s for s in player.mr_card.skills if s.name == '奇袭'), None)
        if qixi_skill and card.color == 'green':
            if player.is_ai:
                self._handle_ai_qixi(player, qixi_skill, card)
            else:
                self._handle_player_qixi(player, qixi_skill, card)
        
        # 集智技能处理
        jizhi_skill = next((s for s in player.mr_card.skills if s.name == '集智'), None)
        if jizhi_skill and card.type in ['draw2', 'wild_draw4', 'wild']:
            if player.is_ai:
                self._handle_ai_jizhi(player, jizhi_skill, card)
            else:
                self._handle_player_jizhi(player, jizhi_skill, card)

    def _handle_ai_qixi(self, player, qixi_skill, card):
        """AI奇袭技能处理"""
        target_player = self.ai_handler.decide_qixi_target(player, self.player_list)
        if target_player:
            print(f"AI 玩家 {player.position+1} 对 {target_player.position+1} 发动【奇袭】")
            # 添加历史记录
            self.add_history(f"{player.mr_card.name} 发动[奇袭]，令玩家 {target_player.position+1} 摸了一张牌")
            qixi_skill(card, player, target_player)

    def _handle_player_qixi(self, player, qixi_skill, card):
        """玩家奇袭技能处理"""
        if self.gui and self.gui.ask_yes_no_question("发动技能", "是否对一名其他角色发动【奇袭】？"):
            target_player = self.gui.choose_target_player_dialog(exclude_self=True)
            if target_player:
                # 添加历史记录
                self.add_history(f"{player.mr_card.name} 发动[奇袭]，令玩家 {target_player.position+1} 摸了一张牌")
                qixi_skill(card, player, target_player)
                # 更新目标玩家信息
                if self.gui.player_widgets.get(target_player.position):
                    self.gui.player_widgets[target_player.position].update_info(
                        target_player, 
                        self.cur_location == target_player.position
                    )

    def _handle_ai_jizhi(self, player, jizhi_skill, card):
        """AI集智技能处理"""
        if len(player.uno_list) >= 2:
            # AI选择要弃置的牌
            cards_to_discard = AIPlayer.ai_choose_cards_to_discard(player, 2)
            if cards_to_discard:
                # 找到这些牌在玩家手牌中的索引
                indices_to_discard = []
                for card_to_discard in cards_to_discard:
                    try:
                        idx = player.uno_list.index(card_to_discard)
                        indices_to_discard.append(idx)
                    except ValueError:
                        continue
                
                # 从大到小排序索引，防止删除时索引变化
                indices_to_discard.sort(reverse=True)
                for card_idx in indices_to_discard:
                    player.fold_card(card_idx)
                
                print(f"AI 玩家 {player.position+1} 发动【集智】，弃置了2张牌")
                self.add_history(f"{player.mr_card.name} 发动[集智]，弃置了2张牌")

    def _handle_player_jizhi(self, player, jizhi_skill, card):
        """玩家集智技能处理"""
        if len(player.uno_list) >= 2:
            if self.gui and self.gui.ask_yes_no_question("发动技能", "是否发动【集智】弃置2张牌？"):
                cards_to_discard = player.choose_cards_to_discard(2)
                if cards_to_discard:
                    for card_idx in sorted(cards_to_discard, reverse=True):
                        player.fold_card(card_idx)
                    self.add_history(f"{player.mr_card.name} 发动[集智]，弃置了2张牌")
                    # 更新玩家信息显示
                    if self.gui.player_widgets.get(player.position):
                        self.gui.player_widgets[player.position].update_info(
                            player, 
                            self.cur_location == player.position
                        )

    # ==================== 统一处理函数 ====================
    def handle_play(self, player, card_idx, wusheng_active):
        """统一的出牌处理入口"""
        if player.is_ai:
            AIPlayer.ai_play(player, card_idx, wusheng_active)
        else:
            player.player_play(card_idx, wusheng_active)

    def handle_draw(self, player):
        """统一的摸牌处理入口"""
        if player.is_ai:
            if self.draw_n > 0: # If there's any pending draw penalty
                # AI chooses to take the penalty.
                player.handle_forced_draw() # This performs the actual draw based on draw_n and hand_limit
                
                # After drawing, check for JianXiong
                jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
                jianxiong_eligible_cards = [
                    original_card for effective_card, original_card, source_player in self.draw_chain_cards
                    if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != player
                ]

                if jianxiong_skill and jianxiong_eligible_cards:
                    if self.ai_handler.decide_jianxiong(player, self.draw_chain_cards):
                        self.execute_skill_jianxiong(player) # This method will gain the cards from draw_chain_cards

                # Clear draw state after handling forced draw and potential JianXiong
                self.draw_n = 0
                self.draw_chain_cards.clear()
            else: # Voluntary draw (draw_n == 0)
                AIPlayer.ai_draw_cards(player, 1)
            
            self.next_player()
            if self.gui:
                self.gui.show_game_round()
        else:
            if self.draw_n > 0: # If there's any pending draw penalty
                # Player chooses to take the penalty.
                player.handle_forced_draw() # This performs the actual draw based on draw_n and hand_limit
                
                # After drawing, check for JianXiong
                jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
                jianxiong_eligible_cards = [
                    original_card for effective_card, original_card, source_player in self.draw_chain_cards
                    if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != player
                ]

                if jianxiong_skill and jianxiong_eligible_cards:
                    if self.gui and self.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                        self.execute_skill_jianxiong(player) # This method will gain the cards from draw_chain_cards

                # Clear draw state after handling forced draw and potential JianXiong
                self.draw_n = 0
                self.draw_chain_cards.clear()
            else: # Voluntary draw (draw_n == 0)
                player.player_draw_cards(1)
            
            self.turn_action_taken = True # Drawing counts as an action
            if self.gui:
                self.gui.show_game_round()
            self.next_player() # End turn after drawing (voluntary or forced)

    def handle_skill(self, player, skill_name):
        """统一的技能处理入口"""
        if player.is_ai:
            # AI技能处理逻辑
            if skill_name == '反间':
                # AI反间逻辑可以在这里添加
                pass
        else:
            # 玩家技能处理
            if skill_name == '反间':
                player.activate_skill('反间')

    def get_next_player(self, current_player_pos: int) -> 'Player':
        """获取当前方向上的下一个玩家"""
        next_pos = (current_player_pos + self.dir) % self.player_num
        return self.player_list[next_pos]

    # ==================== 出牌处理函数 ====================
    def process_play_action(self, action: PlayAction, is_jump: bool = False):
        """处理一个出牌动作的核心函数。所有出牌逻辑都应通过这里。"""
        player = action.source
        original_card = action.card
        effective_card = action.virtual_card if action.virtual_card else original_card

        # 1. 从玩家手牌中移除原始牌
        player.play_card_object(original_card)

        # 2. 将行动信息放入弃牌堆（跳牌时不添加）
        if not is_jump:
            self.playedcards.add_card(effective_card, player, original_card)

        # 3. 更新当前颜色
        self._update_color_after_play(player, effective_card, action.color_choice)

        # 4. 根据牌的效果更新游戏状态
        self.change_flag()

        # 5. 检查胜利条件
        if len(player.uno_list) == 0:
            self.game_over = True
            if self.gui:
                self.gui.show_winner_and_exit(player)
            return

        # 6. 出牌后的回合处理（包括跳牌历史记录）
        self._handle_post_play_turn_logic(player, is_jump)

        # 7. 处理出牌后可能触发的技能（在跳牌历史记录之后）
        # 注意：跳牌时的技能已经在_execute_jump中处理过了
        if not is_jump:
            self.handle_post_play_skills(player, original_card)

    def _update_color_after_play(self, player, effective_card, color_choice):
        """更新出牌后的颜色"""
        if effective_card.type in ['wild', 'wild_draw4']:
            if color_choice:
                self.cur_color = color_choice
            elif player.is_ai:
                self.cur_color = self._choose_ai_wild_color(player)
            else:
                self.cur_color = self._choose_player_wild_color()
        else:
            self.cur_color = effective_card.color

    def _choose_ai_wild_color(self, player):
        """AI选择万能牌颜色"""
        color = self.ai_handler.choose_wild_color(player)
        print(f"AI 将颜色变为 {color}")
        return color

    def _choose_player_wild_color(self):
        """玩家选择万能牌颜色"""
        if self.gui:
            chosen_color = self.gui.choose_color_dialog()
            if chosen_color:
                return chosen_color
        return random.choice(['red', 'blue', 'yellow', 'green'])

    def _handle_post_play_turn_logic(self, player, is_jump):
        """处理出牌后的回合逻辑"""
        if is_jump:
            # 跳牌历史记录已经在_execute_jump中处理了，这里不需要重复处理
            
            # 跳牌后直接切换到跳牌玩家的下家
            self.cur_location = (self.cur_location + self.dir) % self.player_num
            self.turn_action_taken = False
            self.clear_state()
            self.turn_count += 1
            # 跳牌后检查新玩家的强制摸牌
            self._check_forced_draw_after_jump()
            if self.gui:
                self.gui.show_game_round()
            # 跳牌后再次检查跳牌
            self._check_jump_after_jump()
            return
            
            # 跳牌后直接切换到跳牌玩家的下家
            self.cur_location = (self.cur_location + self.dir) % self.player_num
            self.turn_action_taken = False
            self.clear_state()
            self.turn_count += 1
            # 跳牌后检查新玩家的强制摸牌
            self._check_forced_draw_after_jump()
            if self.gui:
                self.gui.show_game_round()
            # 跳牌后再次检查跳牌
            self._check_jump_after_jump()
            return

        # 检查跳牌
        if self.handle_jump_logic():
            return

        # 检查是否打出了reverse牌，如果是则记录方向倒转历史
        last_play_info = self.playedcards.get_last_play_info()
        if last_play_info and last_play_info[0].type == "reverse":
            # 记录方向倒转历史
            self.add_history("方向倒转！")
            # reverse已经在change_flag()中改变了方向，让正常的回合逻辑处理下一个玩家

        # 根据玩家类型处理回合结束
        if player.is_ai:
            self.next_player()
            if self.gui:
                self.gui.show_game_round()
        elif not self.turn_action_taken:
            self.next_player()
            if self.gui:
                self.gui.show_game_round()

    # ==================== 跳牌处理函数 ====================
    def handle_jump_logic(self) -> bool:
        """在出牌后检查并处理跳牌逻辑。返回 True 如果发生了跳牌，否则返回 False。"""
        last_play_info = self.playedcards.get_last_play_info()
        if not last_play_info:
            return False

        last_card, _, _ = last_play_info
        players_to_check = self._get_players_to_check_for_jump()

        for jumper in players_to_check:
            if self._try_player_jump(jumper, last_card):
                return True

        return False

    def handle_jump_logic_except_current(self) -> bool:
        """在跳牌后检查并处理跳牌逻辑（排除当前玩家）。返回 True 如果发生了跳牌，否则返回 False。"""
        last_play_info = self.playedcards.get_last_play_info()
        if not last_play_info:
            return False

        last_card, _, _ = last_play_info
        players_to_check = self._get_players_to_check_for_jump_except_current()

        for jumper in players_to_check:
            if self._try_player_jump(jumper, last_card):
                return True

        return False

    def _get_players_to_check_for_jump(self):
        """获取需要检查跳牌的玩家列表"""
        players_to_check = []
        start_pos = self.cur_location 
        current_pos = start_pos  # 从当前玩家开始检查
        while len(players_to_check) < self.player_num:  # 检查所有玩家
            players_to_check.append(self.player_list[current_pos])
            current_pos = (current_pos + self.dir) % self.player_num
            if current_pos == start_pos:  # 如果回到起始位置，说明已经检查完所有玩家
                break
        return players_to_check

    def _get_players_to_check_for_jump_except_current(self):
        """获取需要检查跳牌的玩家列表（排除当前玩家）"""
        players_to_check = []
        start_pos = self.cur_location 
        current_pos = start_pos  # 从当前玩家开始检查
        while len(players_to_check) < self.player_num:  # 检查所有玩家
            players_to_check.append(self.player_list[current_pos])
            current_pos = (current_pos + self.dir) % self.player_num
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
        if jumper.is_ai:
            return True  # AI总是跳牌
        elif self.gui:
            jump_card_display = str(chosen_jump_info['virtual_card'] or chosen_jump_info['original_card'])
            return self.gui.ask_yes_no_question("发现跳牌机会", f"是否使用 {jump_card_display} 进行跳牌？")
        return False

    def _execute_jump(self, jumper, chosen_jump_info):
        """执行跳牌动作"""
        original_card = chosen_jump_info['original_card']
        virtual_card = chosen_jump_info['virtual_card']
        
        if self.gui:
            self.gui.show_message_box("跳牌！", f"玩家 {jumper.position+1} ({jumper.mr_card.name}) 跳牌！")

        # 重置加牌链
        if self.draw_n > 0:
            self.draw_n = 0
            self.draw_chain_cards.clear()

        # 切换当前玩家到跳牌玩家
        self.cur_location = jumper.position

        # 添加跳牌历史记录
        jump_card_for_history = virtual_card if virtual_card else original_card
        self.add_history(f"{jumper.mr_card.name} 跳 [{jump_card_for_history}]")

        # 处理跳牌后的技能效果（在出牌前）
        if virtual_card:
            self._handle_jump_skills(jumper, virtual_card)
        else:
            self._handle_jump_skills(jumper, original_card)

        # 处理跳牌的出牌动作
        # 跳牌后的下一个玩家应该是跳牌玩家的下家
        next_player_after_jump = (jumper.position + self.dir) % self.player_num
        action = PlayAction(
            card=original_card,
            source=jumper,
            target=self.player_list[next_player_after_jump],
            virtual_card=virtual_card
        )

        self.process_play_action(action, is_jump=True)

    def _check_jump_after_jump(self):
        """跳牌后再次检查跳牌"""
        # 检查是否有玩家可以跳牌（包括当前跳牌玩家，允许连续跳牌）
        if self.handle_jump_logic():
            # 如果发生跳牌，递归检查
            self._check_jump_after_jump()

    def _check_forced_draw_after_jump(self):
        """跳牌后检查新玩家的强制摸牌"""
        current_player = self.player_list[self.cur_location]
        
        # 检查是否需要强制摸牌
        if self.draw_n > 0 and not self.can_continue_draw_chain(current_player):
            # 直接调用强制摸牌方法，不通过pre_turn_checks
            current_player.handle_forced_draw()

    # ==================== 手牌管理函数 ====================
    def check_hand_limit_and_discard_if_needed(self, player: Player):
        """检查指定玩家的手牌是否超限。现在规则：等于上限时不能再摸牌。"""
        if len(player.uno_list) >= player.hand_limit:
            if self.gui:
                self.gui.show_temporary_message(f"{player.mr_card.name} 手牌已达上限，不能再摸牌！")
            return True
        return False

    def player_confirms_discard(self, player: Player, cards_to_discard: List[UnoCard]):
        """当人类玩家在GUI上确认弃牌后，调用此方法。"""
        if not self.is_discard_mode or player != self.player_in_discard:
            return

        # 弃掉选择的牌
        player.fold_card_objects(cards_to_discard)
        
        # 清理并退出弃牌模式的游戏状态
        self.is_discard_mode = False
        self.player_in_discard = None
        self.cards_to_draw_in_discard.clear()
        self.num_to_discard = 0

    def add_history(self, text):
        # 只在Game类中维护历史记录，GUI会自动同步
        if self.gui:
            self.gui.add_history(text)