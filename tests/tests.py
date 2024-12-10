from src.bot.twitch_bot import PickBot


def manual_test():
    bot = PickBot()
    # Simulate some queue states
    bot.queue.tank = {"player1", "player2", "player3", "player4", "player5", "player6", "player7", "player8", "player9", "player10"}
    bot.queue.dps = {"player1", "player2", "player3", "player4", "player5", "player6", "player7", "player8", "player9", "player10"}
    bot.queue.support = {"player1", "player2", "player3", "player4", "player5", "player6", "player7", "player8", "player9", "player10"}

    # Test the pick command
    team1, team2, captain1, captain2 = bot._select_teams()

    print("Results:")
    print(f"Team 1: {team1}")
    print(f"Team 2: {team2}")
    print(f"Captains: {captain1}, {captain2}")


set1 = {"player1", "player2", "player3", "player4", "player5", "player6"}
set1.update(('tim','tom'))
print(set1)