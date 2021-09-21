from discord.ext import commands, tasks
from discord.utils import get
import discord

from collections import namedtuple
import asyncio


MESSAGE_IDS = [
    889545146704740433,
    889545362212290632,
    889077818854625321
]

RoleBucket = namedtuple('RoleBucket', 'emoji name description')

# find unicode name from
# https://emojipedia.org/

ROLE_BUCKETS = [
    RoleBucket(emoji='\N{WOLF FACE}', name='狼人杀', description=''),
    RoleBucket(emoji='\N{HOCHO}', name='剧本杀', description=''),
    RoleBucket(emoji='\N{PICK}', name='矮人矿坑', description=''),
    RoleBucket(emoji='\N{PENCIL}', name='你画我猜', description=''),
    RoleBucket(emoji='\N{CROSSED SWORDS}', name='王者荣耀', description=''),
    RoleBucket(emoji='\N{FOX FACE}', name='光遇', description=''),
    RoleBucket(emoji='\N{CHICKEN}', name='吃鸡', description=''),
    RoleBucket(emoji='\N{STEAM LOCOMOTIVE}', name='柯尔特快车', description=''),
    RoleBucket(emoji='\N{COW FACE}', name='谁是牛头王', description=''),
    RoleBucket(emoji='\N{MAGE}', name='阿瓦隆', description=''),
    RoleBucket(emoji='\N{FIRST QUARTER MOON WITH FACE}', name='一夜终极狼人', description=''),
    #
    RoleBucket(emoji='\N{SCHOOL}', name='邯郸', description=''),
    RoleBucket(emoji='\N{STETHOSCOPE}', name='枫林', description=''),
    RoleBucket(emoji='\N{ROBOT FACE}', name='张江', description=''),
    RoleBucket(emoji='\N{SCALES}', name='江湾', description=''),
    #
    RoleBucket(emoji='\N{ARTIST PALETTE}', name='美术', description=''),
    RoleBucket(emoji='\N{PAW PRINTS}', name='宠物/动物', description=''),
    RoleBucket(emoji='\N{CAMERA}', name='摄影', description=''),
    RoleBucket(emoji='\N{STEAMING BOWL}', name='北区食堂', description=''),
    RoleBucket(emoji='\N{ANGER SYMBOL}', name='动漫', description=''),
    RoleBucket(emoji='\N{RIGHT-POINTING MAGNIFYING GLASS}', name='侦探悬疑', description=''),
    RoleBucket(emoji='\N{FILM FRAMES}', name='影视', description=''),
    RoleBucket(emoji='\N{ROLLING ON THE FLOOR LAUGHING}', name='Memes', description=''),
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
            return payload.message_id in MESSAGE_IDS and payload.emoji.name in self._roles

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

                if payload.event_type == 'REACTION_ADD':
                   await member.add_roles(role)
                
                if payload.event_type == 'REACTION_REMOVE':
                   await member.remove_roles(role)

            except Exception:
                continue

    @main_loop.before_loop
    async def before_main_loop(self):
        await self.bot.wait_until_ready()

        for bucket in ROLE_BUCKETS:
            role = get(self.bot.guild.roles, name=bucket.name)

            if role is None:
               role = await self.bot.guild.create_role(name=bucket.name, mentionable=True)
                
            self._roles[bucket.emoji] = role



def setup(bot):
    bot.add_cog(Roles(bot))
