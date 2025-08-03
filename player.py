from __future__ import annotations
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from game import Game
    from mr_cards import MrCard
from card import UnoCard
from util import PlayAction
from PyQt5.QtWidgets import QApplication
from ai import AIPlayer

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
                self.game.execute_skill_jianxiong(self)
        
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

        # 对于reverse卡牌，需要特殊处理target_player
        if original_card.type == 'reverse':
            # 计算方向改变后的下一个玩家
            new_dir = -self.game.dir  # 方向改变后的方向
            next_pos_after_reverse = (self.position + new_dir) % self.game.player_num
            target_player = self.game.player_list[next_pos_after_reverse]
        else:
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
        self.game.process_play_action(action)
        
        # 检查是否是最后一张黑色牌，如果是则摸一张
        if hasattr(self, '_last_card_is_black') and self._last_card_is_black:
            self.player_draw_cards(1)
            self.game.add_history(f"{self.mr_card.name} 打出最后一张黑色牌，摸了一张牌")
            self._last_card_is_black = False  # 重置标记

    # ==================== 通用函数 ====================
    def draw_cards(self, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """统一的摸牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            AIPlayer.ai_draw_cards(self, num_to_draw, from_deck, specific_cards, is_skill_draw)
        else:
            self.player_draw_cards(num_to_draw, from_deck, specific_cards, is_skill_draw)

    def handle_forced_draw(self):
        """统一的强制摸牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            AIPlayer.ai_handle_forced_draw(self)
        else:
            self.player_handle_forced_draw()

    def play(self, card_idx: int, wusheng_active: bool = False):
        """统一的出牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            AIPlayer.ai_play(self, card_idx, wusheng_active)
        else:
            self.player_play(card_idx, wusheng_active)

    def validate_play(self, card_idx: int, wusheng_active: bool):
        """统一的出牌验证入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return AIPlayer._validate_ai_play(self, card_idx, wusheng_active)
        else:
            return self._validate_player_play(card_idx, wusheng_active)

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
            AIPlayer._activate_ai_skill(self, skill_name)
        else:
            self._activate_player_skill(skill_name)

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
        """玩家反间技能处理"""
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

    def _activate_player_dimeng(self):
        """玩家缔盟技能处理"""
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

        # 8. 刷新整个游戏界面
        self.game.turn_action_taken = True # 发动技能视为已行动
        self.game.gui.show_game_round()

    def choose_fanjian_color_from_gui(self):
        """统一的反间颜色选择入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return AIPlayer._ai_choose_fanjian_color(self)
        else:
            return self._player_choose_fanjian_color()

    def _player_choose_fanjian_color(self):
        """玩家反间颜色选择"""
        if not self.game.gui:
            return 'red'  # 非GUI模式默认
        return self.game.gui.choose_fanjian_color_dialog()

    def check_for_jump(self, last_card: UnoCard) -> List:
        """统一的跳牌检查入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return AIPlayer._check_ai_jump(self, last_card)
        else:
            return self._check_player_jump(last_card)

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
    def play_a_hand(self, i: int):
        """统一的打牌入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return AIPlayer._ai_play_a_hand(self, i)
        else:
            return self._player_play_a_hand(i)
    
    def _player_play_a_hand(self, i: int):
        """玩家打牌"""
        return self.uno_list.pop(i)
    
    def play_card_object(self, card: UnoCard):
        """统一的打牌对象入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            AIPlayer._ai_play_card_object(self, card)
        else:
            self._player_play_card_object(card)

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
    def fold_card(self, indices):
        """统一的弃牌入口，根据玩家类型调用对应函数"""
        # 确保indices是列表
        if not isinstance(indices, list):
            indices = [indices]
        
        if self.is_ai:
            return AIPlayer._ai_fold_card(self, indices)
        else:
            return self._player_fold_card(indices)

    def _player_fold_card(self, indices: list):
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
            return AIPlayer._ai_fold_card_objects(self, cards_to_fold)
        else:
            return self._player_fold_card_objects(cards_to_fold)

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

    def check_card(self, card: UnoCard):
        """统一的卡牌检查入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return AIPlayer._check_ai_card(self, card)
        else:
            return self._check_player_card(card)

    def _check_player_card(self, card: UnoCard):
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
            return AIPlayer._ai_can_play_any_card(self)
        else:
            return self._player_can_play_any_card()

    def _player_can_play_any_card(self) -> bool:
        """玩家检查手牌中是否有任何可以合法打出的牌"""
        for card in self.uno_list:
            if self.check_card(card):
                return True
        return False

    def choose_cards_to_discard(self, num_to_discard: int) -> List[int]:
        """玩家选择要弃置的牌（返回牌在uno_list中的索引列表）"""
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
        """统一的技能使用选择入口，根据玩家类型调用对应函数"""
        if self.is_ai:
            return AIPlayer.ai_choose_to_use_skill(self, skill_name)
        else:
            return self._player_choose_to_use_skill(skill_name)

    def _player_choose_to_use_skill(self, skill_name: str) -> bool:
        """玩家选择是否使用技能"""
        if self.game and self.game.gui:
            return self.game.gui.ask_yes_no_question("发动技能", f"是否发动【{skill_name}】？")
        else:
            choice = input(f"是否发动【{skill_name}】？(y/n): ")
            return choice.lower() == 'y'