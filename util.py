from __future__ import annotations
from card import UnoCard
from collections import deque
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from player import Player

#本文件将编写一些可能用到的数据结构

class PlayedCards:
    def __init__(self):
        # d: list of tuples (effective_card, original_card, source_player)
        self.d: list[tuple[UnoCard, UnoCard, 'Player']] = []

    def add_card(self, effective_card: UnoCard, source_player: 'Player', original_card: UnoCard = None):
        """
        向弃牌堆添加一张牌。
        :param effective_card: 生效的牌（可能是虚拟的，如武圣牌）
        :param source_player: 出牌的玩家
        :param original_card: 实际打出的原始牌，如果与生效牌不同
        """
        if original_card is None:
            original_card = effective_card
        self.d.append((effective_card, original_card, source_player))

    def get_one(self) -> Optional[UnoCard]:
        """获取最上面一张生效的牌"""
        return self.d[-1][0] if self.d else None

    def get_last_cards(self, n: int) -> list[UnoCard]:
        """获取最上面n张生效的牌，用于显示"""
        return [item[0] for item in self.d[-n:]]

    def get_card_source(self, card: UnoCard) -> Optional['Player']:
        """查找特定生效牌的来源玩家"""
        for eff_card, _, source in reversed(self.d):
            if eff_card is card:
                return source
        return None
    
    def get_last_play_info(self) -> Optional[tuple[UnoCard, UnoCard, 'Player']]:
        """获取最后一次出牌的完整信息（生效牌，原始牌，来源）"""
        return self.d[-1] if self.d else None

    def get_two(self):
        #二张专属，返回最近两个card，type=tuple
        if len(self.d) >= 2:
            return (self.d[-2][0], self.d[-1][0]) # 返回生效的牌
        elif len(self.d) == 1:
            return (self.d[-1][0], self.d[-1][0])
        return None

@dataclass
class PlayAction:
    """记录一次出牌行动的数据结构"""
    card: UnoCard # 玩家实际打出的原始卡牌
    source: Player
    target: Optional[Player] = None
    color_choice: Optional[str] = None
    virtual_card: Optional[UnoCard] = None # 如果技能改变了牌的效果，这里存储其虚拟效果

    def __repr__(self):
        source_info = f"Player {self.source.position}"
        target_info = f"Player {self.target.position}" if self.target else "None"
        color_info = f", color_choice='{self.color_choice}'" if self.color_choice else ""
        return f"PlayAction(card={self.card}, source={source_info}, target={target_info}{color_info})"