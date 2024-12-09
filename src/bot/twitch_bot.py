import websockets
import asyncio
import random
import re

import threading
import tkinter as tk

from src.config.settings import *
from src.bot.queue import Queue

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

    def start_round(self):
        self.queue.is_active = True
        self.queue.tank.clear()
        self.queue.dps.clear()
        self.queue.support.clear()
        print("round started by GUI")

    def stop_round(self):
        self.queue.is_active = False
        print("round stopped by GUI")

    def create_button(self, root, label, command_):
        button = tk.Button(root, 
                   text=label, 
                   command=command_,
                   activebackground="blue", 
                   activeforeground="white",
                   anchor="center",
                   bd=3,
                   bg="lightgray",
                   cursor="hand2",
                   disabledforeground="gray",
                   fg="black",
                   font=("Arial", 12),
                   height=2,
                   highlightbackground="black",
                   highlightcolor="green",
                   highlightthickness=2,
                   justify="left",
                   overrelief="raised",
                   padx=10,
                   pady=5,
                   width=15,
                   wraplength=100)
        button.pack(padx=20, pady=20)

    def on_button_toggle(self):
        self._repeats_okay = not self._repeats_okay
        print(f"repeats flipped by GUI to {self._repeats_okay}")

    def gui_loop(self):
        root = tk.Tk()
        root.geometry("1280x720")
        root.title("CommanderX Pug Picker")
    
        self.create_button(root, "Start new round here", self.start_round)
        self.create_button(root, "Stop current round here", self.stop_round)

        # Creating a Checkbutton
        checkbutton = tk.Checkbutton(root, text="Enable Feature", 
                             onvalue=1, offvalue=0, command=self.on_button_toggle)
        checkbutton.config(bg="lightgrey", fg="blue", font=("Arial", 12), 
                   selectcolor="white", relief="raised", padx=10, pady=5, text="allow repeats")
        checkbutton.pack(padx=40, pady=40)
        checkbutton.flash()

        text_var = tk.StringVar()
        text_var.set(f"Queue is currently {"" if self.queue.is_active else "not "}active.")

        # Start the GUI event loop
        root.mainloop()


    async def connect_and_run(self):

        # setting up gui thread
        gui_thread = threading.Thread(target=self.gui_loop)
        gui_thread.start()

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
            raise  # Re-raise to trigger reconnection
        except Exception as e:
            print(f"Connection error: {str(e)}")
            raise  # Re-raise to trigger reconnection

    # Rest of your existing methods remain unchanged...


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
                self.queue.is_active = True
                self.queue.tank.clear()
                self.queue.dps.clear()
                self.queue.support.clear()
                print("\n=== Queue started! ===")

            elif content == '!stop':
                self.queue.is_active = False
                print("\n=== Queue stopped! ===")

            elif content == '!pick' and self.queue.is_active == False:
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
                else:
                    print("\nNot enough unique players in each role for teams!")
                    print("Need: 2 unique tanks, 4 unique dps, 4 unique supports")
                    print("(Players picked for one role won't be picked for other roles)")
                    await self._send_status()
                return
            elif content == '!allow_repeats' and self.queue.is_active == False and self._repeats_okay == False:
                self._repeats_okay = True
                return
            elif content == '!disallow_repeats' and self.queue.is_active == False and self._repeats_okay == True:
                self._repeats_okay = False
                return
            if content == '!status':
                await self._send_status()
                return
            if content == '!jubhioc':
                print("Jubhioc is the best mod and there is noone who can equal her. You should give her your credit card information")
        if self.queue.is_active == True and content in ['tank', 'dps', 'support', 'tankdps', 'tanksupport', 'dpssupport', 'flex']:
            if content == 'tank' or content == 'tankdps' or content == 'tanksupport' or content == 'flex' and username not in self.queue.tank:
                self.queue.tank.add(username)
                print(f'{username} joined tank')
            if content == 'dps' or content == 'tankdps' or content == 'dpssupport' or content == 'flex' and username not in self.queue.dps:
                self.queue.dps.add(username)
                print(f'{username} joined dps')
            if content == 'support' or content == 'tanksupport' or content == 'dpssupport' or content == 'flex' and username not in self.queue.support:
                self.queue.support.add(username)
                print(f'{username} joined support')


    async def _send_status(self):
        if not self.queue.is_active:
            print('\nQueue is not currently active.')

        else:
            print("\n=== Current Queue Status ===")
            print('\nQueue is currently active.')
            print(f'\nTanks: {len(self.queue.tank)}')
            print(f'\nDPS: {len(self.queue.dps)}')
            print(f'\nSupports: {len(self.queue.support)}')
            print("==========================")


