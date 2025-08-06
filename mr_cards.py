from card import MRCard
from skill import WuSheng, JianXiong, HuJia, QiXi, ZiShou, ZongShi, FanJian, JiZhi, DiMeng, XuanFeng, SanYao, ShiCai # 导入需要的技能

# 武将卡牌定义
all_heroes = {
    '关羽': MRCard(
        name='关羽',
        gender='male',
        team='shu',
        skills=[WuSheng()],
        image_path='关羽.jpg',
        skill_description='【武圣】：你的[红色]可以当作[红+2]打出。',
        tags='进攻、应变',
        difficulty=1
    ),
    '曹操': MRCard(
        name='曹操',
        gender='male',
        team='wei',
        skills=[JianXiong(), HuJia()],
        image_path='曹操.jpg',
        skill_description='【奸雄】：若场上打出的[+2]/[+4]牌对你生效且不由你打出，你可选择获得之。\n【护驾】：（主公技）当你需要打出[蓝色]时，你可以请求其他【魏】势力角色打出[蓝色]响应。',
        tags='反击',
        difficulty=2
    ),
    '甘宁': MRCard(
        name='甘宁',
        gender='male',
        team='wu',
        skills=[QiXi()],
        image_path='甘宁.jpg',
        skill_description='【奇袭】：当你打出[绿色]时，你可以指定一名玩家摸1张牌。',
        tags='进攻',
        difficulty=2
    ),
    '刘表': MRCard(
        name='刘表',
        gender='male',
        team='qun',
        skills=[ZiShou(), ZongShi()],
        image_path='刘表.jpg', # 假设图片名为liubiao.jpg
        skill_description='【自守】（锁定技）你的手牌数上限调整为8。\n【宗室】（主公技）其他【群】势力玩家被加牌时，其可以令你弃置1张牌。',
        tags='防御',
        difficulty=0
    ),
    '周瑜': MRCard(
        name='周瑜',
        gender='male',
        team='wu',
        skills=[FanJian()],
        image_path='周瑜.jpg',
        skill_description='【反间】：出牌阶段，你可以摸一张牌，然后将一张手牌（非黑色）交给一名其他角色，该角色需弃置所有与此牌相同颜色的手牌。如果弃掉的手牌数量>2，周瑜额外摸一张牌。',
        tags='辅助、博弈',
        difficulty=6
    ),
    '黄月英': MRCard(
        name='黄月英',
        gender='female',
        team='shu',
        skills=[JiZhi()],
        image_path='黄月英.jpg',
        skill_description='【集智】：当你打出[+2]/[+4]/[换色]时，你可以弃置2张牌。',
        tags='爆发',
        difficulty=4
    ),
    '鲁肃': MRCard(
        name='鲁肃',
        gender='male',
        team='wu',
        skills=[DiMeng()],
        image_path='鲁肃.jpg',
        skill_description='【缔盟】：你摸x张牌并指定两名其他玩家交换手牌，x为两人手牌数目之差。手牌数大于6时此技能失效。',
        tags='干扰、辅助',
        difficulty=8
    ),
    '凌统': MRCard(
        name='凌统',
        gender='male',
        team='wu',
        skills=[XuanFeng()],
        image_path='凌统.jpg',
        skill_description='【旋风】：当你跳牌时，可以弃置所有与该牌点数相同的牌。',
        tags='爆发',
        difficulty=1
    ),
    '马谡': MRCard(
        name='马谡',
        gender='male',
        team='shu',
        skills=[SanYao(), ShiCai()],
        image_path='马谡.jpg',
        skill_description='【散谣】：当你跳牌时，你可以指定一名玩家摸2张牌。\n【恃才】：（锁定技）你剩余2张牌时，须喊"UNO"。',
        tags='进攻',
        difficulty=2
    ),

    # 在这里添加更多武将...
    # '甄姬': MRCard(name='甄姬', gender='female', skills=[QingGuo()], image_path='zhenji.jpg'),
}
