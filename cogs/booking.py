from collections import namedtuple
from discord.ext import commands, tasks
from discord.utils import get
import discord
import asyncio

from datetime import datetime, timedelta, timezone

# Kuala Lumpur, Malaysia GMT+8
TZINFO = timezone(timedelta(hours = 8))

async def sleep_until(dt, tzinfo = TZINFO):
    delta = max(0.0, (dt - datetime.now(tzinfo)).total_seconds())
    if delta > 0.0:
        await asyncio.sleep(delta)


class Worker:

    def __init__(self, bot, **attrs):
        self.bot = bot
        self.interval = attrs.pop('interval')
        self.channel = attrs.pop('channel')
        self.members = attrs.pop('members')
        self.role = attrs.pop('role')

        self._task = None
        self.working = False

    async def task(self):
        await self.interval.wait_until_start()

        for member in self.members:
            await member.add_roles(self.role)
            await member.send(embed=discord.Embed(title='你的预约的时间到了！', description=f'请点击<#{self.channel.id}>去到你预约的房间.', color=0x00aaff))

        await self.interval.wait_until_end()

        for member in self.members:
            await member.remove_roles(self.role)
            await member.send(embed=discord.Embed(title='预约的期限离截止了！', description='请速速离开！', color=0x00aaff)) 
        
        await asyncio.sleep(60)

        for member in self.members:
            if member.voice.channel is not None:
                await member.edit(voice_channel=None)


    def start(self):
        self._task = self.bot.loop.create_task(self.task())
        self.working = True


CHANNEL_ID = 886922862957559848
MESSAGE_ID = 888424563438944276

RoomBucket = namedtuple('RoomBucket', 'emoji channel_id role_id')

ROOM_BUCKETS = [
    RoomBucket(emoji='1\ufe0f\u20e3', channel_id=888423117351972894, role_id=888423240203137094),
    RoomBucket(emoji='2\ufe0f\u20e3', channel_id=888423825564389417, role_id=888423964270002237),
]

class Booking(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._channel = None
        self._rooms = {}
        self._workers = {}
        self.main_loop.start()


    async def _get_booking_details(self, payload):
        
        channel = self.bot.get_channel(CHANNEL_ID)

        def check(message):
            return message.author.id == payload.user_id and message.channel == channel

        await channel.send(embed=discord.Embed(description='请写出预约的时间. 例: `10:00AM`', color=0x00aaff))
        start = (await self.bot.wait_for('message', check=check)).content

        await channel.send(embed=discord.Embed(description='请写出预约为期几久（分钟）. 例: `180`', color=0x00aaff))
        duration = int((await self.bot.wait_for('message', check=check)).content)

        interval = TimeInterval(start, duration)
        if not interval.in_future():
            raise ValueError("预约的时间一定是要在未来！")

        await channel.send(embed=discord.Embed(description='请利用@得方式指定其他预约的人. 例: `@总策- 黄宇悦 @总策- Evelyn`'))
        mentions = (await self.bot.wait_for('message', check=check)).mentions

        members = [
            self.bot.guild.get_member(id) for id in 
            [payload.user_id, *[mention.id for mention in mentions]]
        ]

        return interval, members

        
    @tasks.loop(hours=1)
    async def main_loop(self):

        def check(payload):
            return payload.message_id == MESSAGE_ID

        while True:
            try:
                payload = await self.bot.wait_for('raw_reaction_add', check=check)
                member = self.bot.guild.get_member(payload.user_id)

                channel, role = self._rooms[payload.emoji.name]

                async with self.bot.lock_channel(self._channel, allowed_members=[member]):
                    interval, members = await self._get_booking_details(payload)

                worker = Worker(self.bot, channel=channel, role=role, interval=interval, members=members)


                worker.start()

            except Exception:
                raise 

    @main_loop.before_loop
    async def before_main_loop(self):
        await self.bot.wait_until_ready()
        self._channel = self.bot.get_channel(CHANNEL_ID)

        for bucket in ROOM_BUCKETS:
            channel = self.bot.get_channel(bucket.channel_id)
            role = get(self.bot.guild.roles, id=bucket.role_id)
            self._rooms[bucket.emoji] = channel, role 

def setup(bot):
    bot.add_cog(Booking(bot))