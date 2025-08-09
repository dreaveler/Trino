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

    # ==================== 1. 基础属性和初始化 ====================
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
            try:
                if self.game and new_uno_state:
                    self.game.add_history(f"{self.mr_card.name} 只剩一张手牌！")
                elif self.game and not new_uno_state and self.uno_state:
                    # 从uno状态退出（手牌从1变为其他数量）
                    pass
            except RuntimeError:
                # 如果GUI组件已被删除，静默忽略
                pass

    # ==================== 2. 游戏逻辑核心方法 ====================
    def turn(self):
        """
        普通玩家回合：skip检查 -> +牌链处理 -> 出牌/摸牌/发动技能三选一 -> 根据打出牌类型更新flag -> 结束回合
        """
        # 如果游戏已经结束，则不再继续
        if self.game.game_over:
            return
            
        # 回合开始时的状态重置（原本在next_player方法中）
        self.game.turn_action_taken = False
        self.game.turn_count += 1
        
        # 重置武圣状态（原本在next_player方法中）
        if self.game.gui:
            self.game.gui.wusheng_active = False
        
        # 1. skip检查 - 检查当前玩家是否应该被跳过
        if self._check_and_handle_skip():
            return  # 如果被跳过，回合结束
        
        # 2. +牌链处理 - 处理强制摸牌
        if self._handle_draw_chain():
            # 如果处理了强制摸牌，回合已经结束，直接返回
            return
        
        # 3. 执行玩家回合内容
        self.execute_turn_content()
        
        # 4. 根据打出牌类型更新flag
        self._update_flags_after_turn()
        
        # 5. 回合结束时清空状态
        self.game.clear_state()

    def jump_turn(self):
        """
        跳牌玩家特殊回合：可以打出与上一张牌相同的牌来跳牌
        """
        # 如果游戏已经结束，则不再继续
        if self.game.game_over:
            return
            
        print(f"跳牌玩家 {self.mr_card.name} 特殊回合开始")
        
        # 跳牌玩家可以打出与上一张牌相同的牌来跳牌
        action_type, action_value = self._get_jump_decision()
        if action_type == 'play':
            # 可以跳牌，执行出牌
            self.play(action_value)
            # 添加跳牌历史记录
            # 获取跳牌时打出的牌
            if action_value is not None and 0 <= action_value < len(self.uno_list):
                jumped_card = self.uno_list[action_value]
                # 可选详细日志：self.game.add_history(f"{self.mr_card.name} 跳牌使用: {jumped_card}")
            else:
                # 跳牌历史已由 Game.handle_gui_jump_turn 统一记录
                pass
        else:
            # 无法跳牌，跳过这个特殊回合
            print(f"{self.mr_card.name} 无法跳牌，跳过特殊回合")
        
        # 更新flag（在跳牌回合中，reverse/skip不生效）
        self._update_flags_after_jump_turn()

    def _check_and_handle_skip(self):
        """检查并处理skip效果"""
        if self.game.skip:
            print(f"玩家 {self.position+1} ({self.mr_card.name}) 被跳过")
            # 记录跳过历史
            self.game.add_history(f"{self.mr_card.name} 被跳过！")
            if self.game.gui:
                # 在GUI中显示跳过信息
                self.game.gui.show_temporary_message(f"玩家 {self.position + 1} ({self.mr_card.name}) 被跳过！")
            
            self.game.skip = False  # 消耗skip状态
            # 设置行动标志，表示回合已结束（被跳过）
            self.game.turn_action_taken = True
            return True  # 表示被跳过
        return False  # 表示未被跳过

    def _handle_draw_chain(self):
        """处理+牌链（强制摸牌）"""
        if self.game.draw_n > 0:
            print(f"玩家 {self.position+1} 需要处理+牌链，摸 {self.game.draw_n} 张牌")
            self.handle_forced_draw()
            return True  # 表示处理了强制摸牌
        return False  # 表示没有强制摸牌

    def _settle_skip_and_draw_chain(self):
        """结算skip和+牌链（已废弃，保留用于兼容性）"""
        # 检查skip效果
        if self._check_and_handle_skip():
            return  # 如果被跳过，回合结束
        
        # 处理+牌链
        self._handle_draw_chain()

    def _update_flags_after_turn(self):
        """根据打出牌类型更新flag"""
        # 这个方法会在change_flag()中处理，这里只是占位
        pass

    def _update_flags_after_jump_turn(self):
        """跳牌回合后更新flag（reverse/skip不生效）"""
        # 在跳牌回合中，reverse/skip效果不生效
        last_play_info = self.game.playedcards.get_last_play_info()
        if last_play_info:
            effective_card, original_card, source_player = last_play_info
            card_type = effective_card.type
            
            if card_type == "reverse":
                # 在跳牌回合中，reverse不生效，恢复方向
                self.game.dir *= -1
                print(f"跳牌回合中，reverse效果被忽略")
            elif card_type == "skip":
                # 在跳牌回合中，skip不生效，恢复skip状态
                self.game.skip = False
                print(f"跳牌回合中，skip效果被忽略")

    def _get_jump_decision(self):
        """跳牌玩家决策：检查可以跳牌的牌"""
        # 获取上一张牌
        last_play_info = self.game.playedcards.get_last_play_info()
        if not last_play_info:
            return 'draw', None
        
        last_card, _, _ = last_play_info
        
        # 查找可以跳牌的牌
        potential_jumps = self.check_for_jump(last_card)
        if potential_jumps:
            # 选择第一张可以跳牌的牌
            jump_info = potential_jumps[0]
            card_to_jump = jump_info['original_card']
            # 找到这张牌在手牌中的索引
            for i, card in enumerate(self.uno_list):
                if card == card_to_jump:
                    return 'play', i
        
        return 'draw', None

    def execute_turn_content(self):
        """
        执行一个玩家在一个回合内的全部内容，不包括跳牌与切换至下一个玩家
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
                self.game.gui.show_temporary_message(f"{self.mr_card.name} 摸了 {self.game.draw_n} 张牌", duration=1000)
            
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
            # 设置保护：当前玩家因强制摸牌后，不允许立刻作为跳牌的第一候选
            try:
                self.game.skip_jump_after_forced_draw = True
                self.game.player_who_just_forced_draw = self
            except Exception:
                pass
            
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
        
        # 6. 确保回合已结束（如果还没有设置的话）
        if not self.game.turn_action_taken:
            self.game.turn_action_taken = True



    # ==================== 3. 跳牌相关 ====================
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

    def check_for_jump(self, last_card: UnoCard) -> List:
        """默认的跳牌检查实现"""
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

    # ==================== 4. 摸牌相关（默认实现） ====================
    def draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """摸牌实现"""
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
                    try:
                        if self.game:
                            self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，停止摸牌")
                    except RuntimeError:
                        # 如果GUI组件已被删除，静默忽略
                        pass
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
            try:
                if self.game:
                    self.game.add_history(f"{self.mr_card.name} 摸了 {len(cards_drawn)} 张牌")
            except RuntimeError:
                # 如果GUI组件已被删除，静默忽略
                pass
        # 统计：记录摸牌数量（技能摸牌也计入“摸了多少张”）
        if self.game:
            try:
                self.game.record_draw(self, len(cards_drawn))
            except Exception:
                pass

        # 摸牌后，立即检查手牌上限
        self.check_hand_limit_and_discard_if_needed()
        
        # 通知GUI有玩家摸牌
        if self.game:
            self.game.notify_cards_drawn(self, len(cards_drawn))
            self.game.notify_player_hand_changed(self)
            self.game.notify_draw_pile_changed()

    def handle_forced_draw(self):
        """强制摸牌实现"""
        # 先完成强制摸牌（遵守手牌上限）
        actual_draw_n = min(self.game.draw_n, self.hand_limit - len(self.uno_list))
        if actual_draw_n > 0:
            self.draw_cards(actual_draw_n)
                        # 如果实际摸牌数少于要求的摸牌数，说明达到了手牌上限
            if actual_draw_n < self.game.draw_n:
                try:
                    if self.game:
                        self.game.add_history(f"{self.mr_card.name} 强制摸牌时达到手牌上限({self.hand_limit})，只摸了 {actual_draw_n} 张牌")
                except RuntimeError:
                    # 如果GUI组件已被删除，静默忽略
                    pass
        else:
            # 如果已经达到手牌上限，记录到历史
            try:
                if self.game:
                    self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，无法强制摸牌")
            except RuntimeError:
                # 如果GUI组件已被删除，静默忽略
                pass
        
        # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        if jianxiong_skill and self.game.draw_chain_cards:
            # 检查是否为AI玩家
            if isinstance(self, AIPlayer):
                # AI玩家使用AI决策逻辑
                if self.game.ai_handler.ai_choose_to_use_skill(self, '奸雄'):
                    self.execute_skill_jianxiong()
            elif self.game.gui:
                # 人类玩家通过GUI询问
                if self.game.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                    self.execute_skill_jianxiong()
        
        self.game.draw_n = 0
        self.game.draw_chain_cards.clear()
        
        # 强制摸牌完成后，结束玩家的回合
        self.game.turn_action_taken = True

        # 统计：将本次强制摸牌归因到+牌来源玩家
        try:
            self.game.attribute_forced_draw(self, actual_draw_n)
        except Exception:
            pass

    # ==================== 5. 出牌相关（默认实现） ====================
    def play(self, card_idx: int, wusheng_active: bool = False):
        """出牌实现"""
        is_valid, message, card_to_play, original_card = self.validate_play(card_idx, wusheng_active)
        if not is_valid:
            if self.game.gui:
                self.game.gui.show_message_box("提示", message)
            else:
                print(message)
            return

        color_choice = None
        if card_to_play.type in ['wild', 'wild_draw4']:
            if isinstance(self, AIPlayer):
                # AI玩家自动选择颜色，不需要对话框
                color_choice = self._choose_ai_wild_color()
            elif self.game.gui:
                # 人类玩家通过对话框选择颜色
                color_choice = self.game.gui.choose_color_dialog()
                if not color_choice:
                    return # 玩家取消选择
            else:
                color_choice = 'red' # 非GUI模式默认为红色

        # 对于reverse卡牌，需要特殊处理target_player
        if original_card.type == 'reverse':
            # 计算方向改变后的下一个玩家
            new_dir = -self.game.dir  # 方向改变后的方向
            next_pos_after_reverse = (self.position + new_dir) % len(self.game.player_list)
            target_player = self.game.player_list[next_pos_after_reverse]
        else:
            # 获取下一个玩家，但不切换回合
            target_player = self.game._get_next_player(self.position)
        
        action = PlayAction(
            card=original_card,
            source=self,
            target=target_player,
            color_choice=color_choice,
            virtual_card=card_to_play if wusheng_active and original_card.color == 'red' else None
        )
        # 历史记录在process_play_action中统一处理
        self.game.turn_action_taken = True
        self.process_play_action(action)
        
        # 检查是否是最后一张黑色牌，如果是则摸一张
        if hasattr(self, '_last_card_is_black') and self._last_card_is_black:
            self.draw_cards(1)
            self.game.add_history(f"{self.mr_card.name} 打出最后一张黑色牌，摸了一张牌")
            self._last_card_is_black = False  # 重置标记

    def validate_play(self, card_idx: int, wusheng_active: bool):
        """默认的出牌验证"""
        if card_idx is None or card_idx >= len(self.uno_list):
            return False, "无效的卡牌索引。", None, None

        original_card = self.uno_list[card_idx]
        card_to_play = original_card
        if wusheng_active and original_card.color == 'red':
            from card import UnoCard
            card_to_play = UnoCard('draw2', 'red', 0)

        # 检查是否为跳牌场景：如果是跳牌，则跳过普通出牌规则检查
        is_jump_scenario = False
        last_play_info = self.game.playedcards.get_last_play_info()
        if last_play_info:
            effective_card, _, _ = last_play_info
            # 检查当前玩家是否可以跳牌
            potential_jumps = self.check_for_jump(effective_card)
            if potential_jumps:
                # 检查选中的牌是否在可跳牌列表中
                for jump_info in potential_jumps:
                    if jump_info['original_card'] == original_card:
                        is_jump_scenario = True
                        break

        # 只有在非跳牌场景下才检查普通出牌规则
        if not is_jump_scenario and not self.check_card(card_to_play):
            return False, "这张牌不符合出牌规则。", None, None

        if len(self.uno_list) == 2 and self.game.gui:
            # 可以在这里添加喊UNO的逻辑
            pass

        # 最后一张牌是黑色牌的特殊处理：允许出牌，但出牌后需要摸一张
        if len(self.uno_list) == 1 and card_to_play.type in ['wild', 'wild_draw4']:
            # 标记这是最后一张黑色牌，需要在出牌后摸一张
            self._last_card_is_black = True

        return True, "有效出牌", card_to_play, original_card

    def check_card(self, card: UnoCard):
        """默认的卡牌检查实现"""
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
        """检查手牌中是否有任何可以合法打出的牌"""
        for card in self.uno_list:
            if self.check_card(card):
                return True
        return False

    def play_a_hand(self, i: int):
        """打出一张手牌"""
        card = self.uno_list.pop(i)
        # 更新uno状态
        self.update_uno_state()
        return card

    def play_card_object(self, card: UnoCard):
        """打出卡牌对象"""
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

    # ==================== 6. 弃牌相关（默认实现） ====================
    def fold_card(self, indices):
        """默认的弃牌实现"""
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
        """根据卡牌对象弃牌"""
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

    # ==================== 7. 技能相关（抽象方法） ====================
    def execute_skill_jianxiong(self):
        """奸雄技能处理 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def execute_skill_wusheng(self, card_idx):
        """武圣技能处理 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def execute_skill(self, skill, *args):
        """通用技能执行 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def activate_skill(self, skill_name: str):
        """激活技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def handle_jump_card_effect(self, card):
        """处理跳牌时的卡片效果 - 默认实现"""
        # 跳牌时直接应用效果，不延迟
        if card.type == "draw2":
            # 跳牌时如果跳的是+2牌，则清空加牌链并只保留当前+2牌
            self.game.draw_n = 2
            self.game.draw_chain_cards.clear()
            self.game.draw_chain_cards.append((card, card, self))
        elif card.type == "wild_draw4":
            # 跳牌时如果跳的是+4牌，则清空加牌链并只保留当前+4牌
            self.game.draw_n = 4
            self.game.draw_chain_cards.clear()
            self.game.draw_chain_cards.append((card, card, self))
        # 跳牌时skip与reverse不生效，也不对当前flag做出改变
        # elif card.type == "skip":
        #     self.game.skip = True
        # elif card.type == "reverse":
        #     self.game.dir *= -1
        #     self.game.add_history("方向倒转！")

    def handle_jump_skills(self, jump_card):
        """处理跳牌后的技能效果 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def handle_post_play_skills(self, card):
        """处理出牌后技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def _check_and_handle_skill(self, skill_name: str, handler_method: str, *args, skill_class_name: str = None, condition_func=None):
        """通用技能检查和处理方法"""
        if not self.mr_card:
            return False
        
        # 查找技能
        if skill_class_name:
            skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == skill_class_name), None)
        else:
            skill = next((s for s in self.mr_card.skills if s.name == skill_name), None)
        
        # 检查条件函数
        condition_met = True
        if condition_func is not None:
            # 检查条件函数的参数数量
            import inspect
            sig = inspect.signature(condition_func)
            if len(sig.parameters) == 0:
                # 无参数的条件函数（如lambda: card.color == 'green'）
                condition_met = condition_func()
            else:
                # 有参数的条件函数
                condition_met = condition_func(*args)
        
        if skill and condition_met:
            if handler_method and hasattr(self, handler_method):
                getattr(self, handler_method)(skill, *args)
                return True
        return False

    # ==================== 8. 决策相关（抽象方法） ====================
    def choose_cards_to_discard(self, num_to_discard: int) -> List[int]:
        """选择要弃置的卡牌 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def choose_to_use_skill(self, skill_name: str) -> bool:
        """选择是否使用技能 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")
    
    def choose_blue_card_to_play_for_lord(self) -> UnoCard:
        """选择蓝色牌为主公打出 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def _get_player_decision(self):
        """获取玩家决策 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def _execute_player_decision(self, action_type, action_value):
        """执行玩家决策 - 子类需要重写"""
        raise NotImplementedError("子类必须实现此方法")

    def _handle_action_failure(self):
        """处理行动失败时的通用逻辑"""
        if self.game.draw_n > 0:
            self.handle_forced_draw()
            self._check_jianxiong_after_draw()
            self.game.draw_n = 0
            self.game.draw_chain_cards.clear()
        else:
            self.draw_cards(1)
        
        # 确保设置行动标志
        self.game.turn_action_taken = True

    def _check_jianxiong_after_draw(self):
        """摸牌后检查奸雄技能 - 子类可以重写"""
        pass

    # ==================== 9. 辅助方法 ====================
    def check_hand_limit_and_discard_if_needed(self):
        """检查手牌是否超限"""
        if len(self.uno_list) >= self.hand_limit:
            if self.game and self.game.gui:
                self.game.gui.show_temporary_message(f"{self.mr_card.name} 手牌已达上限，不能再摸牌！")
            return True
        return False

    def _get_players_to_check_for_jump(self):
        """获取需要检查跳牌的玩家列表"""
        if not self.game:
            return []
            
        players_to_check = []
        start_pos = self.game.cur_location 
        current_pos = start_pos  # 从当前玩家开始检查
        actual_player_count = len(self.game.player_list)
        while len(players_to_check) < actual_player_count:  # 检查所有玩家
            players_to_check.append(self.game.player_list[current_pos])
            current_pos = (current_pos + self.game.dir) % actual_player_count
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

        # 重置+牌串
        if self.game.draw_n > 0:
            self.game.draw_n = 0
            self.game.draw_chain_cards.clear()

        # 添加跳牌历史记录（武圣跳牌有特殊的历史记录，这里不添加通用记录）
        jump_card_for_history = virtual_card if virtual_card else original_card
        # 检查是否是武圣跳牌，如果是则不添加通用跳牌历史记录
        is_wusheng_jump = (virtual_card and virtual_card.type == 'draw2' and virtual_card.color == 'red')
        if not is_wusheng_jump:
            # 跳牌历史已由 Game.handle_gui_jump_turn 统一记录
            pass

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
            # 统计：记录玩家打出一张牌
            try:
                self.game.record_play(self)
            except Exception:
                pass
            # 标记：发生了“真正的出牌”，打开跳牌窗口
            try:
                self.game.jump_window_open = True
            except Exception:
                pass
            
            # 处理武圣技能的历史记录
            if not getattr(self.game, 'suppress_next_play_history', False):
                if effective_card.type == 'draw2' and effective_card.color == 'red' and original_card.color == 'red' and original_card.type != 'draw2':
                    # 这是武圣技能激活的情况
                    self.game.add_history(f"{self.mr_card.name} 发动[武圣]技能，将 [{original_card}] 当作 [红+2] 打出 -> {action.target.mr_card.name}")
                else:
                    # 正常出牌的历史记录
                    self.game.add_history(f"{self.mr_card.name} - {original_card} -> {action.target.mr_card.name}")
            else:
                # 被跳牌逻辑抑制的第一条正常出牌历史，跳过并重置标志
                self.game.suppress_next_play_history = False
        else:
            # 跳牌时，只添加弃牌堆信息，不添加历史记录（历史记录在_execute_jump中处理）
            self.game.playedcards.add_card(effective_card, self, original_card)

        # 3. 更新当前颜色
        self._update_color_after_play(effective_card, action.color_choice)

        # 4. 根据牌的效果更新游戏状态
        self.game.change_flag(is_jump)

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
            
            # 跳牌检查现在在游戏主循环中进行，这里不需要处理
        else:
            # 非跳牌的正常出牌逻辑
            # 在设置turn_action_taken之前，先检查当前玩家是否有相同的牌可以跳牌
            last_play_info = self.game.playedcards.get_last_play_info()
            if last_play_info:
                effective_card, original_card, source_player = last_play_info
                # 检查当前玩家是否有相同的牌可以跳牌
                potential_jumps = self.check_for_jump(effective_card)
                if potential_jumps:
                    # 当前玩家有相同的牌可以跳牌，不结束回合，让游戏循环处理跳牌
                    if self.game.gui:
                        self.game.gui.restart_game_loop()
                else:
                    # 当前玩家没有相同的牌可以跳牌，检查其他玩家是否有跳牌机会
                    if self.game.check_for_jump():
                        # 其他玩家有跳牌机会，不结束回合，让游戏循环处理跳牌
                        if self.game.gui:
                            self.game.gui.restart_game_loop()
                    else:
                        # 没有任何跳牌机会，正常结束回合
                        self.game.turn_action_taken = True  # 标记回合已结束
                        self.game.clear_state()
                        self.game.turn_count += 1
            else:
                # 没有上一张牌信息，正常结束回合
                self.game.turn_action_taken = True  # 标记回合已结束
                self.game.clear_state()
                self.game.turn_count += 1

    def _update_color_after_play(self, effective_card, color_choice):
        """更新出牌后的颜色"""
        if effective_card.type in ['wild', 'wild_draw4']:
            if color_choice:
                # 如果已经有颜色选择（AI玩家或人类玩家已选择），直接使用
                self.game.cur_color = color_choice
            else:
                # 如果没有颜色选择（不应该发生），使用默认逻辑
                if isinstance(self, AIPlayer):
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

    # ==================== 10. 入口方法 ====================
    # 这些方法直接调用对应的player_*方法，保持接口一致性



class HumanPlayer(Player):
    """人类玩家类，继承自Player基类"""
    
    def __init__(self, position: int, team: str = None):
        super().__init__(position, team)

    # ==================== 人类玩家特有的实现 ====================
    


    # ==================== 技能相关 ====================
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
        self.game.draw_chain_cards.clear() # 清空+牌串
        # 奸雄后应该结束回合
        self.game.turn_action_taken = True
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

    def activate_skill(self, skill_name: str):
        """激活技能 - 人类玩家实现"""
        if skill_name == '反间':
            # 检查是否有非黑色手牌
            non_black_cards = [card for card in self.uno_list if card.color not in ['black']]
            if not non_black_cards:
                if self.game.gui:
                    self.game.gui.show_message_box("技能发动失败", "没有非黑色手牌可以发动反间技能")
                return
            
            # 通过GUI选择目标玩家
            if self.game.gui:
                target = self.game.gui.choose_target_player_dialog(exclude_self=True)
                if not target:
                    return
                
                # 通过GUI选择要给出的牌
                card_to_give = self.game.gui.choose_specific_card_dialog(self, non_black_cards, "选择要给出的牌")
                if not card_to_give:
                    return
                
                # 执行反间技能
                self._execute_fanjian_skill(target, card_to_give)
            else:
                print("反间技能需要GUI支持")
                return
        elif skill_name == '武圣':
            # 检查是否有红色手牌
            red_cards = [card for card in self.uno_list if card.color == 'red']
            if not red_cards:
                if self.game.gui:
                    self.game.gui.show_message_box("技能发动失败", "没有红色手牌可以发动武圣技能")
                return
            
            # 通过GUI选择要当作红+2打出的红色牌
            if self.game.gui:
                card_to_play = self.game.gui.choose_specific_card_dialog(self, red_cards, "选择要当作红+2打出的红色牌")
                if not card_to_play:
                    return
                
                # 执行武圣技能
                self._execute_wusheng_skill(card_to_play)
            else:
                print("武圣技能需要GUI支持")
                return
        elif skill_name == '缔盟':
            # 检查手牌数是否大于6
            if len(self.uno_list) > 6:
                if self.game.gui:
                    self.game.gui.show_message_box("技能发动失败", "手牌数大于6时缔盟技能失效")
                return
            
            # 通过GUI选择两名其他玩家
            if self.game.gui:
                self.game.gui.show_message_box("选择玩家", "请选择第一个玩家")
                player1 = self.game.gui.choose_target_player_dialog(exclude_self=True)
                if not player1:
                    return
                
                self.game.gui.show_message_box("选择玩家", "请选择第二个玩家（不能与第一个玩家相同）")
                player2 = self.game.gui.choose_target_player_dialog(exclude_self=True)
                if not player2 or player2 == player1:
                    if self.game.gui:
                        self.game.gui.show_message_box("技能发动失败", "请选择两个不同的玩家")
                    return
                
                # 执行缔盟技能
                self._execute_dimeng_skill(player1, player2)
            else:
                print("缔盟技能需要GUI支持")
                return
        else:
            print(f"未知技能: {skill_name}")

    def _execute_fanjian_skill(self, target, card_to_give):
        """执行反间技能的具体逻辑"""
        # 1. 玩家摸一张牌
        self.draw_cards(1, is_skill_draw=True)
        
        # 2. 将牌从玩家手牌给目标
        self.play_card_object(card_to_give) # 从手牌移除
        
        # 3. 目标弃掉所有同色牌
        color_to_discard = card_to_give.color
        cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
        cards_to_discard.append(card_to_give) # 把给的牌也算上
        
        fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
        target.fold_card(fold_indices)

        # 4. 检查弃牌数量，如果>2则周瑜额外摸一张牌
        discarded_count = len(cards_to_discard)
        if discarded_count > 2:
            self.draw_cards(1, is_skill_draw=True)
            self.game.add_history(f"{self.mr_card.name} 弃牌数量为{discarded_count}，额外摸了一张牌")

        if self.game.gui:
            self.game.gui.show_message_box("反间成功", f"玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
        else:
            print(f"反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
        
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if self.game.check_win_condition(self) or self.game.check_win_condition(target):
            return

        # 技能执行完成后，手动结束回合
        self.game.turn_action_taken = True

    def _execute_wusheng_skill(self, card_to_play):
        """执行武圣技能的具体逻辑"""
        # 从手牌中移除选中的红色牌
        self.play_card_object(card_to_play)
        
        # 创建一个红+2牌的效果
        from card import UnoCard
        red_draw2_card = UnoCard('draw2', 'red', 0)
        
        # 将红+2牌添加到弃牌堆
        self.game.playedcards.add_card(red_draw2_card, self, card_to_play)
        
        # 更新当前颜色
        self.game.cur_color = 'red'
        
        # 不手动设置draw_n和draw_chain_cards，让change_flag()来处理
        # 不手动调用change_flag()，让process_play_action来处理
        
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[武圣]，将 [{card_to_play}] 当作 [红+2] 打出")
        
        # 设置行动标志
        self.game.turn_action_taken = True

    def _execute_dimeng_skill(self, player1, player2):
        """执行缔盟技能的具体逻辑"""
        # 计算两人手牌数目之差
        hand_diff = abs(len(player1.uno_list) - len(player2.uno_list))
        
        # 玩家摸x张牌
        self.draw_cards(hand_diff, is_skill_draw=True)
        
        # 交换两人的手牌
        temp_hand = player1.uno_list.copy()
        player1.uno_list = player2.uno_list.copy()
        player2.uno_list = temp_hand.copy()
        
        # 通知GUI更新显示
        if self.game.gui:
            self.game.gui.on_player_hand_changed(player1)
            self.game.gui.on_player_hand_changed(player2)
        
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[缔盟]，摸了 {hand_diff} 张牌，玩家 {player1.position+1} 和玩家 {player2.position+1} 交换了手牌")
        
        # 设置行动标志
        self.game.turn_action_taken = True

    def execute_skill(self, skill, *args):
        """人类玩家技能执行"""
        print(f"玩家 {self.position+1} 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            self.draw_cards(1, is_skill_draw=True)
            # 2. 将牌从玩家手牌给目标
            self.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            # 4. 检查弃牌数量，如果>2则周瑜额外摸一张牌
            discarded_count = len(cards_to_discard)
            if discarded_count > 2:
                self.draw_cards(1, is_skill_draw=True)
                self.game.add_history(f"{self.mr_card.name} 弃牌数量为{discarded_count}，额外摸了一张牌")

            print(f"AI反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            # 添加历史记录
            self.game.add_history(f"{self.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if self.game.check_win_condition(self) or self.game.check_win_condition(target):
            return
        
        # 技能执行完成后，手动结束回合
        self.game.turn_action_taken = True



    def handle_jump_skills(self, jump_card):
        """人类玩家处理跳牌后的技能效果"""
        # 检查奇袭技能
        self._check_and_handle_skill('奇袭', '_handle_player_qixi', jump_card, condition_func=lambda: jump_card.color == 'green')
        
        # 检查旋风技能
        self._check_and_handle_skill('旋风', '_handle_player_xuanfeng', jump_card, skill_class_name='XuanFeng')
        
        # 检查散谣技能
        self._check_and_handle_skill('散谣', '_handle_player_sanyao', jump_card, skill_class_name='SanYao')

    def handle_post_play_skills(self, card):
        """人类玩家处理出牌后可能触发的技能"""
        # 奇袭技能处理
        self._check_and_handle_skill('奇袭', '_handle_player_qixi', card, condition_func=lambda: card.color == 'green')
        
        # 集智技能处理
        self._check_and_handle_skill('集智', '_handle_player_jizhi', card, condition_func=lambda: card.type in ['draw2', 'wild_draw4', 'wild'])

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
                # 技能执行完成后，手动结束回合
                self.game.turn_action_taken = True

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
                    
                    # 技能执行完成后，手动结束回合
                    self.game.turn_action_taken = True

    def _handle_player_xuanfeng(self, xuanfeng_skill, jump_card):
        """人类玩家旋风技能处理"""
        # 检查跳牌是否有value属性（适用于number和draw2等有数值的牌）
        if hasattr(jump_card, 'value'):
            # 找到所有与跳牌value相同的牌（不包括跳牌本身）
            same_value_cards = [card for card in self.uno_list if hasattr(card, 'value') and card.value == jump_card.value]
            
            # 总是询问是否发动技能，即使没有相同点数的牌
            if self.game.gui and self.game.gui.ask_yes_no_question("发动技能", "是否发动【旋风】弃置所有相同点数的牌？"):
                if same_value_cards:
                    # 弃置所有相同value的牌
                    cards_to_discard = []
                    for i, card in enumerate(self.uno_list):
                        if hasattr(card, 'value') and card.value == jump_card.value:
                            cards_to_discard.append(i)
                    
                    # 按索引从大到小排序，避免删除时索引变化
                    for idx in sorted(cards_to_discard, reverse=True):
                        self.fold_card(idx)
                    
                    # 添加历史记录（跳牌本身不计入弃置牌数）
                    self.game.add_history(f"{self.mr_card.name} 发动[旋风]，弃置了 {len(same_value_cards)} 张相同点数的牌")
                else:
                    # 没有相同点数的牌，但仍然记录发动技能
                    self.game.add_history(f"{self.mr_card.name} 发动[旋风]，没有相同点数的牌可弃置")
                
                # 技能执行完成后，手动结束回合
                self.game.turn_action_taken = True

    def _handle_player_sanyao(self, sanyao_skill, jump_card):
        """人类玩家散谣技能处理"""
        if self.game.gui and self.game.gui.ask_yes_no_question("发动技能", "是否发动【散谣】指定一名玩家摸2张牌？"):
            target = self.game.gui.choose_target_player_dialog(exclude_self=True)
            if target:
                # 让目标玩家摸2张牌
                target.draw_cards(2, is_skill_draw=True)
                self.game.add_history(f"{self.mr_card.name} 发动[散谣]，令 {target.mr_card.name} 摸了2张牌")
                
                # 技能执行完成后，手动结束回合
                self.game.turn_action_taken = True



    # ==================== 决策相关 ====================
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

    def choose_blue_card_to_play_for_lord(self) -> UnoCard:
        """人类玩家选择蓝色牌为主公打出"""
        if self.game and self.game.gui:
            # GUI模式下，通过GUI选择蓝色牌
            blue_cards = [card for card in self.uno_list if card.color == 'blue']
            if blue_cards:
                return self.game.gui.choose_specific_card_dialog(self, blue_cards, "选择蓝色牌为主公打出")
        else:
            # 命令行模式下的简单实现
            blue_cards = [card for card in self.uno_list if card.color == 'blue']
            if blue_cards:
                print("选择蓝色牌为主公打出:")
                for i, card in enumerate(blue_cards):
                    print(f"{i}: {card}")
                try:
                    choice = int(input())
                    if 0 <= choice < len(blue_cards):
                        return blue_cards[choice]
                except ValueError:
                    pass
        return None

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
                self._handle_action_failure()
        else:
            # 摸牌
            self._handle_action_failure()
            
class AIPlayer(Player):
    """AI玩家类，继承自Player基类，只负责执行AI决策"""
    
    def __init__(self, position: int, team: str = None):
        super().__init__(position, team)

    # ==================== AI玩家特有的实现 ====================

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
        self.game.draw_chain_cards.clear() # 清空+牌串

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
            self.draw_cards(1, is_skill_draw=True)
            # 2. 将牌从玩家手牌给目标
            self.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            # 4. 检查弃牌数量，如果>2则周瑜额外摸一张牌
            discarded_count = len(cards_to_discard)
            if discarded_count > 2:
                self.draw_cards(1, is_skill_draw=True)
                self.game.add_history(f"{self.mr_card.name} 弃牌数量为{discarded_count}，额外摸了一张牌")

            print(f"AI反间成功，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")
            # 添加历史记录
            self.game.add_history(f"{self.mr_card.name} 发动[反间]，玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌")

        # 检查胜利条件
        if self.game.check_win_condition(self) or self.game.check_win_condition(target):
            return

    def handle_jump_skills(self, jump_card):
        """AI玩家处理跳牌后的技能效果"""
        # 检查奇袭技能
        self._check_and_handle_skill('奇袭', '_handle_ai_qixi', jump_card, condition_func=lambda: jump_card.color == 'green')
        
        # 检查旋风技能
        self._check_and_handle_skill('旋风', '_handle_ai_xuanfeng', jump_card, skill_class_name='XuanFeng')
        
        # 检查三要技能
        self._check_and_handle_skill('三要', '_handle_ai_sanyao', jump_card, skill_class_name='SanYao')

    def handle_post_play_skills(self, card):
        """AI玩家处理出牌后的技能效果"""
        # 检查机智技能
        self._check_and_handle_skill('机智', '_handle_ai_jizhi', card, condition_func=lambda: card.type == 'number')

    def _handle_ai_qixi(self, qixi_skill, card):
        """AI奇袭技能处理"""
        # 使用AI处理器选择目标
        target_player = self.game.ai_handler.decide_qixi_target(self, self.game.player_list)
        if target_player and target_player != self:
            # 执行奇袭技能
            self.game.execute_skill_qixi(self, target_player)
            # 技能执行完成后，手动结束回合
            self.game.turn_action_taken = True

    def _handle_ai_skill_draw(self, skill_name: str):
        """AI通用技能摸牌处理"""
        self.draw_cards(1, is_skill_draw=True)
        print(f"AI 玩家 {self.position+1} ({self.mr_card.name}) 发动【{skill_name}】，摸了1张牌")
        # 添加历史记录
        self.game.add_history(f"{self.mr_card.name} 发动[{skill_name}]，摸了1张牌")
        # 技能执行完成后，手动结束回合
        self.game.turn_action_taken = True

    def _handle_ai_jizhi(self, jizhi_skill, card):
        """AI机智技能处理"""
        self._handle_ai_skill_draw("机智")

    def _handle_ai_xuanfeng(self, xuanfeng_skill, jump_card):
        """AI旋风技能处理"""
        # 检查跳牌是否有value属性（适用于number和draw2等有数值的牌）
        if hasattr(jump_card, 'value'):
            # 找到所有与跳牌value相同的牌（不包括跳牌本身）
            same_value_cards = [card for card in self.uno_list if hasattr(card, 'value') and card.value == jump_card.value]
            
            # AI决定是否发动技能
            if self.choose_to_use_skill('旋风'):
                if same_value_cards:
                    # 弃置所有相同value的牌
                    cards_to_discard = []
                    for i, card in enumerate(self.uno_list):
                        if hasattr(card, 'value') and card.value == jump_card.value:
                            cards_to_discard.append(i)
                    
                    # 按索引从大到小排序，避免删除时索引变化
                    for idx in sorted(cards_to_discard, reverse=True):
                        self.fold_card(idx)
                    
                    # 添加历史记录（跳牌本身不计入弃置牌数）
                    self.game.add_history(f"{self.mr_card.name} 发动[旋风]，弃置了 {len(same_value_cards)} 张相同点数的牌")
                else:
                    # 没有相同点数的牌，但仍然记录发动技能
                    self.game.add_history(f"{self.mr_card.name} 发动[旋风]，没有相同点数的牌可弃置")
                
                # 技能执行完成后，手动结束回合
                self.game.turn_action_taken = True

    def _handle_ai_sanyao(self, sanyao_skill, jump_card):
        """AI三要技能处理"""
        self._handle_ai_skill_draw("三要")

    # AI玩家使用基类的通用方法，不需要重写
    # ==================== AI决策相关 ====================
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

    def choose_blue_card_to_play_for_lord(self) -> UnoCard:
        """AI玩家选择蓝色牌为主公打出"""
        # AI简单策略：选择第一张蓝色牌
        blue_cards = [card for card in self.uno_list if card.color == 'blue']
        if blue_cards:
            return blue_cards[0]  # 返回第一张蓝色牌
        return None

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
                self._handle_action_failure()
                # 确保设置行动标志
                self.game.turn_action_taken = True
        else:
            # 摸牌
            self._handle_action_failure()
            # 确保设置行动标志
            self.game.turn_action_taken = True

    # ==================== AI特有方法 ====================
    def _choose_ai_wild_color(self):
        """AI选择万能牌颜色"""
        # 使用AI处理器选择颜色
        return self.game.ai_handler.choose_wild_color(self)

    def _check_jianxiong_after_draw(self):
        """摸牌后检查奸雄技能"""
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        jianxiong_eligible_cards = [
            original_card for effective_card, original_card, source_player in self.game.draw_chain_cards
            if (effective_card.type == 'draw2' or effective_card.type == 'wild_draw4') and source_player != self
        ]
        
        if jianxiong_skill and jianxiong_eligible_cards:
            if self.game.ai_handler.decide_jianxiong(self, self.game.draw_chain_cards):
                self.execute_skill_jianxiong()