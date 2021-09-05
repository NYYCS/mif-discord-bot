from discord.ext import commands

CHANNEL_ID = 883967508934193192

class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(CHANNEL_ID)
        await channel.send(f'欢迎新人 {member}')