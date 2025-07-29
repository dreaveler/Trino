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
        self.judging_list:str=[]#所需进行的判定
        self.card_num: int = None
        self.mr_card: MRCard = None
        self.state: str = "playing"
        self.game : Game = None
    def get_card_object(self, card: UnoCard):
        """直接将一个卡牌对象加入手牌"""
        self.uno_list.append(card)

    def play_card_object(self, card: UnoCard):
        """从手牌中移除指定的卡牌对象"""
        # 从后往前找，避免删除错误
        for i in range(len(self.uno_list) - 1, -1, -1):
            if self.uno_list[i] is card:
                self.uno_list.pop(i)
                return
        print(f"警告: {self.name} 手中未找到要打出的牌 {card}")

    def choose_to_use_skill(self, skill_name: str) -> bool:
        """
        询问玩家是否使用技能。
        这应该触发GUI中的一个对话框。
        """
        # 在GUI模式下，这会连接到MainWindow中的一个方法
        if self.game and hasattr(self.game, 'gui') and self.game.gui:
            return self.game.gui.ask_yes_no_question(f"轮到【{self.name}】", f"是否发动技能【{skill_name}】？")
        # Fallback for non-GUI mode
        answer = input(f"【{self.name}】, 是否发动技能【{skill_name}】？ (y/n): ")
        return answer.lower() == 'y'

    def choose_blue_card_to_play_for_lord(self) -> UnoCard:
        """
        为护驾技能选择要打出的蓝色牌。
        这应该触发GUI中的一个对话框。
        """
        blue_cards = [card for card in self.uno_list if card.color == 'blue']
        if not blue_cards:
            return None

        if self.game and hasattr(self.game, 'gui') and self.game.gui:
            # GUI会返回选中的卡牌对象或None
            return self.game.gui.ask_for_card_choice(f"【{self.name}】的响应", "请为【护驾】选择一张蓝色牌打出，或取消。", blue_cards)
        
        # Fallback for non-GUI mode
        print(f"【{self.name}】, 请为【护驾】选择一张蓝色牌打出:")
        for i, card in enumerate(blue_cards):
            print(f"  {i}: {card.content}")
        print("  输入 'c' 取消.")
        choice = input("你的选择: ")
        if choice.isdigit() and 0 <= int(choice) < len(blue_cards):
            return blue_cards[int(choice)]
        return None

    #拿num张牌,先用print来做游戏提示了 无return
    def get_card(self,num:int):
        for _ in range(num):
            if self.game.unocard_pack:
                self.uno_list.append(self.game.unocard_pack.pop())
            else:
                print("uno牌已被拿完")
                break
    #检查出牌是否合规 return T/F  最好检查一下有没有逻辑错误)
    def check_card(self, card: UnoCard) -> bool:
        """检查出牌是否合规，已整合+2/+4叠加规则"""
        # 规则：如果当前有加牌惩罚(draw_n > 0)，则必须出+2或+4来续上
        if self.game.draw_n > 0:
            last_card = self.game.playedcards.get_one()
            # 规则：+2上可叠+2或+4
            if last_card.type == 'draw2' and card.type in ['draw2', 'wild_draw4']:
                return True
            # 规则：+4上只能叠+4
            if last_card.type == 'wild_draw4' and card.type == 'wild_draw4':
                return True
            # 其他任何牌在加牌链中都是不合规的
            return False

        # 正常出牌规则 (draw_n == 0)
        # 首轮弃牌堆为空
        if not self.game.playedcards.d:
            return card.type in ['wild', 'wild_draw4'] or card.color == self.game.cur_color

        last_card = self.game.playedcards.get_one()
        
        # 万能牌总是可以出
        if card.type in ['wild', 'wild_draw4']:
            return True

        # 颜色或数字/类型匹配
        if card.color == self.game.cur_color or (card.type == last_card.type and card.type != 'number') or (card.value == last_card.value and card.type == 'number'):
             # 如果弃牌堆顶是万能牌，则只匹配cur_color
            if last_card.type in ['wild', 'wild_draw4']:
                return card.color == self.game.cur_color
            return True
            
        return False  

    #出牌 无return 如果出牌合规则回合结束 否则无视发生 这里单指正常出一张   需要一个flag来说明回合结束? 
    def play_a_hand(self,location:int, color_choice=None):
        card = self.uno_list.pop(location)
        # 关羽技能：红色牌可当红+2
        if self.mr_card and any(skill.__class__.__name__ == 'WuSheng' for skill in self.mr_card.skills):
            if card.color == 'red' and card.type == 'number':
                from card import UnoCard
                card = UnoCard('draw2', 'red', 0)
        if self.check_card(card):
            # 设定颜色
            if card.type == 'wild' or card.type == 'wild_draw4':
                if color_choice:
                    self.game.cur_color = color_choice
                else:
                    self.game.cur_color = card.color if card.color != 'wild' and card.color != 'wild_draw4' else self.game.cur_color
            else:
                self.game.cur_color = card.color
            self.game.playedcards.add_card(card)
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
    #依次执行判定
    def judging(self):
        for f in self.judging_list:
            if f.need_judging:
                f(self,self.game.unocard_pack.pop())