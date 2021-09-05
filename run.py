import discord

import os

from bot import Miffy

TOKEN = os.environ['BOT_TOKEN']
CHANNEL_ID = 882857755554230312

miffy = Miffy(command_prefix='-', intents=discord.Intents.all())

@miffy.event
async def on_ready():
    channel = miffy.get_channel(CHANNEL_ID)
    await channel.send('welcome')

miffy.load_extension('roles')
miffy.load_extension('verification')

miffy.run(TOKEN)