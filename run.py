import discord
import os

from bot import Miffy


if 'BOT_TOKEN' not in os.environ:
  from dotenv import load_dotenv
  load_dotenv()

TOKEN = os.environ['BOT_TOKEN']

miffy = Miffy(command_prefix='-', intents=discord.Intents.all())

COGS = [
  'cogs.roles',
  'cogs.verification',
  'cogs.confession',
  'cogs.welcome'
]

for cog in COGS:
  miffy.load_extension(cog)


miffy.run(TOKEN)