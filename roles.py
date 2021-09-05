from discord.ext import commands, tasks
from discord.utils import get
import discord

from collections import namedtuple
import asyncio


MESSAGE_ID = 883959090764730379
CHANNEL_ID = 882826317127626805

RoleBucket = namedtuple('RoleBucket', 'emoji name')

# find unicode name from
# https://emojipedia.org/

ROLE_BUCKETS = [
    RoleBucket(emoji='\N{WOLF FACE}', name='狼人杀'),
    RoleBucket(emoji='\N{HOCHO}', name='剧本杀'),
    RoleBucket(emoji='\N{PICK}', name='矮人矿坑'),
    RoleBucket(emoji='\N{PENCIL}', name='你画我猜'),
]


class Roles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._roles = {}
        self._role_channel = None
        self._role_message = None

        self.main_loop.start()

    @tasks.loop(hours=1)
    async def main_loop(self):
        
        def check(payload):
            return payload.channel_id == CHANNEL_ID and payload.emoji.name in self._roles

        while True:
            try:
                tasks = [
                    self.bot.wait_for('raw_reaction_add', check=check),
                    self.bot.wait_for('raw_reaction_remove', check=check)
                ]

                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                payload = done.pop().result()

                for task in pending:
                    task.cancel()

                member = self.bot.guild.get_member(payload.user_id)
                emoji = payload.emoji.name

                role = self._roles.get(emoji)

                if role not in member.roles and role is not None:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)

            except Exception:
                raise

    @main_loop.before_loop
    async def before_main_loop(self):
        await self.bot.wait_until_ready()

        self._role_channel = self.bot.get_channel(CHANNEL_ID)
        self._role_message = await self._role_channel.fetch_message(MESSAGE_ID)

        for bucket in ROLE_BUCKETS:
            role = get(self.bot.guild.roles, name=bucket.name)
            self._roles[bucket.emoji] = role

        await self.refresh_message()

    async def refresh_message(self):

        title = ''

        description = '\n'.join([
            f'{bucket.emoji} {bucket.name:>8} -'
            for bucket in ROLE_BUCKETS
        ])

        
        await self._role_message.edit(embed=discord.Embed(title=title, description=description, color=0x00aaff))

        for bucket in ROLE_BUCKETS:
            await self._role_message.add_reaction(bucket.emoji)
            

def setup(bot):
    bot.add_cog(Roles(bot))
