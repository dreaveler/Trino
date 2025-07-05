from card import UnoCard, MRCard
from typing import List, Callable

class Player:
    def __init__(self, position, team):
        self.position = position
        self.team = team
        
        self.uno_list: List[UnoCard] = []
        self.mr_card: MRCard = None
        self.state: str = "playing"