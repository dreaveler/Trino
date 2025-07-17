from card import UnoCard
from player import Player
from game import Game

#本文件将编写一些判定牌的逻辑
class Judge:
    def __init__(self):
        self.need_judging=True#当前是否需要被判定，默认为true
        self.transfer=False#是否将被转移

class LeBuSiShu(Judge):
    def __init__(self):
        super().__init__()
    def __call__(self, player:Player, card:UnoCard):
        if card.color!='red':
            player.get_card(1)

class BingLiangCunDuan(Judge):#兵粮的need_judging可能为false
    def __init__(self):
        super().__init__()
    def __call__(self, player:Player, card:UnoCard):
        if card.color!='blue':
            pass#这部分的交互还没想好

class Lightening(Judge):
    def __init__(self):
        super().__init__()
    def __call__(self, player:Player, card:UnoCard):
        if card.color=='wild' or card.color=='wild_draw4':
            player.get_card(10)
        else:
            self.transfer=True

class Duel:
    def __init__(self,color,player1,player2):
        self.color=color
        self.player1=player1
        self.player2=player2
        self.duel_cards=[]
    def __call__(self):
        pass#没想好如何让双方轮流出牌

class NanManRuQin:
    def __call__(self, caller:Player, game:Game):
        for player in game.player_list:
            if player!=caller:
                #和决斗一样没想好如何让大家轮流出牌并给出一个bool,这里应该有一个if
                player.get_card(4)