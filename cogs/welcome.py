from discord.ext import commands

import discord

WELCOME_CHANNEL = 883967508934193192

class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = self.bot.get_channel(WELCOME_CHANNEL)
    
    @commands.Cog.listener()
    async def on_member_join(self, member):
        embed = discord.Embed(color=discord.Color.teal())
        embed.description = f'👋欢迎`{member}`来到【旦马公寓】!\n' \
                             '请记得检查你的私信进行注册！'
        await self.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Welcome(bot))