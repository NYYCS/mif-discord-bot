from discord.embeds import Embed
from discord.ext import commands

import discord.utils
import discord


VERIFICATION_CHANNEL = 882817947217825823
NEW_MEMBER_ROLE      = 883964905965887509


class Verify(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(VERIFICATION_CHANNEL)
        self.role = discord.utils.get(self.bot.guild.roles, id=NEW_MEMBER_ROLE)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(color=discord.Color.teal())
        embed.title = '👋欢迎来到【旦马公寓】!'
        embed.description = '请同学利用`-register 全名 名字`进行注册!\n' \
                            '例子：`-register 黄宇悦 20300246005`'

        await member.add_roles(self.role)
        await member.send(embed=embed)

    @commands.command()
    async def register(self, ctx, name: str, school_id: str):
        if isinstance(ctx.channel, discord.DMChannel):
            member = self.bot.guild.get_member(ctx.author.id)
            await member.send(embed=discord.Embed(description='✅注册成功！请稍等....'), color=discord.Color.teal())
            await self.channel.send(f'{member.mention} - {name}: {school_id}')


def setup(bot):
    bot.add_cog(Verify(bot))