from card import UnoCard
from collections import deque
#本文件将编写一些可能用到的数据结构

class PlayedCards:
    #创建储存正常打出的牌的deque，maxlen为2，为张昭张纮特殊准备
    def __init__(self):
        self.d=deque(maxlen=2)
    def AddCard(self,card:UnoCard):
        #将打出的牌加入deque
        self.d.append(card)
    def GetOne(self):
        #一般情况，返回最近一个card
        return self.d[-1]
    def GetTwo(self):
        #二张专属，返回最近两个card，type=tuple
        return (self.d[0],self.d[-1])