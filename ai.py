import requests
import os

class DeepSeekAI:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('sk-d072d2e34a2b42e5ba3ab148b098ca5a')
        self.api_url = 'https://api.deepseek.com/v1/chat/completions'

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

# 示例用法
if __name__ == "__main__":
    ai = DeepSeekAI(api_key="你的deepseekapi-key")
    uno_list = ["red number 3", "blue draw2 0", "green number 5"]
    last_card = "red number 3"
    cur_color = "red"
    idx = ai.choose_card(uno_list, last_card, cur_color)
    print("AI选择的出牌序号：", idx)
