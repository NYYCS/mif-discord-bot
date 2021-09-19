import discord
import discord.utils
import os

if 'BOT_TOKEN' not in os.environ:
  	from dotenv import load_dotenv
  	load_dotenv()


from miffy.bot import Miffy


TOKEN = os.environ['BOT_TOKEN']

miffy = Miffy(command_prefix='-m', intents=discord.Intents.all())

COGS = [
	'cogs.roles',
	'cogs.utils',
	'cogs.verification',
	'cogs.rooms',
	'cogs.welcome',
]
		
for cog in COGS:
	miffy.load_extension(cog)


miffy.run(TOKEN)