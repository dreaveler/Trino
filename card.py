from typing import Callable

class UnoCard:
    """UNO Card class representing a card in the game UNO.
    Attributes:
        type (str): The type of the card (e.g., "number", "action", "wild","wild_draw4").  
        color (str): The color of the card (e.g., "red", "blue", "green", "yellow").
        value (int): The value of the card, if applicable (e.g., 0-9 for number cards, skip, reverse etc.).
    """
    def __init__(self, type: str, color: str, value: int):
        self.type = type
        self.color = color
        self.value = value

    @property
    def content(self):
        """返回卡牌内容的字符串描述，用于UI显示"""
        if self.type == 'number':
            return f"[{self.color}] {self.value}"
        elif self.type == 'reverse':
            return f"[{self.color}] 反转"
        elif self.type == 'skip':
            return f"[{self.color}] 跳过"
        elif self.type == 'draw2':
            return f"[{self.color}] +2"
        elif self.type == 'wild':
            return "[万能牌]"
        elif self.type == 'wild_draw4':
            return "[+4 万能牌]"
        return f"[{self.color}] {self.type}"

    def __str__(self):
        return f"{self.color} {self.type} {self.value}"

class MRCard:
    def __init__(self, name: str, gender: str, skills: list):
        self.name = name          # 武将名
        self.gender = gender      # 性别 'male'/'female'
        self.skills = skills      # 技能列表（Skill对象）

    def use_skill(self, skill_name, *args, **kwargs):
        """发动指定技能"""
        for skill in self.skills:
            if skill.name == skill_name:
                return skill(*args, **kwargs)
        raise ValueError(f"未找到技能: {skill_name}")