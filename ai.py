import requests
import os
import json
import sys
import random

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
