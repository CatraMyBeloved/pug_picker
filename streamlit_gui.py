import streamlit as st
import asyncio
import threading
from src.bot.twitch_bot import PickBot


# Fix for the team composition selection in streamlit_gui.py

# Add this code to the beginning of streamlit_gui.py, right after the imports

# Team composition state initialization function
def init_session_state():
    if 'tanks_per_team' not in st.session_state:
        st.session_state.tanks_per_team = 1
    if 'dps_per_team' not in st.session_state:
        st.session_state.dps_per_team = 2
    if 'supports_per_team' not in st.session_state:
        st.session_state.supports_per_team = 2


# Modify the main function's team composition section:
def main():
    st.title("PUG Picker")
    print("Started!")

    # Initialize session state
    init_session_state()

    # Initialize bot if needed
    if 'bot_initialized' not in st.session_state:
        st.session_state.bot = PickBot()
        st.session_state.bot_initialized = True

        # Set the bot's initial team composition from session state
        st.session_state.bot.tanks_per_team = st.session_state.tanks_per_team
        st.session_state.bot.dps_per_team = st.session_state.dps_per_team
        st.session_state.bot.supports_per_team = st.session_state.supports_per_team

        # Start bot in background
        def run_bot(bot):
            asyncio.run(bot.connect_and_run())

        thread = threading.Thread(target=run_bot, args=(st.session_state.bot,))
        thread.daemon = True
        thread.start()

    # Get the bot instance
    bot = st.session_state.bot

    # Connection status
    is_connected = bot.websocket is not None and hasattr(bot.websocket,
                                                         'open') and bot.websocket.open
    if is_connected:
        st.success("Connected to Twitch")
    else:
        st.error("Not connected to Twitch")

    # Team Composition Config section
    st.header("Team Composition")

    # Create update functions for each input
    def update_tanks():
        st.session_state.tanks_per_team = st.session_state.tanks_input
        bot.tanks_per_team = st.session_state.tanks_per_team

    def update_dps():
        st.session_state.dps_per_team = st.session_state.dps_input
        bot.dps_per_team = st.session_state.dps_per_team

    def update_supports():
        st.session_state.supports_per_team = st.session_state.supports_input
        bot.supports_per_team = st.session_state.supports_per_team

    # Display the inputs with their corresponding update functions
    col1, col2, col3 = st.columns(3)
    with col1:
        st.number_input(
            "Tanks per team",
            min_value=0,
            max_value=3,
            value=st.session_state.tanks_per_team,
            key="tanks_input",
            on_change=update_tanks
        )
    with col2:
        st.number_input(
            "DPS per team",
            min_value=0,
            max_value=4,
            value=st.session_state.dps_per_team,
            key="dps_input",
            on_change=update_dps
        )
    with col3:
        st.number_input(
            "Supports per team",
            min_value=0,
            max_value=4,
            value=st.session_state.supports_per_team,
            key="supports_input",
            on_change=update_supports
        )

    # Calculate total players per team
    total = st.session_state.tanks_per_team + st.session_state.dps_per_team + st.session_state.supports_per_team
    st.info(f"Total players per team: {total} (Teams of {total}v{total})")

    # Warning for non-standard teams
    is_standard = (st.session_state.tanks_per_team == 1 and
                   st.session_state.dps_per_team == 2 and
                   st.session_state.supports_per_team == 2)
    if not is_standard:
        st.warning(
            "⚠️ Non-standard team composition: Game statistics will not be logged!")

    # Rest of the code continues as before...
    # Controls in a nice row
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Toggle Queue"):
            status = bot.toggle_queue()
            st.info(status)
    with col2:
        if st.button('Reenable Queue without clearing'):
            bot.queue.is_active = 'active'

    # Queue status with refresh button side by side
    col1, col2, col3 = st.columns([3, 1, 2])  # 3:1 ratio for status vs button
    with col1:
        st.header("Queue Status")
    with col2:
        st.button("Refresh Queue", key="refresh_queue")
    with col3:
        if st.button('Enough Players?'):
            all_players = bot.queue.support | bot.queue.tank | bot.queue.dps
            valid_players = all_players
            if len(valid_players) < 10:
                st.write(f'There is not enough players, only '
                         f'{len(valid_players)} valid players.')
            if len(valid_players) >= 10:
                st.write('Yeah! YIPPIE')
    # Add this after the Queue Status section in streamlit_gui.py

    # Testing Tools Section
    st.header("Testing Tools")

    if st.button("Populate Full Queue (20 Players)"):
        status = bot.populate_full_queue(20)
        st.success(status)

    if st.button("Create Archive Directory"):
        import os
        os.makedirs("archive", exist_ok=True)
        st.success("Archive directory created (if it didn't exist)")
    # Status metrics
    col1, col2, col3 = st.columns(3)
    status = bot.get_queue_status()
    with col1:
        st.metric("Tank", status['tank_count'])
    with col2:
        st.metric("DPS", status['dps_count'])
    with col3:
        st.metric("Support", status['support_count'])

    # After queue status, maybe add expandable player lists
    with st.expander("Show Queued Players"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Tank")
            for player in status['tank_players']:
                st.write(player)
        with col2:
            st.subheader("DPS")
            for player in status['dps_players']:
                st.write(player)
        with col3:
            st.subheader("Support")
            for player in status['support_players']:
                st.write(player)

    st.header('Team selection')
    if bot.queue.is_active == 'active':
        st.write('Queue must be stopped before generating teams!')
    if bot.queue.is_active == 'ingame':
        st.write('Game must be completed before generating teams!')
    else:
        # Replace the team display section in streamlit_gui.py with this updated code

        if st.button('Generate Teams'):
            team1, team2, captain1, captain2, message = bot.generate_teams()
            if team1 and team2:
                st.success('Generated Teams!')
                bot.queue.is_active = 'ingame'
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader('Team Blue')

                    # Display tanks
                    if 'tank' in team1:
                        tanks = team1['tank']
                        if isinstance(tanks, list):
                            st.write(f"Tank: {', '.join(tanks)}")
                        else:
                            st.write(f"Tank: {tanks}")

                    # Display DPS
                    if 'dps' in team1:
                        dps = team1['dps']
                        if isinstance(dps, list):
                            st.write(f"DPS: {', '.join(dps)}")
                        else:
                            st.write(f"DPS: {dps}")

                    # Display support
                    if 'support' in team1:
                        support = team1['support']
                        if isinstance(support, list):
                            st.write(f"Support: {', '.join(support)}")
                        else:
                            st.write(f"Support: {support}")

                    st.write(f"**Captain**: {captain1}")

                with col2:
                    st.subheader('Team Red')

                    # Display tanks
                    if 'tank' in team2:
                        tanks = team2['tank']
                        if isinstance(tanks, list):
                            st.write(f"Tank: {', '.join(tanks)}")
                        else:
                            st.write(f"Tank: {tanks}")

                    # Display DPS
                    if 'dps' in team2:
                        dps = team2['dps']
                        if isinstance(dps, list):
                            st.write(f"DPS: {', '.join(dps)}")
                        else:
                            st.write(f"DPS: {dps}")

                    # Display support
                    if 'support' in team2:
                        support = team2['support']
                        if isinstance(support, list):
                            st.write(f"Support: {', '.join(support)}")
                        else:
                            st.write(f"Support: {support}")

                    st.write(f"**Captain**: {captain2}")
            else:
                st.error('Not enough unique players in the queue')

    st.header('Game management:')
    if bot.queue.is_active == 'ingame':
        st.subheader('Winner:')
        col1, col2 = st.columns(2)
        with col1:
            if st.button('Team Red'):
                bot.winner1()
                bot.queue.is_active = 'inactive'
        with col2:
            if st.button('Team Blue'):
                bot.winner2()
                bot.queue.is_active = 'inactive'

    else:
        st.subheader('No game active!')
if __name__ == "__main__":
    import sys
    import streamlit.web.bootstrap

    try:
        if getattr(sys, 'frozen', False):
            # We are running in a PyInstaller bundle
            sys.argv = ["streamlit", "run", sys.argv[0], "--server.headless",
                        "true"]
            sys.exit(streamlit.web.bootstrap.run())
        else:
            main()
    except Exception as e:
        print(f"Error occurred: {e}")
        input("Press Enter to exit...")  # This keeps the window open