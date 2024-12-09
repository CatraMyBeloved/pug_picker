from configparser import ConfigParser
import os

config = ConfigParser()
config_path = 'config/config.ini'

if os.path.exists(config_path):
    config.read(config_path)

else:
    config['Twitch'] = {
        'channel' : 'commanderx',
        'bot_username' : 'commanderxpugpicker',
        'oauth_token' : 'oauth:aeq5w8jdllall6pnjfsnwt2mxouzdb'
    }
    config['Bot'] = {
        'admins' : 'commanderx, noidea100, soverclysm'
    }

TWITCH_CHANNEL = config.get('Twitch', 'channel')
TWITCH_BOT_USERNAME = config.get('Twitch', 'bot_username')
TWITCH_OAUTH_TOKEN = config.get('Twitch', 'oauth_token')
TWITCH_WEBSOCKET_URI = 'wss://irc-ws.chat.twitch.tv:443'

BOT_ADMINS = {admin.strip() for admin in config.get('Bot', 'admins').split(',')}
