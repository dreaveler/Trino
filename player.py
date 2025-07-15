from card import UnoCard, MRCard
from typing import List, Callable
from enum import Enum

class Player:
    #初始化玩家的时候似乎不应该给定position和team
    def __init__(self, position, team:str):
        from game import Game
        self.position = position
        self.team = team
        
        self.uno_list: List[UnoCard] = []
        self.card_num: int = None
        self.mr_card: MRCard = None
        self.state: str = "playing"
        self.game : Game = None
    #拿num张牌,先用print来做游戏提示了 无return
    def get_card(self,num:int):
        for _ in range(num):
            if self.game.unocard_pack:
                self.uno_list.append(self.game.unocard_pack.pop())
            else:
                print("uno牌已被拿完")
                break
    #检查出牌是否合规 return T/F  最好检查一下有没有逻辑错误)
    def check_card(self,card):
        last_card = self.game.playedcards.get_one()
        need_color = last_card.color
        need_type = last_card.type
        need_value = last_card.value
        cur_color = card.color
        cur_type = card.type
        cur_value = card.value
        if need_type == 'wild_draw4':
            if cur_type == 'wild_draw4':
                return True
            else:
                return False  #+4只能叠+4
        if need_type == 'draw2':
            if cur_type == 'draw2' or cur_type == 'wild_draw4':
                return True
            else:
                return False  #+2可以叠+2或+4
        if need_type == 'skip':
            return False  #这里认为同种skip是抢出的逻辑
        if cur_type == 'wild' or cur_type == 'wild_draw4':  #黑色牌可以任意
            return True
        if cur_color !=  need_color:   #颜色不一样时只有类型相同且数字相同才能出
            if need_type == cur_type and need_value == cur_value:
                return True
            return False
        return True   #这里之后都是同色的逻辑了  reverse的逻辑应该反应在game里  ban的逻辑同样且上面也写了  

    #出牌 无return 如果出牌合规则回合结束 否则无视发生 这里单指正常出一张   需要一个flag来说明回合结束? 
    def play_a_hand(self,location:int):
        card = self.uno_list.pop(location)
        if self.check_card(card):
            #设定颜色
            if card.type == 'wild' or card.type == 'wild_draw4':
                color = input("choose a color from red , green , blue , yellow")
                self.game.cur_color = color
            self.game.playedcards.add_card(card)
            self.game.cur_color = card.color
        else:
            print("出牌不符合规范！")

    #弃牌 无return 输入position:List 弃的牌不加入弃牌堆
    def fold_card(self,pos:List[int]):
        for index in sorted(pos,reverse=True):
            self.uno_list.pop(index)
    #检测无法出牌 返回T/F
    def check_cannot_play_card(self):
        for card in self.uno_list:
            if self.check_card(card):
                return False
        return True
    #跳牌 无return 在game中每次有人出牌后调用 如果不能跳牌则无事发生 如果可以则询问
    def skip_card(self):
        card = self.game.playedcards.get_one()
        #need more
    
