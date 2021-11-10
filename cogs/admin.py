from discord.ext import commands

import discord
import aiohttp


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    async def cog_after_invoke(self, ctx):
        pass
    
    @commands.command()
    async def add(self, ctx, cog_name, id: str):
        url = f'https://pastebin.com/raw/{id}'
        async with aiohttp.ClientSession() as session:
            async with sessiosn.get(url) as resp:
                text = await resp.text()
                with open(f'{cog_name}.py', 'w') as file:
                    file.write(text)
        await ctx.send(embed=discord.Embed(description=f'Successfully downloaded cog file from `{url}`'))
        self.bot.load_extension(f'cogs/{cog_name}')
    
    @commands.command()
    async def reload(self, ctx, cog_name):
        self.bot.reload_extension(cog_name)
        await ctx.send(embed=discord.Embed(description=f'Successfully reloaded `{cog_name}`'))


def setup(bot):
    bot.add_cog(Admin(bot))