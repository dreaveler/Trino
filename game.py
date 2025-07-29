from player import Player
from typing import List, Callable
from card import UnoCard
from util import PlayedCards
import random
from ai import AI
from PyQt5.QtWidgets import QMessageBox

#胜利条件
class Game:
    def check_jump(self):
        # 跳牌逻辑：遍历所有玩家，查找能跳牌的玩家（除当前玩家）
        last_card = self.playedcards.get_one()
        for idx, player in enumerate(self.player_list):
            if idx == self.cur_location:
                continue
            for i, card in enumerate(player.uno_list):
                # 普通跳牌
                if card.color == last_card.color and card.type == last_card.type and card.value == last_card.value:
                    print(f"玩家{idx+1}可以跳牌！手牌序号：{i}，牌：{card}")
                    choice = input(f"玩家{idx+1}是否跳牌？(y/n): ")
                    if choice.lower() == 'y':
                        player.play_a_hand(i)
                        print(f"玩家{idx+1}跳牌打出：{card}")
                        self.cur_location = idx
                        self.change_flag()
                        return True
                # 关羽武圣跳红+2
                if player.mr_card and any(skill.__class__.__name__ == 'WuSheng' for skill in player.mr_card.skills):
                    if card.color == 'red' and card.type == 'number' and last_card.type == 'draw2':
                        print(f"玩家{idx+1}可以用武圣跳牌！手牌序号：{i}，牌：{card}")
                        choice = input(f"玩家{idx+1}是否用武圣跳红+2？(y/n): ")
                        if choice.lower() == 'y':
                            from card import UnoCard
                            player.uno_list.pop(i)
                            new_card = UnoCard('draw2', 'red', 0)
                            self.playedcards.add_card(new_card)
                            print(f"玩家{idx+1}武圣跳牌打出：{new_card}")
                            self.cur_location = idx
                            self.change_flag()
                            return True
        return False
    def __init__(self,player_num:int,mode:str):
        self.player_num = player_num
        self.playedcards = PlayedCards()
        self.mode = mode

        self.player_list: List[Player] = []
        self.unocard_pack:List[UnoCard] = []

        self.cur_location:int = None
        self.dir: int = 1  #每次加一个dir  1/-1  默认为++
        self.cur_color:str = None
        #flag
        self.draw_n:int = 0
        self.skip:bool = False
        self.gui = None # 添加GUI引用
        self.ai_handler = AI()

    #创造牌组
    def create_unocard_pack(self):
        colors = ['red','blue','yellow','green']
        type = ['reverse','skip','draw2']*2
        numbers = [0] + 2*[i for i in range(1,10)]
        for color in colors:
            for number in numbers:
                self.unocard_pack.append(UnoCard("number",color,number))
            for action in type:
                self.unocard_pack.append(UnoCard(action,color,0))
        for _ in range(4):
            self.unocard_pack.append(UnoCard('wild','wild',10))
            self.unocard_pack.append(UnoCard('wild_draw4','wild_draw4',10))
        random.shuffle(self.unocard_pack)
        
    #将玩家加对对局中同时将game赋給玩家
    def add_player(self,player:Player):
        self.player_list.append(player)
        player.game = self

    def set_gui(self, gui):
        """设置GUI的引用"""
        self.gui = gui
        for player in self.player_list:
            player.game = self # 确保所有player的game实例都更新

    #发牌！ 每人8张 第一个出牌/主公9张(需要设定模式)
    def deal_cards(self):
        for i, player in enumerate(self.player_list):
            if i == self.cur_location:
                player.get_card(9)
            else:
                player.get_card(8)
    #开始游戏
    def game_start(self):
        self.create_unocard_pack()
        self.cur_location = random.randint(0, self.player_num - 1)
        self.deal_cards()
        card = self.unocard_pack.pop()
        print(f"游戏开始，揭示的第一张牌为：{card}")
        self.playedcards.add_card(card)
        # 只用于设定颜色，不加入弃牌堆和玩家手牌
        if card.type in ['wild', 'wild_draw4']:
            if self.gui:
                color = self.gui.choose_color_dialog()
                self.cur_color = color
            else:
                color = input("揭示的是黑色牌，请选择一个颜色（red/blue/yellow/green）：")
                self.cur_color = color
        else:
            self.cur_color = card.color
    
    def execute_skill_jianxiong(self, player):
        """处理奸雄技能"""
        card_to_gain = self.playedcards.d.pop() # 从弃牌堆顶拿走牌
        player.get_card_object(card_to_gain)
        self.draw_n = 0 # 罚牌数清零
        print(f"玩家 {player.position+1} 发动【奸雄】，获得了 {card_to_gain}")
        # 奸雄后是自己的回合，所以不需要next_player，只需要刷新UI
        if self.gui:
            self.gui.show_game_round()

    def execute_skill_wusheng(self, player, card_idx):
        """处理武圣技能"""
        original_card = player.uno_list.pop(card_idx)
        wusheng_card = UnoCard('draw2', 'red', 0)
        self.playedcards.add_card(wusheng_card)
        self.cur_color = 'red'
        self.change_flag() # 触发+2效果
        print(f"玩家 {player.position+1} 发动【武圣】，将 {original_card} 当作 {wusheng_card} 打出")

    def execute_skill(self, skill, player, *args):
        """统一的技能执行入口"""
        print(f"玩家 {player.position+1} 尝试发动技能 {skill.name}")
        # 这里可以根据技能名称调用不同的处理函数
        if skill.name == '反间':
            target, card_to_give = args
            # 1. 玩家摸一张牌
            player.get_card(1)
            # 2. 将牌从玩家手牌给目标
            player.play_card_object(card_to_give) # 从手牌移除
            # 3. 目标弃掉所有同色牌
            color_to_discard = card_to_give.color
            cards_to_discard = [c for c in target.uno_list if c.color == color_to_discard]
            cards_to_discard.append(card_to_give) # 把给的牌也算上
            
            fold_indices = [i for i, c in enumerate(target.uno_list) if c.color == color_to_discard]
            target.fold_card(fold_indices)

            QMessageBox.information(self.gui, "反间成功", f"玩家 {target.position+1} 弃掉了所有 {color_to_discard} 牌。")

        # 在这里添加其他技能的逻辑...

        # 检查胜利条件
        if len(player.uno_list) == 0:
            self.gui.show_winner_and_exit(player)
            return
        if len(target.uno_list) == 0:
            self.gui.show_winner_and_exit(target)
            return

    def execute_ai_turn(self):
        """执行AI玩家的回合"""
        player = self.player_list[self.cur_location]
        
        # 检查是否必须响应加牌
        if self.draw_n > 0 and not self.can_continue_draw_chain(player):
            print(f"AI 玩家 {player.position+1} 无法续上加牌链，摸 {self.draw_n} 张牌")
            player.get_card(self.draw_n)
            self.draw_n = 0
            self.next_player()
            if self.gui:
                self.gui.show_game_round()
            return

        # 构造游戏状态
        game_state = {
            'players': self.player_list,
            'last_card': self.playedcards.get_one(),
            'current_color': self.cur_color,
            'draw_n': self.draw_n,
            'game_direction': self.dir,
        }

        # AI决策
        action_type, action_value = self.ai_handler.choose_action(player, game_state)
        
        print(f"AI ({player.mr_card.name}) 决定: {action_type} {action_value if action_value is not None else ''}")

        try:
            if action_type == 'draw':
                player.get_card(1)
            elif action_type == 'play':
                card_to_play = player.uno_list[action_value]
                
                if player.check_card(card_to_play):
                    if card_to_play.type in ['wild', 'wild_draw4']:
                        # AI为万能牌选择颜色
                        self.cur_color = self.ai_handler.choose_wild_color(player)
                        print(f"AI 将颜色变为 {self.cur_color}")

                    player.play_a_hand(action_value)
                    self.change_flag()

                    if len(player.uno_list) == 0:
                        if self.gui:
                            self.gui.show_winner_and_exit(player)
                        return
                else:
                    # AI决策无效，则摸牌
                    print(f"AI 决策无效，改为摸牌。")
                    player.get_card(1)
            # TODO: handle 'use_skill'
        except Exception as e:
            print(f"AI 执行出错: {e}，改为摸牌。")
            player.get_card(1)

        self.next_player()
        if self.gui:
            self.gui.show_game_round()

    #结算skip
    def skip_player(self):
        if self.skip:
            self.skip = False
    #结算所有状态（处理skip和draw2/draw4的移除）
    def clear_state(self):
        self.skip_player()
        # 结算加牌后只清理skip，不清理draw_n
        # draw_n只在玩家实际摸牌后清零
    def can_continue_draw_chain(self, player: Player) -> bool:
        """检查玩家是否可以续上+2/+4的链条"""
        if self.draw_n == 0:
            return False
        
        last_card = self.playedcards.get_one()
        if not last_card:
            return False

        last_type = last_card.type
        for card in player.uno_list:
            # 规则：+2上可叠+2或+4，+4上只能叠+4
            if last_type == 'draw2' and card.type in ['draw2', 'wild_draw4']:
                return True
            if last_type == 'wild_draw4' and card.type == 'wild_draw4':
                return True
        return False

    #单个玩家回合
    def player_turn(self):
        player = self.player_list[self.cur_location]

        # 回合开始时，检查是否有对该玩家生效的延时锦囊（如乐不思蜀）
        # ... 延时锦囊判定逻辑 ...

        # 检查是否需要响应打出的牌（如+2/+4）
        if self.draw_n > 0:
            # 首先检查玩家是否能续上，如果不能，则必须摸牌
            if not self.can_continue_draw_chain(player):
                # 检查是否有【奸雄】技能
                if player.mr_card and any(skill.__class__.__name__ == 'JianXiong' for skill in player.mr_card.skills):
                    if self.gui.ask_yes_no_question("发动技能", "是否发动【奸雄】获得这张牌？"):
                        self.execute_skill_jianxiong(player)
                        # 奸雄后，轮到自己出牌，继续执行回合
                        # UI should be refreshed inside execute_skill_jianxiong or after it
                        self.gui.show_game_round()
                        return # Stop current turn logic, as a new one will start
                    else:
                        # 玩家选择不发动奸雄，正常摸牌
                        print(f"玩家 {player.position+1} 选择不发动【奸雄】，摸 {self.draw_n} 张牌")
                        player.get_card(self.draw_n)
                        self.draw_n = 0
                        self.next_player()
                        self.gui.show_game_round()
                        return # 回合结束
                else:
                    # 没有奸雄，正常摸牌
                    print(f"玩家 {player.position+1} 不能续上加牌链，摸 {self.draw_n} 张牌")
                    player.get_card(self.draw_n)
                    self.draw_n = 0
                    self.next_player()
                    self.gui.show_game_round()
                    return # 回合结束
            # 如果能续上，则正常进入他的回合，让他选择出牌

        # 跳牌逻辑，优先处理
        if self.check_jump():
            # 跳牌后直接进入下一个回合
            return False
        
        # 检查胜利条件
        if len(player.uno_list) == 0:
            print(f"玩家{self.cur_location+1}获胜！")
            return True
        # 检查无法出牌
        if player.check_cannot_play_card():
            player.get_card(1)
            print(f"玩家{self.cur_location+1}无法出牌，摸1张")
            self.next_player()
            return False
        
        # GUI/手动出牌逻辑
        # 在GUI模式下，这里会等待GUI的信号，而不是阻塞输入
        # 在命令行模式下，执行以下逻辑
        if not self.gui:
            # 展示手牌
            cards = player.uno_list
            for i, card in enumerate(cards):
                print(f"card{i}: {card}")
            # 输入合法性校验和出牌合法性
            while True:
                try:
                    index = int(input("请选择你出牌的序号: "))
                    if 0 <= index < len(cards):
                        if player.check_card(cards[index]):
                            break
                        else:
                            print("出牌不符合规范，请重新选择。")
                    else:
                        print("输入序号不合法，请重新输入。")
                except Exception:
                    print("输入错误，请输入数字。")
            
            # UNO 叫牌逻辑
            if len(cards) == 2:
                uno_call = input("你只剩1张牌，是否喊UNO？(y/n): ")
                if uno_call.lower() != 'y':
                    print("未喊UNO，罚摸1张牌")
                    player.get_card(1)
            
            # 黑色牌不能作为最后一张牌
            if len(cards) == 1 and (cards[index].type == 'wild' or cards[index].type == 'wild_draw4'):
                print("最后一张不能为黑色牌，罚摸1张牌")
                player.get_card(1)
                self.next_player()
                return False
            
            player.play_a_hand(index)
            print(f"玩家{self.cur_location+1}打出：{cards[index]}")
            self.change_flag()
            # 检查胜利
            if len(player.uno_list) == 0:
                print(f"玩家{self.cur_location+1}获胜！")
                return True
            self.next_player()
        
        return False
    #+2/+4/skip
    def change_flag(self):
        card = self.playedcards.get_one()
        cardtype = card.type
        # 武圣红+2也计入加牌串
        if cardtype == "draw2":
            self.draw_n += 2
        elif cardtype == "wild_draw4":
            self.draw_n += 4
        elif cardtype == "skip":
            self.skip = True
        elif cardtype == "reverse":
            self.dir *= -1
    def next_player(self):
        # 跳过玩家
        if self.skip:
            self.cur_location = (self.cur_location + self.dir * 2) % self.player_num
            self.skip = False
        else:
            self.cur_location = (self.cur_location + self.dir) % self.player_num
