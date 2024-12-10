import websockets
import asyncio
import random
import re

import threading
import tkinter as tk
from tkinter import PhotoImage

from src.config.settings import *
from src.bot.queue import Queue

class PickBot:
    def __init__(self):
        self.channel_name = TWITCH_CHANNEL
        self.starter_names = BOT_ADMINS
        self.queue_status = None
        self.queue_button = None
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
        self.queue_status.set(f"Queue is currently {"" if self.queue.is_active else "not "}active.\n\n{"Type one of the following to queue for pugs: tank, dps, support, tankdps, tanksupport, dpssupport, flex" if self.queue.is_active else ""}")
        print("queue started by GUI")

    def stop_round(self):
        self.queue.is_active = False
        self.queue_status.set(f"Queue is currently {"" if self.queue.is_active else "not "}active.")
        print("queue stopped by GUI")

    def queue_round(self):
        if self.queue.is_active:
            self.queue.is_active = False
            self.queue_status.set(f"Queue is currently {"" if self.queue.is_active else "not "}active.")
            self.queue_button.set("Start new queue")
            print("queue stopped by GUI")
        else:
            self.queue.is_active = True
            self.queue.tank.clear()
            self.queue.dps.clear()
            self.queue.support.clear()
            self.queue_status.set(f"Queue is currently {"" if self.queue.is_active else "not "}active.\n\n{"Type one of the following to queue for pugs: tank, dps, support, tankdps, tanksupport, dpssupport, flex" if self.queue.is_active else ""}")
            self.queue_button.set("Stop current queue")
            print("queue started by GUI")

    def pick_teams(self):
        team1, team2, team_1_captain, team_2_captain = self._select_teams()
        if team1 and team2 and team_1_captain and team_2_captain:
            # will superimpose this on image at some point instead of just printing to console
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


    def create_button(self, root, label, command_, x_, y_):
        if isinstance(label, str):
            label_ = tk.StringVar()
            label_.set(label)
        else:
            label_ = label

        button = tk.Button(root, 
                   textvariable=label_, 
                   command=command_,
                   activebackground="blue", 
                   activeforeground="white",
                   anchor="center",
                   bd=3,
                   bg="lightgray",
                   cursor="hand2",
                   disabledforeground="gray",
                   fg="black",
                   font=("Arial", 14),
                   height=3,
                   highlightbackground="black",
                   highlightcolor="green",
                   highlightthickness=2,
                   justify="left",
                   overrelief="raised",
                   padx=10,
                   pady=5,
                   width=20,
                   wraplength=200)
        button.place(x=x_, y=y_)

    def on_button_toggle(self):
        self._repeats_okay = not self._repeats_okay
        print(f"repeats flipped by GUI to {self._repeats_okay}")

    def gui_loop(self):
        root = tk.Tk()
        root.geometry("1920x1080")
        root.title("CommanderX Pug Picker")
        self.queue_button = tk.StringVar()
        self.queue_button.set("Start new queue")
    
        self.create_button(root, self.queue_button, self.queue_round, 115, 15)
        self.create_button(root, "Generate teams", self.pick_teams, 115, 125)

        # Creating a Checkbutton
        checkbutton = tk.Checkbutton(root,
                             onvalue=1, offvalue=0, command=self.on_button_toggle)
        checkbutton.config(font=("Arial", 12), 
                   selectcolor="white", padx=10, pady=5, text="Allow repeats")
        checkbutton.place(x=115, y=235)

        self.queue_status = tk.StringVar()
        self.queue_status.set(f"Queue is currently {"" if self.queue.is_active else "not "}active.{"\n\nType one of the following to queue for pugs: tank, dps, support, tankdps, tanksupport, dpssupport, flex" if self.queue.is_active else ""}")

        queue_status_label = tk.Label(root, 
                 textvariable=self.queue_status, anchor=tk.CENTER, height=7,              
                 width=35, bd=3, font=("Arial", 14, "bold"),   
                 fg="black", padx=15, pady=15, justify=tk.CENTER, relief=tk.RAISED,     
                 wraplength=400        
                )

        # Pack the label into the window
        queue_status_label.place(x=15, y=290)

        img = PhotoImage(file="img\PUGOFTHEDAYTEAMS.png")
        image_label = tk.Label(root, image=img)
        image_label.place(x=505, y=15)

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


