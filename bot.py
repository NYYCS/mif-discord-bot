from discord.ext import commands

import discord

MIF_GUILD = 879252094509518908

EXTENSIONS = [
    'cogs.fun',
    'cogs.study',
    'cogs.sql',
    'cogs.verify',
    'cogs.welcome',
    'cogs.roles',
    'cogs.rooms',
    'cogs.admin'
]
class Bot(commands.Bot):

    def __init__(self, command_prefix, description=None, **options):
        super().__init__(command_prefix, description=description, **options)
        self.pool = None

        for extension in EXTENSIONS:
            self.load_extension(extension)

    async def on_command_error(self, ctx, exception) -> None:
        if not isinstance(exception, commands.CommandNotFound):
            exception = getattr(exception, 'original', exception)
            embed = discord.Embed(color=discord.Color.brand_red())
            embed.description = str(exception)
            await ctx.send(embed=embed)


    @property
    def guild(self):
        return self.get_guild(MIF_GUILD)
    