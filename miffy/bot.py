from discord import message
from discord.ext import commands
import discord

from . import locks

import os


GUILD_ID = 879252094509518908

POSTGRES_URI = os.environ['POSTGRES_URI']

class Miffy(commands.Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.pool = None

    async def start(self, *args, **kwargs):
        return await super().start(*args, **kwargs)
    
    async def send(self, messageable, *, delete_after=None, **attrs):
        embed = discord.Embed(**attrs, color=0x00aaff)
        await messageable.send(embed=embed, delete_after=delete_after)

    def lock_channel(self, channel, *, allowed_members = None):
        return locks.ChannelLock(self, channel, allowed_members=allowed_members)
        
    @property
    def guild(self):
        return self.get_guild(GUILD_ID)