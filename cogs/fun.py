from typing import Union
from discord.ext import commands

import async_timeout
import discord

from .utils.paginator import SimplePaginator


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def _emote_task(self, member, emoji):
        async with async_timeout.timeout(60.0):
            while True:
                message = await self.bot.wait_for('message', check=lambda x: x.author == member)
                await message.add_reaction(emoji)
            
    @commands.command()
    async def emote(self, member: discord.Member, emoji: discord.PartialEmoji):
        self.bot.loop.create_task(self._emote_task(member, emoji))

    @commands.command()
    async def test(self, ctx):
        paginator = SimplePaginator(None)
        await ctx.send('hello', view=paginator)


def setup(bot):
    bot.add_cog(Fun(bot))