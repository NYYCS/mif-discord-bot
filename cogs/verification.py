from discord.ext import commands
from discord.utils import get
import discord


CHANNEL_ID = 882817947217825823

class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = get(self.bot.guild.roles, name='游客')
        await member.add_roles(role)

        message = '欢迎'

        await member.send(message)

    
    @commands.command(name='register')
    async def register_command(self, ctx, name: str, school_id: int):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            channel = self.bot.get_channel(CHANNEL_ID)
            await channel.send(f'{ctx.author} - {name} {school_id}')
            await ctx.channel.send('注册成功！请稍等....')

def setup(bot):
    bot.add_cog(Verification(bot))