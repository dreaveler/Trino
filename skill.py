from card import UnoCard
from player import Player

class Skill:
    def __init__(self, name, description:str, type:str):
        self.name = name
        self.description = description

class WuSheng(Skill):
    def __init__(self):
        super().__init__('武圣', '你的[红色]可以当作[红+2]打出', 'active')
    def __call__(self, card:UnoCard):
        if card.color=='red':
            return UnoCard('draw2','red',0)
        else:
            return card
            print('当前卡牌不符合技能发动条件')

class JiZhi(Skill):
    def __init__(self):
        super().__init__('集智','当你打出[+2]/[+4]/[换色]时，可以弃置1张牌','active')
    def __call__(self, card:UnoCard, player:Player, index):
        if card.type=='draw2' or card.type=='wild_draw4' or card.type=='wild':
            player.fold_card(index)
        else:
            return card
            print('当前卡牌不符合技能发动条件')
            
class QiXi(Skill):
    def __init__(self):
        super().__init__('奇袭','当你打出[绿色]时，你可以指定一名玩家摸1张牌','active')
    def __call__(self, card:UnoCard, other_player:Player):
        if card.color=='green':
            other_player.get_card(1)

class FanJian(Skill):
    def __init__(self):
        super().__init__('反间','你摸1张牌后指定一名玩家，交给其1张非[黑色]手牌，目标玩家需弃置所有与此牌颜色相同的手牌（包括此牌）','active')
    def __call__(self, card:UnoCard,player:Player,other_player:Player):
        player.get_card(1)
        if card.color!='wild' and card.color!='wild_draw4':
            fold_list=[]
            for i in range(len(other_player.uno_list)):
                if other_player.uno_list[i].color==card.color:
                    fold_list.append(i)
            other_player.fold_card(fold_list)