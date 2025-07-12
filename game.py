from player import Player
from typing import List, Callable
from card import UnoCard
from util import PlayedCards
import random

#需要添加处理draw和skip的逻辑 指的是修改flag 在每次出牌后完成这次任务 
class Game:
    def __init__(self,player_num:int,mode:str):
        self.player_num = player_num
        self.playedcards = PlayedCards()
        self.mode = mode

        self.player_list: List[Player] = []
        self.unocard_pack:List[UnoCard] = []

        self.cur_location:int = None
        self.dir: int = 1  #每次加一个dir  1/-1  默认为++
        self.cur_color:str = None
        #flag
        self.draw_n:int = None
        self.skip:bool = None

    #创造牌组
    def create_unocard_pack(self):
        colors = ['red','blue','yellow','green']
        type = ['reverse','skip','draw2']*2
        numbers = [0] + 2*[i for i in range(1,10)]
        for color in colors:
            for number in numbers:
                self.unocard_pack.append(UnoCard("number",color,number))
            for action in type:
                self.unocard_pack.append(UnoCard(action,color,0))
        for _ in range(4):
            self.unocard_pack.append(UnoCard('wild','wild',10))
            self.unocard_pack.append(UnoCard('wild_draw4','wild_draw4',10))
        random.shuffle(self.unocard_pack)
        
    #将玩家加对对局中同时将game赋给玩家
    def add_player(self,player:Player):
        self.player_list.append(player)
        player.game = self
    #发牌！ 每人8张 第一个出牌/主公9张(需要设定模式)
    def deal_cards(self):
        for player in self.player_list:
            player.get_card(8)
        if self.cur_location:
            self.player_list[self.cur_location].get_card(1)
    #开始游戏
    def game_start(self):
        self.create_unocard_pack()
        self.cur_location = random.randint(1,self.player_num)
        self.deal_cards()
        card = self.unocard_pack.pop()
        self.playedcards.add_card(card)
    #结算draw
    def draw_card(self):
        if self.draw_n:
            player = self.player_list[self.cur_location]
            player.get_card(self.draw_n)
            self.draw_n = None
    #结算skip
    def skip_player(self):
        if self.skip:
            self.skip = None
    #结算所有状态
    def clear_state(self):
        self.draw_card()
        self.skip_player()
    #单个玩家回合
    def player_turn(self):
        player = self.player_list[self.cur_location]
        if player.check_cannot_play_card():
            if self.skip or self.draw_n:
                self.clear_state()
            player.get_card(1)
            return
        cards = player.uno_list
        for i,card in enumerate(cards):
            print(f"card{i}: {card}")
        index = input("请选择你出牌的序号")
        player.play_a_hand(int(index))
        self.cur_location = self.cur_location + self.dir
