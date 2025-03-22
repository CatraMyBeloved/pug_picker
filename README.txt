Pug Picker Bot
=============
Installation:
Run install.bat once to install needed libraries. After that, you can either just use run.bat to start the bot, or create shortcut for run.bat to your desktop for convenience.


Welcome to Pug Picker! This bot helps manage your Twitch channel's PUG (Pick-up Game) system.

Getting Started:
1. Read this readme
1. Make sure you have configured your Twitch credentials in the config.ini file (only if youre not commanderx)
2. Launch the bot by running run.bat (this now opens a Streamlit web interface)
3. The web interface will show the bot's status and let you control everything

Commands you can use in your Twitch Chat:
!start - Starts a queue. Viewers can now join the queue for the different roles.
!stop - Stops the queue. Viewers can no longer join.

Only usable OUTSIDE of queue (!stop has to be called first):
!pick - Creates two teams of five players from the queues and assigns captains. Viewers are only assigned to roles they queued for.
!allow_repeats - Allows players to be chosen in multiple games. By default, players can only play once.
!disallow_repeats - Disallows players from being chose in multiple games. Default behaviour.
!status - Prints state of queue and players per role.

NEW: Viewers can now join multiple roles by typing:
- tank - Join as tank only
- dps - Join as DPS only
- support - Join as support only
- tankdps - Join as both tank and DPS
- tanksupport - Join as both tank and support
- dpssupport - Join as both DPS and support
- flex - Join all three roles

NEW: Streamlit Web Interface
The bot now comes with a web interface for easier management:
- Toggle the queue on/off with a single button
- See how many players are in each role's queue
- Generate teams with one click 
- Record which team won after the match
- View detailed lists of queued players
- Testing tools for populating queues and creating directories

NEW: Statistics Dashboard
Want to see player stats? Run run_analysis.bat to open the stats dashboard:
- Check player winrates and games played
- See which roles players prefer
- Filter by date, role, or specific players
- Browse recent games with team compositions
- Track who plays captain most often

Possible configurations:
The config.ini file is located at config/config.ini

channel - The twitch chat to read
bot_username - the name of the bots twitch account
oauth_token - token to authenticate the bot with twitch. DO NOT SHOW PUBLICLY

admins - usernames of people able to use commands
repeats_allowed - allows people to be chosen for multiple games, see !allow_repeats


For support or questions:
- noidea100 on Twitch
- derstein on discord

Thank you for using Pug Picker!