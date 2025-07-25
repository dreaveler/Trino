from game import Game
from player import Player
from ai import DeepSeekAI

if __name__ == "__main__":
    print("UNO 游戏开始！")
    num_players = 4
    ai_player_idx = [2, 3, 4]  # 2号和3号为AI玩家（可自定义）
    ai = DeepSeekAI(api_key="sk-d072d2e34a2b42e5ba3ab148b098ca5a")
    game = Game(player_num=num_players, mode="4人混战")
    for i in range(num_players):
        if i in ai_player_idx:
            # 创建AI玩家，继承Player并重写出牌逻辑
            class AIPlayer(Player):
                def play_turn(self):
                    uno_list = [str(card) for card in self.uno_list]
                    last_card = str(self.game.playedcards.get_one())
                    idx = ai.choose_card(uno_list, last_card, self.game.cur_color)
                    if idx == -1:
                        print(f"AI玩家{i+1}无法出牌，摸1张牌")
                        self.get_card(1)
                        return None
                    print(f"AI玩家{i+1}选择出牌序号：{idx}，牌：{self.uno_list[idx]}")
                    return idx
            game.add_player(AIPlayer(position=i, team=str(i+1)))
        else:
            game.add_player(Player(position=i, team=str(i+1)))
    game.game_start()
    round_count = 1
    while True:
        print(f"\n--- 第{round_count}回合，当前玩家：{game.cur_location+1} ---")
        player = game.player_list[game.cur_location]
        if isinstance(player, Player) and hasattr(player, 'play_turn'):
            idx = player.play_turn()
            if idx is not None:
                # 兼容AI玩家直接出牌
                if player.check_card(player.uno_list[idx]):
                    player.play_a_hand(idx)
                    print(f"AI玩家{game.cur_location+1}打出：{player.uno_list[idx]}")
                    game.change_flag()
                    if len(player.uno_list) == 0:
                        print(f"玩家{game.cur_location+1}获胜！")
                        break
                    game.next_player()
                    round_count += 1
                    continue
        result = game.player_turn()
        if result:
            print("游戏结束！")
            break
        round_count += 1