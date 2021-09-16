from discord.ext import commands
import asyncpg

import os


GUILD_ID = 879252094509518908

POSTGRES_URI = os.environ['POSTGRES_URI']

class Miffy(commands.Bot):

    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        self.pool = None

    async def start(self, *args, **kwargs):
        self.pool = await asyncpg.create_pool(POSTGRES_URI, ssl='require')
        return await super().start(*args, **kwargs)
        
    @property
    def guild(self):
        return self.get_guild(GUILD_ID)