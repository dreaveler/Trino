from card import UnoCard
from player import Player

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