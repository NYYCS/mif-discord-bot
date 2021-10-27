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

    async def cog_before_invoke(self, ctx):
        return any((role in ctx.author.roles for role in self._roles))

    @commands.command(name='send')
    async def send_command(self, ctx, channel: discord.channel.TextChannel, message: discord.Message, title: str = ''):
        embed = discord.Embed(title=title, description=message.content, color=0x00aaff)
        await channel.send(embed=embed)

    @commands.command(name='edit')
    async def edit_command(self, ctx, target: discord.Message, message: discord.Message, title: str = ''):
        embed = discord.Embed(title=title, description=message.content, color=0x00aaff)
        await target.edit(embed=embed)


def setup(bot):
    bot.add_cog(Utility(bot))