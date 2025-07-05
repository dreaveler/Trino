from card import UnoCard, MRCard
from typing import List, Callable
from enum import Enum

class State(Enum):
    playing = 0
    over = 1

class Player:
    def __init__(self, position, team):
        self.position = position
        self.team = team
        
        self.uno_list: List[UnoCard] = []
        self.mr_card: MRCard = None
        self.state: State = State.playing