from player import Player
from typing import List, Callable
from card import UnoCard

class Game:
    def __init__(self,player_num:int):
        self.player_num = player_num

        self.playere_list: List[Player] = []
        self.unocard_pack:List[UnoCard] = []
        self.unocard_discard_pile:List[UnoCard] = []

    def create_unocard_pack(self):
        pass
    #需要写一套uno牌