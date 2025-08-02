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
    def __init__(self, position: int, is_ai: bool = False, team: str = None):
        self.position = position
        self.uno_list: List[UnoCard] = []
        self.is_ai = is_ai
        self.game: Game = None
        self.mr_card: MrCard = None
        self.team = team

    @property
    def hand_limit(self):
        """获取玩家的手牌上限"""
        if self.mr_card and any(s.name == '自守' for s in self.mr_card.skills):
            return 8
        return HAND_LIMIT

    # ==================== AI专用函数 ====================
    def ai_choose_cards_to_discard(self, num_to_discard: int) -> List[UnoCard]:
        """AI选择要弃置的牌的逻辑。简单策略：优先弃置高点数数字牌。"""
        # 按点数降序排序，优先保留功能牌和低点数牌
        sorted_hand = sorted(self.uno_list, key=lambda c: c.value if c.type == 'number' else -1, reverse=True)
        return sorted_hand[:num_to_discard]

    def ai_draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """AI摸牌的核心逻辑"""
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
                    # 记录到历史：达到手牌上限，停止摸牌
                    if self.game and not is_skill_draw:
                        self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，停止摸牌")
                    break
                if self.game.unocard_pack:
                    cards_drawn.append(self.game.unocard_pack.pop())
                else:
                    break
        
        if not cards_drawn:
            return

        self.uno_list.extend(cards_drawn)
        # 只有非技能摸牌才显示print信息和历史记录
        if not is_skill_draw:
            print(f"AI玩家 {self.position+1} 获得了 {len(cards_drawn)} 张牌。")
            # 历史记录：摸牌（技能发动的摸牌不记录，避免重复）
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 摸了 {len(cards_drawn)} 张牌")
        # 摸牌后，立即检查手牌上限
        self.game.check_hand_limit_and_discard_if_needed(self)

    def ai_handle_forced_draw(self):
        """AI处理被动响应摸牌（例如被+2/+4）"""
        # 检查是否有技能可以响应（如奸雄）
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        if jianxiong_skill and self.game.draw_chain_cards:
            # AI决策是否发动奸雄
            if self.game.ai_handler.decide_jianxiong(self, self.game.draw_chain_cards):
                self.game.execute_skill_jianxiong(self)
                return # 发动奸雄后，回合动作结束

        # 正常强制摸牌（遵守手牌上限）
        actual_draw_n = min(self.game.draw_n, self.hand_limit - len(self.uno_list))
        if actual_draw_n > 0:
            self.ai_draw_cards(actual_draw_n)
        else:
            # 如果已经达到手牌上限，记录到历史
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，无法强制摸牌")
        self.game.draw_n = 0
        self.game.draw_chain_cards.clear()

    def ai_play(self, card_idx: int, wusheng_active: bool = False):
        """AI主动出牌"""
        is_valid, message, card_to_play, original_card = self.validate_play(card_idx, wusheng_active)
        if not is_valid:
            print(f"AI出牌无效: {message}")
            return

        # AI选择颜色（简化逻辑，默认红色）
        color_choice = 'red' if card_to_play.type in ['wild', 'wild_draw4'] else None

        action = PlayAction(
            card=original_card,
            source=self,
            target=self.game.get_next_player(self.position),
            color_choice=color_choice,
            virtual_card=card_to_play if wusheng_active and original_card.color == 'red' else None
        )
        # 历史记录：分行显示功能牌效果
        base_record = f"{self.mr_card.name} - {original_card} -> {self.game.get_next_player(self.position).mr_card.name}"
        extra_record = ""
        if original_card.type == 'skip':
            extra_record = f"\n{self.game.get_next_player(self.position).mr_card.name} 被跳过！"
        elif original_card.type == 'reverse':
            extra_record = f"\n方向倒转！"
        self.game.add_history(base_record + extra_record)
        self.game.turn_action_taken = True
        self.game.process_play_action(action)
        
        # 检查是否是最后一张黑色牌，如果是则摸一张
        if hasattr(self, '_last_card_is_black') and self._last_card_is_black:
            self.ai_draw_cards(1)
            self.game.add_history(f"{self.mr_card.name} 打出最后一张黑色牌，摸了一张牌")
            self._last_card_is_black = False  # 重置标记

    # ==================== 玩家专用函数 ====================
    def player_draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """玩家摸牌的核心逻辑"""
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
                    # 记录到历史：达到手牌上限，停止摸牌
                    if self.game and not is_skill_draw:
                        self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，停止摸牌")
                    break
                if self.game.unocard_pack:
                    cards_drawn.append(self.game.unocard_pack.pop())
                else:
                    break
        
        if not cards_drawn:
            return

        self.uno_list.extend(cards_drawn)
        # 只有非技能摸牌才显示print信息和历史记录
        if not is_skill_draw:
            print(f"玩家 {self.position+1} 获得了 {len(cards_drawn)} 张牌。")
            # 历史记录：摸牌（技能发动的摸牌不记录，避免重复）
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 摸了 {len(cards_drawn)} 张牌")
        # 摸牌后，立即检查手牌上限
        self.game.check_hand_limit_and_discard_if_needed(self)

    def player_handle_forced_draw(self):
        """玩家处理被动响应摸牌（例如被+2/+4）"""
        # 检查是否有技能可以响应（如奸雄）
        jianxiong_skill = next((s for s in self.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        if jianxiong_skill and self.game.draw_chain_cards:
            if self.game.gui and self.game.gui.ask_yes_no_question("发动奸雄", "是否发动【奸雄】获得所有[+2]/[+4]牌？"):
                self.game.execute_skill_jianxiong(self)
                return # 发动奸雄后，回合动作结束

        # 正常强制摸牌（遵守手牌上限）
        actual_draw_n = min(self.game.draw_n, self.hand_limit - len(self.uno_list))
        if actual_draw_n > 0:
            self.player_draw_cards(actual_draw_n)
        else:
            # 如果已经达到手牌上限，记录到历史
            if self.game:
                self.game.add_history(f"{self.mr_card.name} 手牌已达上限({self.hand_limit})，无法强制摸牌")
        self.game.draw_n = 0
        self.game.draw_chain_cards.clear()

    def player_play(self, card_idx: int, wusheng_active: bool = False):
        """玩家主动出牌"""
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

        action = PlayAction(
            card=original_card,
            source=self,
            target=self.game.get_next_player(self.position),
            color_choice=color_choice,
            virtual_card=card_to_play if wusheng_active and original_card.color == 'red' else None
        )
        # 历史记录：分行显示功能牌效果
        base_record = f"{self.mr_card.name} - {original_card} -> {self.game.get_next_player(self.position).mr_card.name}"
        extra_record = ""
        if original_card.type == 'skip':
            extra_record = f"\n{self.game.get_next_player(self.position).mr_card.name} 被跳过！"
        elif original_card.type == 'reverse':
            extra_record = f"\n方向倒转！"
        self.game.add_history(base_record + extra_record)
        self.game.turn_action_taken = True
        self.game.process_play_action(action)
        
        # 检查是否是最后一张黑色牌，如果是则摸一张
        if hasattr(self, '_last_card_is_black') and self._last_card_is_black:
            self.player_draw_cards(1)
            self.game.add_history(f"{self.mr_card.name} 打出最后一张黑色牌，摸了一张牌")
            self._last_card_is_black = False  # 重置标记
            self._last_card_is_black = False  # 重置标记

    # ==================== 通用函数 ====================
    def draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """统一的摸牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            self.ai_draw_cards(num_to_draw, from_deck, specific_cards, is_skill_draw)
        else:
            self.player_draw_cards(num_to_draw, from_deck, specific_cards, is_skill_draw)

    def handle_forced_draw(self):
        """统一的强制摸牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            self.ai_handle_forced_draw()
        else:
            self.player_handle_forced_draw()

    def play(self, card_idx: int, wusheng_active: bool = False):
        """统一的出牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            self.ai_play(card_idx, wusheng_active)
        else:
            self.player_play(card_idx, wusheng_active)

    def validate_play(self, card_idx: int, wusheng_active: bool):
        """统一的出牌验证入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._validate_ai_play(card_idx, wusheng_active)
        else:
            return self._validate_player_play(card_idx, wusheng_active)

    def _validate_ai_play(self, card_idx: int, wusheng_active: bool):
        """AI出牌验证"""
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

    def _validate_player_play(self, card_idx: int, wusheng_active: bool):
        """玩家出牌验证"""
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
        """统一的技能发动入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            self._activate_ai_skill(skill_name)
        else:
            self._activate_player_skill(skill_name)

    def _activate_ai_skill(self, skill_name: str):
        """AI技能发动"""
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
                    else:
                        self.game.add_history(f"{self.mr_card.name} 发动[{skill_name}] 效果：{skill.description}")
        if skill_name == '反间':
            self._activate_ai_fanjian()
        # ... 其他技能可以在此添加
        else:
            print(f"AI技能 [{skill_name}] 的逻辑尚未完全移至Player。")

    def _activate_player_skill(self, skill_name: str):
        """玩家技能发动"""
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
                    else:
                        self.game.add_history(f"{self.mr_card.name} 发动[{skill_name}] 效果：{skill.description}")
        if skill_name == '反间':
            self._activate_player_fanjian()
        # ... 其他技能可以在此添加
        else:
            if self.game.gui:
                self.game.gui.show_message_box("提示", f"技能 [{skill_name}] 的逻辑尚未完全移至Player。")

    def _activate_ai_fanjian(self):
        """AI反间技能处理"""
        # AI反间逻辑可以在这里实现
        # 目前AI不主动使用反间技能
        print(f"AI {self.mr_card.name} 的反间技能逻辑待实现")

    def _activate_player_fanjian(self):
        """玩家反间技能处理"""
        if not self.game.gui: return

        # 1. 摸一张牌（技能发动，不写入历史记录）
        self.player_draw_cards(1, is_skill_draw=True)
        self.game.gui.show_temporary_message(f"{self.mr_card.name} 发动【反间】，摸了一张牌。")
        # 2. 选择要"给"的牌，而不是"打出"
        card_to_give = self.game.gui.choose_card_from_hand_dialog(self, "请选择一张你要交给对方的【反间】牌")
        if not card_to_give: return
        # 3. 选择目标
        target = self.game.gui.choose_target_player_dialog(exclude_self=True)
        if not target: return
        # 4. 结算"给牌"动作
        self.uno_list.remove(card_to_give)
        target.uno_list.append(card_to_give)
        # 5. 目标弃牌
        color_to_discard = card_to_give.color
        cards_to_discard_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
        if cards_to_discard_indices:
            discarded_cards = target.fold_card(cards_to_discard_indices)
        else:
            discarded_cards = []
        # 详细历史记录
        for skill in self.mr_card.skills:
            if skill.name == '反间' and hasattr(skill, 'record_history'):
                text = skill.record_history(self, target, card_to_give, discarded_cards)
                if text:
                    self.game.add_history(text)
        message = f"【反间】{target.mr_card.name} 弃掉了所有 {color_to_discard} 牌" if discarded_cards else f"【反间】{target.mr_card.name} 没有 {color_to_discard} 牌可弃。"
        self.game.gui.show_temporary_message(message, duration=3000)
        # 6. 检查目标胜利条件
        if len(target.uno_list) == 0:
            self.game.game_over = True
            self.game.gui.show_winner_and_exit(target)
            return
        # 7. 刷新整个游戏界面
        self.game.turn_action_taken = True # 发动技能视为已行动
        self.game.gui.show_game_round()

    def choose_fanjian_color_from_gui(self):
        """统一的反间颜色选择入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._ai_choose_fanjian_color()
        else:
            return self._player_choose_fanjian_color()

    def _ai_choose_fanjian_color(self):
        """AI反间颜色选择"""
        # AI默认选择红色
        return 'red'

    def _player_choose_fanjian_color(self):
        """玩家反间颜色选择"""
        if not self.game.gui:
            return 'red'  # 非GUI模式默认
        return self.game.gui.choose_fanjian_color_dialog()

    def check_for_jump(self, last_card: UnoCard) -> List:
        """统一的跳牌检查入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._check_ai_jump(last_card)
        else:
            return self._check_player_jump(last_card)

    def _check_ai_jump(self, last_card: UnoCard) -> List:
        """AI跳牌检查"""
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

    def _check_player_jump(self, last_card: UnoCard) -> List:
        """玩家跳牌检查"""
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
        
    # ==================== 打牌函数 ====================
    def play_a_hand(self,i:int):
        """统一的打牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._ai_play_a_hand(i)
        else:
            return self._player_play_a_hand(i)
    
    def _ai_play_a_hand(self,i:int):
        """AI打牌"""
        return self.uno_list.pop(i)
    
    def _player_play_a_hand(self,i:int):
        """玩家打牌"""
        return self.uno_list.pop(i)
    
    def play_card_object(self, card: UnoCard):
        """统一的打牌对象入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            self._ai_play_card_object(card)
        else:
            self._player_play_card_object(card)

    def _ai_play_card_object(self, card: UnoCard):
        """AI打牌对象"""
        try:
            self.uno_list.remove(card)
        except ValueError:
            print(f"错误：AI玩家 {self.position} 手牌中没有 {card}")

    def _player_play_card_object(self, card: UnoCard):
        """玩家打牌对象"""
        try:
            self.uno_list.remove(card)
        except ValueError:
            if self.game and self.game.gui:
                self.game.gui.show_message_box("错误", f"玩家 {self.position} 手牌中没有 {card}")
            else:
                print(f"错误：玩家 {self.position} 手牌中没有 {card}")

    # ==================== 弃牌函数 ====================
    def fold_card(self,indices:list):
        """统一的弃牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._ai_fold_card(indices)
        else:
            return self._player_fold_card(indices)

    def _ai_fold_card(self,indices:list):
        """AI弃牌"""
        # 从大到小排序，防止删除时索引变化
        indices.sort(reverse=True)
        cards_folded = []
        for i in indices:
            if i < len(self.uno_list):
                cards_folded.append(self.uno_list.pop(i))
        return cards_folded

    def _player_fold_card(self,indices:list):
        """玩家弃牌"""
        # 从大到小排序，防止删除时索引变化
        indices.sort(reverse=True)
        cards_folded = []
        for i in indices:
            if i < len(self.uno_list):
                cards_folded.append(self.uno_list.pop(i))
        return cards_folded

    def fold_card_objects(self, cards_to_fold: List[UnoCard]):
        """统一的弃牌对象入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._ai_fold_card_objects(cards_to_fold)
        else:
            return self._player_fold_card_objects(cards_to_fold)

    def _ai_fold_card_objects(self, cards_to_fold: List[UnoCard]):
        """AI根据卡牌对象弃牌"""
        cards_folded = []
        for card in cards_to_fold:
            try:
                self.uno_list.remove(card)
                cards_folded.append(card)
            except ValueError:
                print(f"警告: AI尝试弃掉不存在的牌 {card}")
        return cards_folded

    def _player_fold_card_objects(self, cards_to_fold: List[UnoCard]):
        """玩家根据卡牌对象弃牌"""
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

    def check_card(self,card:UnoCard):
        """统一的卡牌检查入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._check_ai_card(card)
        else:
            return self._check_player_card(card)

    def _check_ai_card(self,card:UnoCard):
        """AI卡牌检查"""
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

    def _check_player_card(self,card:UnoCard):
        """玩家卡牌检查"""
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
        """统一的检查可出牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return self._ai_can_play_any_card()
        else:
            return self._player_can_play_any_card()

    def _ai_can_play_any_card(self) -> bool:
        """AI检查手牌中是否有任何可以合法打出的牌"""
        for card in self.uno_list:
            if self.check_card(card):
                return True
        return False

    def _player_can_play_any_card(self) -> bool:
        """玩家检查手牌中是否有任何可以合法打出的牌"""
        for card in self.uno_list:
            if self.check_card(card):
                return True
        return False