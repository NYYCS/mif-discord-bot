from discord.ext import commands
import discord

import asyncio


CHANNEL_ID = 884004806203691028

class Confession(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='confess')
    async def confess_command(self, ctx):
        if isinstance(ctx.channel, discord.channel.DMChannel):
            await ctx.send('写出你的表白吧, 要取消写`cancel`')

            def check(message):
                return message.author == ctx.author and isinstance(message.channel, discord.channel.DMChannel)

            try:
                message = await self.bot.wait_for('message', check=check, timeout=10 * 60)
            except asyncio.TimeoutError:
                await ctx.send('写太慢了！')
            else:
                channel = self.bot.get_channel(CHANNEL_ID)
                await channel.send(message.content)

def setup(bot):
    bot.add_cog(Confession(bot))