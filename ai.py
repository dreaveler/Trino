import requests
import os
import json
import sys

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
        self.api_key = config.get('ai_api_key', self.api_key)
        self.api_url = config.get('ai_base_url', self.api_url)

    def choose_card(self, uno_list, last_card, cur_color):
        """
        调用 deepseekapi 生成电脑玩家出牌决策。
        uno_list: 当前手牌列表（字符串描述）
        last_card: 场上最后一张牌（字符串描述）
        cur_color: 当前有效颜色
        返回：推荐出的牌索引（int）
        """
        prompt = f"你是UNO游戏的AI玩家。你的手牌是：{uno_list}，场上最后一张牌是：{last_card}，当前有效颜色是：{cur_color}。请根据规则选择你要出的牌的序号（如果不能出牌请返回-1），只返回数字，不要解释。"
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
                return int(answer.strip())
            except Exception:
                return -1
        else:
            print("AI请求失败：", response.text)
            return -1
