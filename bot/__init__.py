from telethon import TelegramClient
from .config import Config

import logging

logging.basicConfig(level=logging.INFO)


config = Config(debug=False)


API_ID = config.get_property('API_ID')
API_HASH = config.get_property('API_HASH')

bot = TelegramClient(config.get_property('SESSION_NAME'), API_ID, API_HASH)
bot.start(bot_token=config.get_property('TOKEN'))

