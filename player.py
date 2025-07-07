from card import UnoCard, MRCard
from typing import List, Callable
from enum import Enum
from game import Game

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
        self.game : Game = None
    #拿num张牌,先用print来做游戏提示了
    def get_card(self,num:int):
        for _ in range(num):
            if not self.game.unocard_pack:
                self.uno_list.append(self.game.unocard_pack.pop())
            else:
                print("uno牌已被拿完")
    #检查出牌是否合规 未完成  需要写
    def check_card(self,card):
        pass
    #出牌 如果出牌合规则回合结束 否则无视发生     需要一个flag来说明回合结束?
    def play_a_hand(self,location):
        card = self.uno_list.pop(location)
        if self.check_card(card):
            #这里用lmt写的数据结构 
            pass
        else:
            print("出牌不符合规范！")
            pass