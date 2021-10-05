from discord.ext import commands, tasks
from collections import namedtuple

import discord.utils
import asyncio

ROLE_MESSAGES = (
    889545146704740433,
    889545362212290632,
    889761159664795679,
    889077818854625321
)

RoleBucket = namedtuple('RoleBucket', 'emoji name')

ROLE_BUCKETS = (
    RoleBucket(emoji='\N{WOLF FACE}',                       name='狼人杀'),
    RoleBucket(emoji='\N{HOCHO}',                           name='剧本杀'),
    RoleBucket(emoji='\N{PICK}',                            name='矮人矿坑'),
    RoleBucket(emoji='\N{PENCIL}',                          name='你画我猜'),
    RoleBucket(emoji='\N{CROSSED SWORDS}',                  name='王者荣耀'),
    RoleBucket(emoji='\N{FOX FACE}',                        name='光遇'),
    RoleBucket(emoji='\N{CHICKEN}',                         name='吃鸡'),
    RoleBucket(emoji='\N{STEAM LOCOMOTIVE}',                name='柯尔特快车'),
    RoleBucket(emoji='\N{COW FACE}',                        name='谁是牛头王'),
    RoleBucket(emoji='\N{MAGE}',                            name='阿瓦隆'),
    RoleBucket(emoji='\N{FIRST QUARTER MOON WITH FACE}',    name='一夜终极狼人'),
    RoleBucket(emoji='\N{SCHOOL}',                          name='邯郸'),
    RoleBucket(emoji='\N{STETHOSCOPE}',                     name='枫林'),
    RoleBucket(emoji='\N{ROBOT FACE}',                      name='张江'),
    RoleBucket(emoji='\N{SCALES}',                          name='江湾'),
    RoleBucket(emoji='\N{ARTIST PALETTE}',                  name='美术'),
    RoleBucket(emoji='\N{PAW PRINTS}',                      name='宠物/动物'),
    RoleBucket(emoji='\N{CAMERA}',                          name='摄影'),
    RoleBucket(emoji='\N{STEAMING BOWL}',                   name='北区食堂'),
    RoleBucket(emoji='\N{ANGER SYMBOL}',                    name='动漫'),
    RoleBucket(emoji='\N{RIGHT-POINTING MAGNIFYING GLASS}', name='侦探悬疑'),
    RoleBucket(emoji='\N{FILM FRAMES}',                     name='影视'),
    RoleBucket(emoji='\N{ROLLING ON THE FLOOR LAUGHING}',   name='Memes')
)


class Roles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.roles = {}

    async def _fill_roles(self):
        for bucket in ROLE_BUCKETS:
            role = discord.utils.get(self.bot.guild.roles, name=bucket.name)
            if role is None:
                role = await self.bot.guild.create_role(name=bucket.name, mentionable=True)

            self.roles[bucket.emoji] = role

    @commands.Cog.listener()
    async def on_ready(self):
        await self._fill_roles()

    @tasks.loop(hours=1)
    async def _internal_loop(self):

        def check(payload):
            return payload.message_id in ROLE_MESSAGES and payload.emoji.name in self.roles

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
                role = self.roles[payload.emoji.name]

                if payload.event_type == 'REACTION_ADD':
                    await member.add_roles(role)

                if payload.event_type == 'REACTION_REMOVE':
                    await member.remove_roles(role)

            except Exception:
                continue
        
    @_internal_loop.before_loop
    async def before_internal_loop(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(Roles(bot))