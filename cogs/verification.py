from discord.embeds import Embed
from discord.ext import commands
from discord.utils import get
import discord


CHANNEL_ID = 882817947217825823

class Verification(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = get(self.bot.guild.roles, id=883964905965887509)

        title='👋欢迎来到【旦马公寓】!'
        description='''请同学利用`-mregister 全名 名字`进行注册!
        例子：`-mregister 黄宇悦 20300246005`
        '''
        
        await member.send(embed=discord.Embed(title=title, description=description, color=0x00aaff))
        await member.add_roles(role)
    
    @commands.command(name='register')
    async def register_command(self, ctx, name: str, school_id: int):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            channel = self.bot.get_channel(CHANNEL_ID)
            await channel.send(f'{ctx.author} - {name} {school_id}')
            description='✅注册成功！请稍等....'
            await ctx.channel.send(embed=discord.Embed(description=description, color=0x00aaff))

def setup(bot):
    bot.add_cog(Verification(bot))