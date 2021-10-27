import discord
import discord.utils
import os

if 'BOT_TOKEN' not in os.environ:
  	from dotenv import load_dotenv
  	load_dotenv()


from miffy.bot import Miffy


TOKEN = os.environ['BOT_TOKEN']

miffy = Miffy(command_prefix='-', intents=discord.Intents.all())

COGS = [
	'cogs.roles',
	'cogs.rooms',
	'cogs.study',
	'cogs.welcome',
	'cogs.verification'
]

for cog in COGS:
	miffy.load_extension(cog)


miffy.run(TOKEN)