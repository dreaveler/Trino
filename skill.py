from card import UnoCard
from player import Player

class Skill:
    def __init__(self, name, description:str, type:str, is_active_in_turn: bool = False):
        self.name = name
        self.description = description
        self.type = type # 'active' or 'passive'
        self.is_active_in_turn = is_active_in_turn # Can be triggered by a button in player's turn

class WuSheng(Skill):
    def __init__(self):
        super().__init__('武圣', '你的[红色]可以当作[红+2]打出。', 'active', is_active_in_turn=True)
    def use(self, original_card:UnoCard):
        # original_card是被当作+2打出的红色牌
        return f"{self.name} 发动[武圣]，将 [{original_card}] 当作 [红+2] 打出"

class JianXiong(Skill):
    def __init__(self):
        super().__init__('奸雄', '【奸雄】若场上打出的[+2]/[+4]牌对你生效且不由你打出，你可以获得之。', 'passive')
    def on_effect(self, card:UnoCard, from_player:Player, to_player:Player):
        """
        返回详细历史文本
        """
        if (card.type == 'draw2' or card.type == 'wild_draw4') and from_player != to_player:
            if to_player.choose_to_use_skill(self.name):
                # 实际获得牌逻辑在game.py
                return f"{to_player.mr_card.name} 发动[奸雄]，获得了 {from_player.mr_card.name} 打出的 [{card}]"
        return None

class HuJia(Skill):
    def __init__(self):
        super().__init__('护驾', '（主公技）当你需要打出[蓝色]时，可以令其他【魏】势力玩家替你打出，然后其摸1张牌', 'active')
    def on_need_blue(self, lord:Player, weiguo_players:list):
        """
        当主公需要出蓝色牌时触发。
        返回打出的牌对象表示成功，返回None表示无人响应。
        """
        # 过滤掉主公自己
        helpers = [p for p in weiguo_players if p.team == 'wei' and p != lord]
        if not helpers:
            return None

        # 游戏引擎应调用主公的UI方法来选择是否发动技能
        if lord.choose_to_use_skill(self.name):
            # 游戏引擎应依次询问魏势力玩家是否愿意打出蓝色牌
            for helper in helpers:
                # 游戏引擎调用helper的UI，让其选择要打的蓝色牌
                card_to_play = helper.choose_blue_card_to_play_for_lord()
                if card_to_play:
                    # 该玩家打出此牌，并从手牌中移除
                    helper.play_card_object(card_to_play)
                    # 然后摸一张牌
                    helper.get_card(1)
                    print(f"【{lord.name}】发动【护驾】，【{helper.name}】替其打出【{card_to_play.content}】并摸一张牌")
                    return card_to_play
        return None

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
        super().__init__('奇袭','当你打出[绿色]时，你可以指定一名玩家摸1张牌','active', is_active_in_turn=False)
    def __call__(self, card:UnoCard, player:Player, other_player:Player):
        if card.color=='green':
            # 使用is_skill_draw=True来避免重复的历史记录
            other_player.draw_cards(1, is_skill_draw=True)
            return f"{player.mr_card.name} 发动[奇袭]，令 {other_player.mr_card.name} 摸了一张牌"
        return None

class FanJian(Skill):
    def __init__(self):
        super().__init__('反间','反间：出牌阶段，你可以摸一张牌，然后将一张手牌（非黑色）交给一名其他角色，该角色需弃置所有与此牌颜色相同的手牌。','active', is_active_in_turn=True)
    def record_history(self, player, target, card_given, cards_discarded):
        discard_str = '、'.join(str(c) for c in cards_discarded) if cards_discarded else '无'
        return f"{player.mr_card.name} 发动[反间]，{target.mr_card.name} 弃掉了 [{discard_str}]"

class ZiShou(Skill):
    def __init__(self):
        super().__init__('自守', '（锁定技）你的手牌数上限调整为8。', 'passive')

class ZongShi(Skill):
    def __init__(self):
        super().__init__('宗室', '（主公技）其他【群】势力玩家被加牌时，其可以令你弃置1张牌。', 'passive')