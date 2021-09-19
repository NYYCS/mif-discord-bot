import random
import string

from . import utils

class ChannelLock:

    def __init__(self, bot, channel, *, allowed_members = None):
        self.bot = bot
        self.channel = channel
        self.overwrites = channel.overwrites
        self.allowed_members = allowed_members
        self._locked = False
        self._role = None

    async def __aenter__(self):
        for target in self.overwrites.keys():
            await self.channel.set_permissions(target, send_messages=False, read_messages=False, add_reactions=False)

        if self.allowed_members:
            self._role = await self.bot.guild.create_role(name=utils.random_hash(6))
            await self.channel.set_permissions(self._role, read_messages=True, send_messages=True, add_reactions=True)

            for member in self.allowed_members:
                await member.add_roles(self._role)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        for target, overwrite in self.overwrites.items():
            await self.channel.set_permissions(target, overwrite=overwrite)

        if self._role:
            await self._role.delete()
