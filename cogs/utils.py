from discord.ext import commands
from discord.utils import get
import discord

ROLE_IDS = [
    879253452432211968,
    883958187114512435,
    883958188074991647,
    882817709136552018
]

class Utility(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot
        self._roles = []

    @commands.Cog.listener()
    async def on_ready(self):
        self._roles = [
            get(self.bot.guild.roles, id=role_id)
            for role_id in ROLE_IDS
        ]

    @commands.command(name='send')
    async def send_command(self, ctx, channel: discord.channel.TextChannel, message: discord.Message, title: str = ''):
        print(self._roles)
        if any((role in ctx.author.roles for role in self._roles)):
            print(self._roles)
            embed = discord.Embed(title=title, description=message.content, color=0x00aaff)
            await channel.send(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))