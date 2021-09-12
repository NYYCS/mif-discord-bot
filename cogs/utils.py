from discord.ext import commands
import discord

class Utility(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command(name='send')
    @commands.is_owner()
    async def send_command(self, ctx, channel: discord.Channel, message: str):
        embed = discord.Embed(description=message, color=0x00aaff)
        await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))