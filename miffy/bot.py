from discord.ext import commands
import discord
import asyncpg

import os

from . import locks


GUILD_ID = 879252094509518908

POSTGRES_URI = os.environ['POSTGRES_URI']

class Miffy(commands.Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.pool = None

    async def start(self, *args, **kwargs):
        self.pool = await asyncpg.create_pool(POSTGRES_URI, ssl='require')
        return await super().start(*args, **kwargs)
    
    async def send(self, messageable, *, delete_after=None, **attrs):
        content = attrs.pop('content', '')
        embed = discord.Embed(**attrs, color=0x00aaff)
        await messageable.send(content, embed=embed, delete_after=delete_after)

    def lock_channel(self, channel, *, allowed_members = None):
        return locks.ChannelLock(self, channel, allowed_members=allowed_members)

    async def on_command_error(self, ctx, exception):
        await self.send(ctx, description=getattr(exception, 'original', exception))
        
    @property
    def guild(self):
        return self.get_guild(GUILD_ID)