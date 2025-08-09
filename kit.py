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
            player.draw_cards(1)

class BingLiangCunDuan(Judge):#兵粮的need_judging可能为false
    def __init__(self):
        super().__init__()
    def __call__(self, player:Player, card:UnoCard, draw_n:int=0):
        """
        兵粮寸断判定：目标玩家被加牌前进行判定，若结果非蓝色，则该玩家摸牌数-2。
        若 draw_n=0，表示本轮未被加牌，直接返回0。
        判定后若目标玩家被加牌则兵粮寸断效果解除（need_judging=False）。
        :param player: 目标玩家
        :param card: 判定牌（通常为牌堆顶）
        :param draw_n: 本应摸牌数（可能为0）
        :return: 实际摸牌数
        """
        if draw_n <= 0:
            return 0
        if card.color != 'blue':
            actual_draw = max(draw_n - 2, 0)
        else:
            actual_draw = draw_n
        # 判定后兵粮寸断效果解除
        self.need_judging = False
        return actual_draw

class Lightening(Judge):
    def __init__(self):
        super().__init__()
    def __call__(self, player:Player, card:UnoCard):
        if card.color=='wild' or card.color=='wild_draw4':
            player.draw_cards(10)
        else:
            self.transfer=True

class Duel:
    def __init__(self, color, player1, player2):
        self.color = color  # 决斗颜色（非黑色）
        self.player1 = player1
        self.player2 = player2
        self.duel_cards = []  # 记录双方打出的牌

    def __call__(self):
        """
        决斗流程：双方交替打出指定颜色牌，不能出牌者摸等量牌（至少3张），期间可发动技能。
        返回：输家对象和应摸牌数
        """
        cur = self.player1
        other = self.player2
        duel_count = 0
        while True:
            idx = self._find_color_card(cur)
            if idx is not None:
                # 可发动技能（此处留接口，实际技能判定需在主流程实现）
                card = cur.uno_list[idx]
                self.duel_cards.append(card)
                cur.play_a_hand(idx)
                duel_count += 1
                # 交换出牌权
                cur, other = other, cur
            else:
                # 当前玩家不能再出牌，判定输家
                lose_player = cur
                break
        # 输家摸牌数=双方打出牌总数，若小于3则摸3张
        draw_num = max(duel_count, 3)
        lose_player.draw_cards(draw_num)
        return lose_player, draw_num

    def _find_color_card(self, player):
        """查找玩家手牌中可出的决斗颜色牌，返回索引或None"""
        for i, card in enumerate(player.uno_list):
            if card.color == self.color and card.type == 'number':
                return i
        return None

class NanManRuQin:
    def __call__(self, caller:Player, game:Game):
        """
        南蛮入侵效果：所有其他玩家需弃置1张[+2]/[+4]，否则摸4张牌。
        """
        for player in game.player_list:
            if player == caller:
                continue
            # 查找手牌中是否有[+2]或[+4]
            idx = self._find_attack_card(player)
            if idx is not None:
                # 弃置该牌（不加入弃牌堆）
                player.fold_card([idx])
            else:
                player.draw_cards(4)

    def _find_attack_card(self, player):
        """查找玩家手牌中[+2]或[+4]牌，返回索引或None"""
        for i, card in enumerate(player.uno_list):
            if card.type in ['draw2', 'wild_draw4']:
                return i
        return None