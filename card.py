from typing import Callable
from enum import Enum

class Color(Enum):
    Nocolor = 0
    Red = 1
    Blue = 2
    Yellow = 3
    Green = 4
    Wild = 5
    
    
class Type(Enum):
    Notype = 0
    Number = 1
    Reverse = 2
    Ban = 3
    AddTwo = 4
    WildChangeColor = 5
    WildAddFour = 6


class UnoCard:
    """UNO Card class representing a card in the game UNO.
    Attributes:
        type (str): The type of the card (e.g., "number", "action", "wild").
        color (str): The color of the card (e.g., "red", "blue", "green", "yellow").
        value (int): The value of the card, if applicable (e.g., 0-9 for number cards, skip, reverse etc.).
    """
    def __init__(self, type: str, color: str, value: int):
        self.type = type
        self.color = color
        self.value = value

class MRCard:
    def __init__(self, team: str, skill: Callable):
        self.team = team
        self.skill = skill
