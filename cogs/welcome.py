from discord.ext import commands
import discord

CHANNEL_ID = 883967508934193192

class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(CHANNEL_ID)
        description = f'👋欢迎`{member}`来到【旦马公寓】!\n请记得检查你的私信进行注册！'
        await channel.send(embed=discord.Embed(description=description, color=0x00aaff))


def setup(bot):
    bot.add_cog(Welcome(bot))