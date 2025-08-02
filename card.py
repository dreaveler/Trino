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

    def __str__(self):
        return f"{self.color} {self.type} {self.value}"

    def Key(self):#整理手牌用，用法为uno_list.sort(key=lambda card: card.Key())
        value=self.value
        if self.color=='red':
            value+=100
        elif self.color=='yellow':
            value+=200
        elif self.color=='blue':
            value+=300
        elif self.color == 'green':
            value+=400
        elif self.color=='wild':
            value+=500
        elif self.color=='wild_draw4':
            value+=600
        if self.type=='reverse':
            value+=10
        elif self.type=='skip':
            value+=20
        elif self.type=='draw2':
            value+=30
        return value


class MRCard:
    def __init__(self, team: str, skill: Callable, gender:str):
        self.team = team
        self.skill = skill
        self.gender = gender