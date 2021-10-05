from discord.flags import Intents
from bot import Bot

import asyncpg
import asyncio
import discord
import os

if 'BOT_TOKEN' not in os.environ:
    from dotenv import load_dotenv
    load_dotenv()

BOT_TOKEN    = os.environ['BOT_TOKEN']
POSTGRES_URL = os.environ['POSTGRES_URL']

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    pool = loop.run_until_complete(asyncpg.create_pool(POSTGRES_URL, ssl='require'))
    bot = Bot('-', intents=discord.Intents.all())
    bot.pool = pool
    bot.run(BOT_TOKEN)