from collections import namedtuple
from discord.ext import commands, tasks
from datetime import datetime
from typing import OrderedDict

from .utils.time import Period
from .utils import time

import async_timeout
import discord.utils
import discord
import asyncio


def to_readable_time(dt):
    return dt.strftime('%I:%M%p')

class RoomError(commands.CheckFailure):
    pass

class Booking:

    def __init__(self, room, members, period):
        self.room = room
        self.members = members
        self.period = period

    def timespan(self):
        start, end = to_readable_time(self.period.start), to_readable_time(self.period.end)
        return f'{start}~{end}'

    async def on_create(self):
        for member in self.members:
            await member.send(embed=discord.Embed(title='✅预约成功!', description=f'{self.channel} `{self.timespan()}`'))

    async def on_start(self):
        for member in self.members:
            await member.add_roles(self.room.role)
            await member.send(embed=discord.Embed(title='你的预约的时间到了!', description=f'请点击<#{self.channel.id}>去到你预约的房间.'))

    async def on_end(self):
        for member in self.members:
            await member.remove_roles(self.room.role)
            await member.send(embed=discord.Embed(title='预约的期限离截止了', description='请速速离开！'))
        await asyncio.sleep(BOOKING_END_GRACE_PERIOD)
        await self._kick_members_from_room()

    async def _kick_members_from_room(self):
        for member in self.members:
            if member.voice is not None and member.voice.channel == self.room.channel:
                await member.edit(voice_channel=None)


BOOKING_END_GRACE_PERIOD = 30

class Room:

    def __init__(self, bot, bucket):
        self.bot = bot
        self.role = discord.utils.get(self.bot.guild.roles, name=bucket.name)
        self.channel =  discord.utils.get(self.bot.guild.channels, name=bucket.name)
        self.bookings = OrderedDict()
        self.occupied = False
        
    def create_booking(self, members, period):
        self.bookings[period.start] = booking = Booking(self, members, period)
        self.bot.loop.create_task(self._internal_worker(booking))
        return booking
    
    async def _internal_worker(self, booking):
        await booking.on_create()
        await booking.period.wait_until_start()
        await booking.on_start()
        self.occupied = True
        await booking.on_end()
        self.occupied = False


RoomBucket = namedtuple('RoomBucket', 'name')

ROOM_BOOKING_CHANNEL = 886922862957559848
ROOM_BOOKING_MESSAGE = 889560157376352256
ROOM_BOOKING_TIMEOUT = 120

ROOM_BUCKETS = (
    RoomBucket(name='📖学习讨论室-1'),
    RoomBucket(name='📖学习讨论室-2'),
    RoomBucket(name='🎬私人影院-1'),
    RoomBucket(name='🎬私人影院-2'),
    RoomBucket(name='🎤唱k房-1'),
    RoomBucket(name='🎤唱k房-2'),
)

class Rooms(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.rooms = OrderedDict()
        self.lock = asyncio.Lock()
        self.channel = None
        self.message = None
        self._internal_main_loop.start()
        self._internal_cleanup_loop.start()
        self._internal_update_loop.start()

    async def _fill_rooms(self):
        for index, bucket in enumerate(ROOM_BUCKETS, 1):
            self.rooms[f'{index}\ufe0f\u20e3'] = Room(self.bot, bucket)

    @commands.Cog.listener()
    async def on_ready(self):
        self.channel = channel = self.bot.get_channel(ROOM_BOOKING_CHANNEL)
        self.message = await channel.fetch_message(ROOM_BOOKING_MESSAGE)
        await self._fill_rooms()

    async def prompt(self, messageable, event, *, check, timeout=None, **kwargs):
        await messageable.send(**kwargs)
        return await self.bot.wait_for(event, check=check, timeout=timeout)

    async def _get_booking_details(self, payload):

        def check(message):
            return payload.user_id == message.author.id and message.channel == self.channel

        message = await self.prompt(self.channel, 'message', check=check, embed=discord.Embed(description='请把你想预约的**【时间】**告诉我。例：`10:00AM`'))

        try:
            dt = datetime.strptime(message.content, '%I:%M%p')
            start = time.dtnow().replace(hour=dt.hour, minute=dt.minute)
        except ValueError:
            raise RoomError('给予的时间格式不正确！')

        message = await self.prompt(self.channel, 'message', check=check, embed=discord.Embed(description='请把你想预约的**【时长】**（单位统一为分钟）告诉我。例：`80`'))

        try:
            minutes = int(message.content)
        except ValueError:
            raise RoomError('给予的时间格式不正确！')

        period = Period.from_duration(start=start, minutes=minutes)

        message = await self.prompt(self.channel, 'message', check=check, embed=discord.Embed(description='请利用**【@用户名】**的方式选择其他一同预约的人。例: `@总策-Evelyn @总策-悦宁`'))

        members = [
            self.bot.guild.get_member(id) for id in 
            [payload.user_id] + [mention.id for mention in message.mentions]
        ]

        return period, members


    @tasks.loop(hours=1)
    async def _internal_main_loop(self):
        await self.bot.wait_until_ready()

        def check(payload):
            return payload.message_id == self.message.id and payload.emoji.name in self.rooms

        while True:
            payload = await self.bot.wait_for('raw_reaction_add', check=check)
            room = self.rooms[payload.emoji.name]
            member = self.bot.guild.get_member(payload.user_id)

            await self.message.remove_reaction(payload.emoji.name, member)

            async with async_timeout.timeout(ROOM_BOOKING_TIMEOUT):
                async with self.lock:
                    period, members = await self._get_booking_details(payload)
                    if not period.in_future():
                        raise RoomError('预约时间不可以在过去！')
    
                    for booking in room.bookings.values():
                        if period.intersects(booking.period):
                            raise RoomError('预约的时间撞到了！')

            room.create_booking(members, period)
            await self.cleanup()
            await self.update_rooms()

    @_internal_main_loop.error
    async def on_error(self, exception):
        exception = getattr(exception, 'original', exception)
        embed = discord.Embed(color=discord.Color.brand_red())
        embed.description = str(exception)
        await self.channel.send(embed=embed)
        await self.cleanup()
        self._internal_main_loop.restart()

    async def cleanup(self):
        if self.channel:
            async with self.lock:
                async for message in self.channel.history():
                    if message != self.message:
                        await message.delete()

    async def update_rooms(self):
        if self.message:
            embed = self.message.embeds[0].copy()
            lines = []
            for emoji, room in self.rooms.items():
                line = '{0} - {1}: {2}'.format(
                    emoji, 
                    room.channel, 
                    ', '.join(f'`{booking.timespan()}`' for booking in room.bookings.values())
                )
                lines.append(line)
            rooms = '\n'.join(lines)
            embed.description = '\n'.join([f'**请点击您想要预约的房间所对应的表情:**',                          
                                           f'',                                                           
                                           f'{rooms}',                                         
                                           f'',                                                           
                                           f'选择好您所要预约的房间后',                                        
                                           f'系统将会和您进入**对话式预约**',                                  
                                           f'请根据系统提供的格式**进行相应回答**',                              
                                           f'完成3道问题后，您将收到预约成功信息通知',                             
                                           f'**确认预约信息无误**后就能在您所预定的时间点和朋友一起进入讨论室啦~'])

            await self.message.edit(embed=embed)
                

    @tasks.loop(minutes=2)
    async def _internal_cleanup_loop(self):
        await self.bot.wait_until_ready()
        await self.cleanup()

    @tasks.loop(minutes=2)
    async def _internal_update_loop(self):
        await self.bot.wait_until_ready()
        await self.update_rooms()


def setup(bot):
    bot.add_cog(Rooms(bot))