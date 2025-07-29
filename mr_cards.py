from card import MRCard
from skill import WuSheng, JianXiong, HuJia, QiXi # 导入需要的技能

# 武将卡牌定义
all_heroes = {
    '关羽': MRCard(
        name='关羽',
        gender='male',
        skills=[WuSheng()]
    ),
    '曹操': MRCard(
        name='曹操',
        gender='male',
        skills=[JianXiong(), HuJia()]
    ),
    '甘宁': MRCard(
        name='甘宁',
        gender='male',
        skills=[QiXi()]
    ),
    # 在这里添加更多武将...
    # '甄姬': MRCard(name='甄姬', gender='female', skills=[QingGuo()]),
}
