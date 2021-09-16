import discord
import discord.utils
import os

if 'BOT_TOKEN' not in os.environ:
  	from dotenv import load_dotenv
  	load_dotenv()


from bot import Miffy


TOKEN = os.environ['BOT_TOKEN']

miffy = Miffy(command_prefix='-m', intents=discord.Intents.all())



miffy.run(TOKEN)