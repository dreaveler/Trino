from enum import Enum

class Color(Enum):
    Nocolor = 0
    Red = 1
    Blue = 2
    Yellow = 3
    Green = 4
    Wild = 5
class Type(Enum):
    Notype = 0
    Number = 1
    Reverse = 2
    Ban = 3
    AddTwo = 4
    WildChangeColor = 5
    WildAddFour = 6

class UnoCard:
    def __init__(self,color:Color,type:Type,num:int):
        self.color = color
        self.type = type
        self.number = num
