from discord.ext import commands

GUILD_ID = 879252094509518908

class Miffy(commands.Bot):

    @property
    def guild(self):
        return self.get_guild(GUILD_ID)