import websockets
import asyncio
import random
import re
import pandas as pd
from src.config.settings import *
from src.bot.queue import Queue
from src.bot.game_log import *

class PickBot:
    def __init__(self):
        self.channel_name = TWITCH_CHANNEL
        self.starter_names = BOT_ADMINS
        self.uri = TWITCH_WEBSOCKET_URI
        self.queue = Queue()
        self._already_played = set()
        self.account_name = TWITCH_BOT_USERNAME
        self.token = TWITCH_OAUTH_TOKEN
        self._repeats_okay = False
        self.chat_message_pattern = re.compile(r'^:(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.*)$')
        self.websocket = None
        self.reconnect_delay = 5  # Start with 5 seconds delay between reconnection attempts
        self.current_game = None

    async def connect_and_run(self):
        while True:  # Main reconnection loop
            try:
                await self.connect()
            except Exception as e:
                print(f"\nConnection lost: {str(e)}")
                print(f"Attempting to reconnect in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
                print("Reconnecting...")

    async def connect(self):
        print("Connecting to " + self.channel_name)
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket

                print("Connected to " + self.channel_name)

                await websocket.send(f"PASS {self.token}\r\n")
                await websocket.send(f"NICK commanderx\r\n")
                await websocket.send(f"JOIN #{self.channel_name}\r\n")

                print(f"{self.account_name} connected to {self.channel_name}. Awaiting commands from {self.starter_names}")

                while True:
                    message = await websocket.recv()
                    await self._evaluate_message(message)

        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: code = {e.code}, reason = {e.reason}")
            raise
        except Exception as e:
            print(f"Connection error: {str(e)}")
            raise


    def _select_teams(self):
        queued_tanks = set(self.queue.tank)
        queued_dps = set(self.queue.dps)
        queued_support = set(self.queue.support)
        if not self._repeats_okay:
            valid_tanks = queued_tanks - self._already_played
            valid_dps = queued_dps - self._already_played
            valid_supports = queued_support - self._already_played
        else:
            valid_tanks = queued_tanks
            valid_dps = queued_dps
            valid_supports = queued_support

        if len(valid_tanks) < 2 or len(valid_dps) < 4 or len(valid_supports) < 4:
            return None, None, None, None

        selected_tanks = random.sample(list(valid_tanks), 2)

        valid_dps -= set(selected_tanks)
        valid_supports -= set(selected_tanks)

        if len(valid_dps) < 4 or len(valid_supports) < 4:
            return None, None, None, None

        selected_dps = random.sample(list(valid_dps), 4)

        valid_supports -= set(selected_dps)

        if len(valid_supports) < 4:
            return None, None, None, None

        selected_supports = random.sample(list(valid_supports), 4)

        self._already_played.update(set(selected_tanks), set(selected_dps), set(selected_supports))

        team_1 = {'tank': selected_tanks[0], 'dps': selected_dps[0:2], 'support': selected_supports[0:2]}
        team_2 = {'tank': selected_tanks[1], 'dps': selected_dps[2:4], 'support': selected_supports[2:4]}

        team_1_set = {team_1['tank']} | set(team_1['dps']) | set(team_1['support'])
        team_2_set = {team_2['tank']} | set(team_2['dps']) | set(team_2['support'])

        captain1 = random.choice(list(team_1_set))
        captain2 = random.choice(list(team_2_set))

        return team_1, team_2, captain1, captain2

    async def _evaluate_message(self, message):
        match = self.chat_message_pattern.match(message)

        if not match:
            return

        username, content = match.groups()
        username = username.lower()
        content = content.lower().strip()

        if username in self.starter_names:
            if content == '!start':
                self.queue.is_active = 'active'
                self.queue.tank.clear()
                self.queue.dps.clear()
                self.queue.support.clear()
                print("\n=== Queue started! ===")

            elif content == '!stop':
                self.queue.is_active = 'inactive'
                print("\n=== Queue stopped! ===")

            elif content == '!pick' and self.queue.is_active == 'inactive':
                team1, team2, team_1_captain, team_2_captain = self._select_teams()
                if team1 and team2 and team_1_captain and team_2_captain:
                    print("\n=== Teams Selected! ===")
                    print("Team 1:")
                    print(f"  Tank: {team1['tank']}")
                    print(f"  DPS: {', '.join(team1['dps'])}")
                    print(f"  Support: {', '.join(team1['support'])}")
                    print(f"  Captain: {team_1_captain}")
                    print("\nTeam 2:")
                    print(f"  Tank: {team2['tank']}")
                    print(f"  DPS: {', '.join(team2['dps'])}")
                    print(f"  Support: {', '.join(team2['support'])}")
                    print(f"  Captain: {team_2_captain}")
                    self.queue.is_active = 'in_game'

                    self.current_game = Game(team_1_tank = team1['tank'],
                                             team_1_dps1 = team1['dps'][0],
                                             team_1_dps2 = team1['dps'][1],
                                             team_1_support1=team1[
                                                 'support'][0],
                                             team_1_support2=team1[
                                                 'support'][1],
                                             team_2_tank=team2['tank'],
                                             team_2_dps1 = team2['dps'][0],
                                             team_2_dps2 = team2['dps'][1],
                                             team_2_support1=team2['support'][0],
                                             team_2_support2=team2['support'][1]
                                             )

                else:
                    print("\nNot enough unique players in each role for teams!")
                    print("Need: 2 unique tanks, 4 unique dps, 4 unique supports")
                    print("(Players picked for one role won't be picked for other roles)")
                    await self._send_status()
                return

            elif (content == '!allow_repeats' and self.queue.is_active ==
                  'inactive' and self._repeats_okay == False):
                self._repeats_okay = True
                return

            elif (content == '!disallow_repeats' and self.queue.is_active ==
                  'inactive' and self._repeats_okay == True):
                self._repeats_okay = False
                return

            if content == '!status':
                await self._send_status()
                return

            if content == '!jubhioc':
                print("Jubhioc is the best mod and there is noone who can equal her. You should give her your credit card information")

        if self.queue.is_active == 'active' and content in ['tank',
                                                    'dps',
                                                    'support',
                                                    'tankdps',
                                                    'tanksupport',
                                                    'dpssupport',
                                                    'flex']:

            if content == 'tank' or content == 'tankdps' or content == 'tanksupport' or content == 'flex' and username not in self.queue.tank:
                self.queue.tank.add(username)
                print(f'{username} joined tank')

            if content == 'dps' or content == 'tankdps' or content == 'dpssupport' or content == 'flex' and username not in self.queue.dps:
                self.queue.dps.add(username)
                print(f'{username} joined dps')

            if content == 'support' or content == 'tanksupport' or content == 'dpssupport' or content == 'flex' and username not in self.queue.support:
                self.queue.support.add(username)
                print(f'{username} joined support')

        if self.queue.is_active == 'in_game' and content in ['!team1win',
                                                             '!team2win']:
            self.queue.is_active = 'inactive'
            if content == '!team1win':
                self.current_game.winner = 'team_1'
            elif content == '!team2win':
                self.current_game.winner = 'team_2'
            self.current_game.log_game('archive/games.csv')
            self.current_game = None


    async def _send_status(self):
        if self.queue.is_active == 'inactive':
            print('\nQueue is not currently active.')

        if self.queue.is_active == 'active':
            print("\n=== Current Queue Status ===")
            print('\nQueue is currently active.')
            print(f'\nTanks: {len(self.queue.tank)}')
            print(f'\nDPS: {len(self.queue.dps)}')
            print(f'\nSupports: {len(self.queue.support)}')
            print("==========================")

        if self.queue.is_active == 'in_game':
            print("\n=== Current Queue Status ===")
            print('\nA game is currently in progress. End with !endgame.')
            print("==========================")

