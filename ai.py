import requests
import os
import json
import sys
import random
from typing import List, TYPE_CHECKING
if TYPE_CHECKING:
    from game import Game
    from mr_cards import MrCard
from card import UnoCard
from util import PlayAction

HAND_LIMIT = 20

class AI:
    def __init__(self, ai_level='rule_based'):
        self.ai_level = ai_level
        if self.ai_level == 'llm_based':
            self.llm_ai = DeepSeekAI()

    def choose_action(self, player, game_state):
        """
        AI的核心决策函数
        player: 当前AI玩家对象
        game_state: 包含游戏当前状态的字典
        """
        if self.ai_level == 'rule_based':
            return self.rule_based_choice(player, game_state)
        elif self.ai_level == 'llm_based':
            return self.llm_ai.choose_action(player, game_state)
        return None, None

    def choose_wild_color(self, player):
        """Determines the best color to switch to when playing a wild card."""
        colors = ['red', 'blue', 'green', 'yellow']
        color_counts = {color: 0 for color in colors}
        for card in player.uno_list:
            if card.color in color_counts:
                color_counts[card.color] += 1
        
        # Return the color with the highest count
        if not any(color_counts.values()):
            return random.choice(colors) # No colored cards, pick randomly
            
        return max(color_counts, key=color_counts.get)

    def rule_based_choice(self, player, game_state):
        """
        A more advanced rule-based AI.
        """
        valid_cards = []
        for i, card in enumerate(player.uno_list):
            if player.check_card(card):
                valid_cards.append((i, card))

        if not valid_cards:
            return 'draw', None

        # --- Strategic Decision Making ---

        # 1. Check if any opponent is close to winning (has 1 card)
        opponents = [p for p in game_state['players'] if p.position != player.position]
        player_to_stop = None
        for p in opponents:
            if len(p.uno_list) == 1:
                player_to_stop = p
                break
        
        if player_to_stop:
            # Try to play a +2, +4, skip, or reverse card
            action_cards = [(i, c) for i, c in valid_cards if c.type in ['draw2', 'wild_draw4', 'skip', 'reverse']]
            if action_cards:
                # Prioritize +4, then +2, then skip, then reverse
                for t in ['wild_draw4', 'draw2', 'skip', 'reverse']:
                    for i, c in action_cards:
                        if c.type == t:
                            # print(f"AI strategy: Stopping player {player_to_stop.position+1} with {c.type}")
                            return 'play', i

        # 2. If must respond to a draw chain, play +4 or +2
        if game_state['draw_n'] > 0:
            plus_cards = [(i, c) for i, c in valid_cards if c.type in ['draw2', 'wild_draw4']]
            if plus_cards:
                # Prefer +4 over +2
                for i, c in plus_cards:
                    if c.type == 'wild_draw4':
                        return 'play', i
                return 'play', plus_cards[0][0]

        # 3. Avoid breaking a color combo if possible. Try to play a card that matches the current color.
        cards_matching_color = [(i, c) for i, c in valid_cards if c.color == game_state['current_color']]
        if cards_matching_color:
            # Of the matching color cards, prefer number cards to get rid of them
            num_cards = [(i, c) for i, c in cards_matching_color if c.type == 'number']
            if num_cards:
                # Play highest value number card
                num_cards.sort(key=lambda item: item[1].value, reverse=True)
                return 'play', num_cards[0][0]
            # If no number cards, play the first available function card
            return 'play', cards_matching_color[0][0]

        # 4. If no card matches current color, check for matching numbers/symbols
        last_card = game_state['last_card']
        if last_card:
            cards_matching_value = [(i, c) for i, c in valid_cards if (c.type != 'number' and c.type == last_card.type) or (c.type == 'number' and last_card.type == 'number' and c.value == last_card.value)]
            if cards_matching_value:
                # This will change the color, which is fine since we couldn't match it anyway
                return 'play', cards_matching_value[0][0]

        # 5. If still no move, play a wild card if available
        wild_cards = [(i, c) for i, c in valid_cards if c.type in ['wild', 'wild_draw4']]
        if wild_cards:
            return 'play', wild_cards[0][0]

        # 6. As a last resort, play the first valid card (should be covered by above, but for safety)
        return 'play', valid_cards[0][0]

    def decide_jianxiong(self, player, cards_to_gain):
        """AI decides whether to use JianXiong skill."""
        # Simple rule: always use it if it's a +4.
        # For +2, maybe consider hand size. For now, always take.
        return True

    def decide_qixi_target(self, player, all_players):
        """AI decides who to target with QiXi skill."""
        # Simple rule: target the player with the fewest cards.
        opponents = [p for p in all_players if p != player]
        if not opponents:
            return None
        
        opponents.sort(key=lambda p: len(p.uno_list))
        return opponents[0]

# ==================== AI玩家专用函数 ====================
class AIPlayer:
    """AI玩家的专用函数类"""
    
    @staticmethod
    def ai_choose_cards_to_discard(player, num_to_discard: int) -> List[UnoCard]:
        """AI选择要弃置的牌的逻辑。简单策略：优先弃置高点数数字牌。"""
        # 按点数降序排序，优先保留功能牌和低点数牌
        sorted_hand = sorted(player.uno_list, key=lambda c: c.value if c.type == 'number' else -1, reverse=True)
        return sorted_hand[:num_to_discard]

    @staticmethod
    def ai_draw_cards(player, num_to_draw: int, from_deck: bool = True, specific_cards: List[UnoCard] = None, is_skill_draw: bool = False):
        """AI摸牌的核心逻辑"""
        if not player.game:
            return

        cards_drawn = []
        if specific_cards:
            cards_drawn = specific_cards
        elif from_deck:
            for _ in range(num_to_draw):
                # 检查手牌上限，如果已达到上限则停止摸牌
                if len(player.uno_list) >= player.hand_limit:
                    print(f"AI玩家 {player.position+1} ({player.mr_card.name}) 手牌已达上限({player.hand_limit})，停止摸牌。")
                    # 记录到历史：达到手牌上限，停止摸牌
                    if player.game and not is_skill_draw:
                        player.game.add_history(f"{player.mr_card.name} 手牌已达上限({player.hand_limit})，停止摸牌")
                    break
                if player.game.unocard_pack:
                    cards_drawn.append(player.game.unocard_pack.pop())
                else:
                    break
        
        if not cards_drawn:
            return

        player.uno_list.extend(cards_drawn)
        # 只有非技能摸牌才显示print信息和历史记录
        if not is_skill_draw:
            print(f"AI玩家 {player.position+1} 获得了 {len(cards_drawn)} 张牌。")
            # 历史记录：摸牌（技能发动的摸牌不记录，避免重复）
            if player.game:
                player.game.add_history(f"{player.mr_card.name} 摸了 {len(cards_drawn)} 张牌")
        # 摸牌后，立即检查手牌上限
        player.game.check_hand_limit_and_discard_if_needed(player)

    @staticmethod
    def ai_handle_forced_draw(player):
        """AI处理被动响应摸牌（例如被+2/+4）"""
        # 先完成强制摸牌（遵守手牌上限）
        actual_draw_n = min(player.game.draw_n, player.hand_limit - len(player.uno_list))
        if actual_draw_n > 0:
            AIPlayer.ai_draw_cards(player, actual_draw_n)
            # 如果实际摸牌数少于要求的摸牌数，说明达到了手牌上限
            if actual_draw_n < player.game.draw_n:
                if player.game:
                    player.game.add_history(f"{player.mr_card.name} 强制摸牌时达到手牌上限({player.hand_limit})，只摸了 {actual_draw_n} 张牌")
        else:
            # 如果已经达到手牌上限，记录到历史
            if player.game:
                player.game.add_history(f"{player.mr_card.name} 手牌已达上限({player.hand_limit})，无法强制摸牌")
        
        # 强制摸牌完成后，检查是否有技能可以响应（如奸雄）
        jianxiong_skill = next((s for s in player.mr_card.skills if s.__class__.__name__ == 'JianXiong'), None)
        if jianxiong_skill and player.game.draw_chain_cards:
            # AI决策是否发动奸雄
            if player.game.ai_handler.decide_jianxiong(player, player.game.draw_chain_cards):
                player.game.execute_skill_jianxiong(player)
        
        player.game.draw_n = 0
        player.game.draw_chain_cards.clear()

    @staticmethod
    def ai_play(player, card_idx: int, wusheng_active: bool = False):
        """AI主动出牌"""
        is_valid, message, card_to_play, original_card = player.validate_play(card_idx, wusheng_active)
        if not is_valid:
            print(f"AI出牌无效: {message}")
            return

        # AI选择颜色（简化逻辑，默认红色）
        color_choice = 'red' if card_to_play.type in ['wild', 'wild_draw4'] else None

        # 对于reverse卡牌，需要特殊处理target_player
        if original_card.type == 'reverse':
            # 计算方向改变后的下一个玩家
            new_dir = -player.game.dir  # 方向改变后的方向
            next_pos_after_reverse = (player.position + new_dir) % player.game.player_num
            target_player = player.game.player_list[next_pos_after_reverse]
        else:
            target_player = player.game.get_next_player(player.position)
        
        action = PlayAction(
            card=original_card,
            source=player,
            target=target_player,
            color_choice=color_choice,
            virtual_card=card_to_play if wusheng_active and original_card.color == 'red' else None
        )
        # 历史记录：出牌信息
        base_record = f"{player.mr_card.name} - {original_card} -> {target_player.mr_card.name}"
        player.game.add_history(base_record)
        player.game.turn_action_taken = True
        player.game.process_play_action(action)
        
        # 检查是否是最后一张黑色牌，如果是则摸一张
        if hasattr(player, '_last_card_is_black') and player._last_card_is_black:
            AIPlayer.ai_draw_cards(player, 1)
            player.game.add_history(f"{player.mr_card.name} 打出最后一张黑色牌，摸了一张牌")
            player._last_card_is_black = False  # 重置标记

    @staticmethod
    def _validate_ai_play(player, card_idx: int, wusheng_active: bool):
        """AI出牌验证"""
        if card_idx is None or card_idx >= len(player.uno_list):
            return False, "无效的卡牌索引。", None, None

        original_card = player.uno_list[card_idx]
        card_to_play = original_card
        if wusheng_active and original_card.color == 'red':
            from card import UnoCard
            card_to_play = UnoCard('draw2', 'red', 0)

        if not player.check_card(card_to_play):
            return False, "这张牌不符合出牌规则。", None, None

        # 最后一张牌是黑色牌的特殊处理：允许出牌，但出牌后需要摸一张
        if len(player.uno_list) == 1 and card_to_play.type in ['wild', 'wild_draw4']:
            # 标记这是最后一张黑色牌，需要在出牌后摸一张
            player._last_card_is_black = True

        return True, "有效出牌", card_to_play, original_card

    @staticmethod
    def _activate_ai_skill(player, skill_name: str):
        """AI技能发动"""
        if player.game:
            # 详细历史记录
            for skill in player.mr_card.skills:
                if skill.name == skill_name:
                    if hasattr(skill, 'use'):
                        # 武圣等主动技能
                        text = skill.use(player.uno_list[0]) if player.uno_list else None
                        if text:
                            player.game.add_history(text)
                    elif hasattr(skill, 'record_history'):
                        # 反间等特殊技能
                        # 具体参数在_fanjian流程中写入
                        pass
                    elif skill_name != '缔盟':  # 缔盟技能有自己的历史记录，不需要通用描述
                        player.game.add_history(f"{player.mr_card.name} 发动[{skill_name}] 效果：{skill.description}")
        if skill_name == '反间':
            AIPlayer._activate_ai_fanjian(player)
        elif skill_name == '缔盟':
            AIPlayer._activate_ai_dimeng(player)
        # ... 其他技能可以在此添加
        else:
            print(f"AI技能 [{skill_name}] 的逻辑尚未完全移至Player。")

    @staticmethod
    def _activate_ai_fanjian(player):
        """AI反间技能处理"""
        # AI反间逻辑：选择一张非黑色牌给目标玩家
        # 1. 过滤出非黑色牌
        non_black_cards = [card for card in player.uno_list if card.color != 'black']
        if not non_black_cards:
            print(f"AI {player.mr_card.name} 没有非黑色牌，无法发动【反间】")
            return
        
        # 2. 选择一张非黑色牌（AI选择第一张）
        card_to_give = non_black_cards[0]
        
        # 3. 选择目标（AI选择手牌最少的对手）
        opponents = [p for p in player.game.player_list if p != player]
        if not opponents:
            print(f"AI {player.mr_card.name} 没有可选择的对手")
            return
        
        target = min(opponents, key=lambda p: len(p.uno_list))
        
        # 4. 结算"给牌"动作
        player.uno_list.remove(card_to_give)
        target.uno_list.append(card_to_give)
        
        # 5. 目标弃牌
        color_to_discard = card_to_give.color
        cards_to_discard_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
        if cards_to_discard_indices:
            discarded_cards = target.fold_card(cards_to_discard_indices)
        else:
            discarded_cards = []
        
        # 6. 记录历史
        message = f"AI {player.mr_card.name} 发动【反间】，将 {card_to_give} 给了 {target.mr_card.name}"
        print(message)
        if player.game:
            player.game.add_history(f"{player.mr_card.name} 发动[反间]，将 [{card_to_give}] 给了 {target.mr_card.name}")
        
        # 7. 检查目标胜利条件
        if len(target.uno_list) == 0:
            player.game.game_over = True
            if player.game.gui:
                player.game.gui.show_winner_and_exit(target)
            return
        
        # 8. 刷新游戏界面
        player.game.turn_action_taken = True
        if player.game.gui:
            player.game.gui.show_game_round()

    @staticmethod
    def _activate_ai_dimeng(player):
        """AI缔盟技能处理"""
        # 1. 检查手牌数是否大于6（技能失效条件）
        if len(player.uno_list) > 6:
            print(f"AI {player.mr_card.name} 手牌数大于6，【缔盟】技能失效")
            return

        # 2. 选择两名其他玩家（AI选择手牌数差异最大的两个对手）
        opponents = [p for p in player.game.player_list if p != player]
        if len(opponents) < 2:
            print(f"AI {player.mr_card.name} 没有足够的对手，无法发动【缔盟】")
            return
        
        # 选择手牌数差异最大的两个对手
        opponents.sort(key=lambda p: len(p.uno_list))
        target1 = opponents[0]  # 手牌最少的
        target2 = opponents[-1]  # 手牌最多的

        # 3. 计算手牌数之差
        hand_diff = abs(len(target1.uno_list) - len(target2.uno_list))
        
        # 4. 摸x张牌（x为手牌数之差）
        if hand_diff > 0:
            AIPlayer.ai_draw_cards(player, hand_diff, is_skill_draw=True)
            print(f"AI {player.mr_card.name} 发动【缔盟】，摸了 {hand_diff} 张牌")

        # 5. 交换两名目标玩家的手牌
        temp_hand = target1.uno_list.copy()
        target1.uno_list = target2.uno_list.copy()
        target2.uno_list = temp_hand

        # 6. 记录历史
        message = f"AI {player.mr_card.name} 发动【缔盟】，{target1.mr_card.name} 和 {target2.mr_card.name} 交换了手牌"
        print(message)
        if player.game:
            player.game.add_history(f"{player.mr_card.name} 发动[缔盟]，{target1.mr_card.name} 和 {target2.mr_card.name} 交换了手牌")

        # 7. 检查胜利条件
        if len(target1.uno_list) == 0:
            player.game.game_over = True
            if player.game.gui:
                player.game.gui.show_winner_and_exit(target1)
            return
        if len(target2.uno_list) == 0:
            player.game.game_over = True
            if player.game.gui:
                player.game.gui.show_winner_and_exit(target2)
            return

        # 8. 刷新游戏界面
        player.game.turn_action_taken = True
        if player.game.gui:
            player.game.gui.show_game_round()

    @staticmethod
    def _ai_choose_fanjian_color(player):
        """AI反间颜色选择"""
        # AI默认选择红色
        return 'red'

    @staticmethod
    def _check_ai_jump(player, last_card: UnoCard) -> List:
        """AI跳牌检查"""
        potential_jumps = []
        if not last_card:
            return potential_jumps

        for i, card in enumerate(player.uno_list):
            # 1. 标准跳牌: 颜色、类型、数值完全一致（黑色牌不能跳牌）
            if (card.color == last_card.color and card.type == last_card.type and card.value == last_card.value and 
                card.type not in ['wild', 'wild_draw4']):
                potential_jumps.append({'original_card': card, 'virtual_card': None})

            # 2. 武圣跳牌:  红色牌 跳 红色+2
            if last_card.type == 'draw2' and last_card.color == 'red':
                if player.mr_card and any(s.name == '武圣' for s in player.mr_card.skills):
                    if card.color == 'red' and card.type not in ['wild', 'wild_draw4']:
                        from card import UnoCard # 确保 UnoCard 被导入
                        virtual_card = UnoCard('draw2', 'red', 0)
                        potential_jumps.append({'original_card': card, 'virtual_card': virtual_card})
        
        return potential_jumps

    @staticmethod
    def _ai_play_a_hand(player, i: int):
        """AI打牌"""
        return player.uno_list.pop(i)

    @staticmethod
    def _ai_play_card_object(player, card: UnoCard):
        """AI打牌对象"""
        try:
            player.uno_list.remove(card)
        except ValueError:
            print(f"错误：AI玩家 {player.position} 手牌中没有 {card}")

    @staticmethod
    def _ai_fold_card(player, indices: list):
        """AI弃牌"""
        # 从大到小排序，防止删除时索引变化
        indices.sort(reverse=True)
        cards_folded = []
        for i in indices:
            if i < len(player.uno_list):
                cards_folded.append(player.uno_list.pop(i))
        return cards_folded

    @staticmethod
    def _ai_fold_card_objects(player, cards_to_fold: List[UnoCard]):
        """AI根据卡牌对象弃牌"""
        cards_folded = []
        for card in cards_to_fold:
            try:
                player.uno_list.remove(card)
                cards_folded.append(card)
            except ValueError:
                print(f"警告: AI尝试弃掉不存在的牌 {card}")
        return cards_folded

    @staticmethod
    def _check_ai_card(player, card: UnoCard):
        """AI卡牌检查"""
        last_card = player.game.playedcards.get_one()
        cur_color = player.game.cur_color
        
        # 检查+2/+4叠加规则：只有在draw_n > 0时才应用
        if player.game.draw_n > 0 and last_card:
            if last_card.type == 'draw2':
                # +2上只能叠+2或+4
                if card.type not in ['draw2', 'wild_draw4']:
                    return False
            elif last_card.type == 'wild_draw4':
                # +4上只能叠+4
                if card.type != 'wild_draw4':
                    return False
        
        # 检查倾国技能
        if player.mr_card:
            qingguo_skill = next((s for s in player.mr_card.skills if s.name == '倾国'), None)
            if qingguo_skill and card.color == 'blue':
                return True # 蓝色牌可以当任何颜色出

            # 检查龙胆技能
            longdan_skill = next((s for s in player.mr_card.skills if s.name == '龙胆'), None)
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

    @staticmethod
    def _ai_can_play_any_card(player) -> bool:
        """AI检查手牌中是否有任何可以合法打出的牌"""
        for card in player.uno_list:
            if player.check_card(card):
                return True
        return False

    @staticmethod
    def ai_choose_to_use_skill(player, skill_name: str) -> bool:
        """AI选择是否使用技能"""
        # AI总是选择使用技能（如果有的话）
        return True

class DeepSeekAI:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """
        从配置文件加载API密钥和基础URL。
        config_path: 配置文件路径
        """
        base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        config_path = os.path.join(base_dir, 'config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.api_key = config.get('ai_api_key', '')
        self.api_url = config.get('ai_base_url', '')

    def choose_action(self, player, game_state):
        """
        调用 deepseek API 生成电脑玩家出牌决策。
        player: 当前AI玩家对象
        game_state: 包含游戏当前状态的字典
        返回：(action_type, card_index)
        """
        prompt = self.construct_prompt(player, game_state)
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        }
        response = requests.post(self.api_url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            try:
                answer = result['choices'][0]['message']['content']
                # 解析AI的返回结果，例如 "play 3" or "draw"
                parts = answer.strip().split()
                action_type = parts[0]
                card_index = int(parts[1]) if len(parts) > 1 else None
                return action_type, card_index
            except Exception:
                # 如果LLM返回错误，使用规则AI作为后备
                return AI(ai_level='rule_based').rule_based_choice(player, game_state)
        else:
            print("AI请求失败：", response.text)
            # 如果API请求失败，使用规则AI作为后备
            return AI(ai_level='rule_based').rule_based_choice(player, game_state)

    def construct_prompt(self, player, game_state):
        """构建发送给LLM的详细prompt"""
        
        hand_str = ", ".join([str(c) for c in player.uno_list])
        other_players_info = []
        for p in game_state['players']:
            if p.position != player.position:
                other_players_info.append(f"玩家{p.position+1}({p.mr_card.name}) 有 {len(p.uno_list)} 张手牌.")

        prompt = f"""
        你是一个UNO纸牌游戏的AI专家，正在玩一个带有三国杀武将技能的特殊版本。
        你的目标是赢得游戏。请根据当前游戏状态，做出最佳决策。

        # 游戏规则概要:
        - 你需要打出与桌上最后一张牌颜色或数字/功能相同的牌。
        - 黑色万能牌可以随时出，并指定下家出牌的颜色。
        - +2, +4牌会让下家摸牌，可以叠加。
        - 你的武将技能: {player.mr_card.name} - {player.mr_card.skill_description}

        # 当前游戏状态:
        - 你的身份: 玩家{player.position+1}, 武将: {player.mr_card.name}, 势力: {player.team}
        - 你的手牌 ({len(player.uno_list)}张): {hand_str}
        - 场上最后一张牌: {str(game_state['last_card'])}
        - 当前生效颜色: {game_state['current_color']}
        - 当前牌堆顶是否需要摸牌: {game_state['draw_n']} 张
        - 游戏进行方向: {'顺时针' if game_state['game_direction'] == 1 else '逆时针'}
        - 其他玩家信息: {' '.join(other_players_info)}

        # 你的任务:
        根据你的手牌和场上情况，决定你的行动。你有以下选择：
        1. 'play card_index': 打出一张牌。'card_index'是你手牌列表中的索引（从0开始）。
           - 你必须确保你出的牌是有效的。
           - 如果你出的是万能牌，请在下一行指定颜色, 例如: 'play 3\ncolor red'
        2. 'draw': 如果你没有可以出的牌，选择摸一张牌。
        3. 'use_skill skill_name': 使用你的武将技能（如果条件满足）。

        请只返回你的决策，格式为 'action card_index' 或 'draw'。不要包含任何解释。
        例如: 'play 2' 或 'draw'
        """
        return prompt.strip()

    def choose_card(self, uno_list, last_card, cur_color):
        """
        根据当前的手牌，最后一张牌和当前颜色，选择要出的牌。
        uno_list: 当前玩家的手牌
        last_card: 场上最后一张牌
        cur_color: 当前生效颜色
        返回: 要出的牌的索引
        """
        # 先尝试出与当前颜色相同的牌
        for i, card in enumerate(uno_list):
            if card.color == cur_color or card.color == 'black':
                return i
        
        # 如果没有符合的牌，尝试出与最后一张牌数字相同的牌
        for i, card in enumerate(uno_list):
            if card.number == last_card.number:
                return i
        
        # 最后随机摸一张牌
        return None
