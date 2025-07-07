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

class MRCard:
    def __init__(self, team: str, skill: Callable):
        self.team = team
        self.skill = skill