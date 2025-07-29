from card import MRCard
from skill import WuSheng, JianXiong, HuJia, QiXi # 导入需要的技能

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
    # 在这里添加更多武将...
    # '甄姬': MRCard(name='甄姬', gender='female', skills=[QingGuo()], image_path='zhenji.jpg'),
}
