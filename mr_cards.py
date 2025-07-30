from card import MRCard
from skill import WuSheng, JianXiong, HuJia, QiXi, ZiShou, ZongShi, FanJian # 导入需要的技能

# 武将卡牌定义
all_heroes = {
    '关羽': MRCard(
        name='关羽',
        gender='male',
        team='shu',
        skills=[WuSheng()],
        image_path='guanyu.jpg',
        skill_description='你的[红色]可以当作[红+2]打出。'
    ),
    '曹操': MRCard(
        name='曹操',
        gender='male',
        team='wei',
        skills=[JianXiong(), HuJia()],
        image_path='caocao.jpg',
        skill_description='奸雄 若场上打出的[+2]/[+4]牌对你生效且不由你打出，你可选择获得之。护驾：主公技，当你需要打出[蓝色]时，你可以请求其他蜀势力角色打出[蓝色]响应。'
    ),
    '甘宁': MRCard(
        name='甘宁',
        gender='male',
        team='wu',
        skills=[QiXi()],
        image_path='ganning.jpg',
        skill_description='当你打出[绿色]时，你可以指定一名玩家摸1张牌。'
    ),
    '刘表': MRCard(
        name='刘表',
        gender='male',
        team='qun',
        skills=[ZiShou(), ZongShi()],
        image_path='liubiao.jpg', # 假设图片名为liubiao.jpg
        skill_description='自守（锁定技）你的手牌数上限调整为8。宗室（主公技）其他【群】势力玩家被加牌时，其可以令你弃置1张牌。'
    ),
    '周瑜': MRCard(
        name='周瑜',
        gender='male',
        team='wu',
        skills=[FanJian()],
        image_path='zhouyu.jpg',
        skill_description='反间：出牌阶段，你可以摸一张牌，然后将一张手牌（非黑色）交给一名其他角色，该角色需弃置所有与此牌颜色相同的手牌。'
    ),
    # 在这里添加更多武将...
    # '甄姬': MRCard(name='甄姬', gender='female', skills=[QingGuo()], image_path='zhenji.jpg'),
}
