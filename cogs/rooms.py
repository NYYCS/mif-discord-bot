from discord.ext import commands, tasks
from discord.utils import get
from async_timeout import timeout

from collections import namedtuple
from datetime import datetime, timedelta
from typing import OrderedDict
import asyncio

from miffy.utils import Interval, TZINFO, keypad_emoji

RoomBucket = namedtuple('RoomBucket', 'name')

class Booking:

    def __init__(self, *, interval, members):
        self.interval = interval
        self.members = members
        self.owner = members[0]

    @property
    def span(self):
        fmt = '%I:%M%p'
        start, end = self.interval.start.strftime(fmt), self.interval.end.strftime(fmt)
        return f'{start}~{end}'

class Room:

    def __init__(self, bot, **attrs):
        self.bot = bot
        self.name = attrs.pop('name')
        self.channel = attrs.pop('channel')
        self.role = attrs.pop('role')

        self._bookings = OrderedDict()
        self.occupied = False


    @classmethod
    def from_bucket(cls, bot, bucket):
        name = bucket.name
        channel = get(bot.guild.channels, name=bucket.name)
        role = get(bot.guild.roles, name=bucket.name)

        return cls(bot, name=name, channel=channel, role=role)

    def create_booking(self, *, interval, members):
        key = interval.start.timestamp()
        self._bookings[key] = booking = Booking(interval=interval, members=members)

        self.bot.loop.create_task(self._worker(booking))

        return booking
        
    async def _worker(self, booking):

        interval = booking.interval
        key = interval.start.timestamp()

        for member in booking.members:
            await self.bot.send(member, title='✅预约成功!', description=f'{self.channel.name} `{booking.span}`')

        await interval.wait_until_start()

        self.occupied = True

        for member in booking.members:
            await member.add_roles(self.role)
            await self.bot.send(member, title='你的预约的时间到了！', description=f'请点击<#{self.channel.id}>去到你预约的房间.')

        await interval.wait_until_end()

        for member in booking.members:
            await member.remove_roles(self.role)
            await self.bot.send(member, title='预约的期限离截止了', description='请速速离开！')

        await asyncio.sleep(60)
        
        for member in booking.members:
            if member.voice is not None and member.voice.channel == self.channel:
                await member.edit(voice_channel=None)

        self._bookings.pop(key)
        self.occupied = False

class Rooms(commands.Cog):

    CHANNEL_ID = 886922862957559848
    MESSAGE_ID = 888424563438944276

    ROOM_BUCKETS = [
        RoomBucket(name='📖学习讨论室-1'),
        RoomBucket(name='📖学习讨论室-2'),
        RoomBucket(name='🍿放映厅-3')
    ]
    
    def __init__(self, bot):
        self.bot = bot
        self._rooms = OrderedDict()
        self._channel = None  
        self._lock = asyncio.Lock()
        
        self.main_loop.start()
        self.update_message_loop.start()
        self._cleanup_loop.start()

    def _fill_rooms(self):
        for i, bucket in enumerate(self.ROOM_BUCKETS):
            emoji = keypad_emoji(i)
            self._rooms[emoji] = Room.from_bucket(self.bot, bucket)

    async def _update_message(self):
        message = await self._channel.fetch_message(self.MESSAGE_ID)

        embed = message.embeds[0].copy()
        lines = ['**请点击您想要预约的房间所对应的表情:**', '']
    
        for emoji, room in self._rooms.items():
            await message.add_reaction(emoji)
            schedule = ' '.join(f'`{booking.span}`' for booking in room._bookings.values())
            lines.append(f'{emoji} {room.name}: {schedule}')

        postfix = [
            ''
            '选择好您所要预约的房间后',
            '系统将会和您进入私人房间进行对话式预约',
            '请根据系统提供的格式进行相应回答',
            '完成3道问题后，您将收到预约成功信息通知',
            '确认预约信息无误后就能在您所预定的时间点和朋友一起进入讨论室啦~'
        ]

        description = '\n'.join(lines + postfix)
        embed.description = description

        await message.edit(embed=embed)

    async def get_interval(self, payload):

        def check(message):
            return payload.user_id == message.author.id and message.channel == self._channel

        await self.bot.send(self._channel, description='请把你想预约的**【时间】**告诉我。例：`10:00AM`')
        message = await self.bot.wait_for('message', check=check)

        try:
            dt = datetime.strptime(message.content, '%I:%M%p')
            start = datetime.now(TZINFO).replace(hour=dt.hour, minute=dt.minute)
        except ValueError:
            raise ValueError('给予的时间格式不正确！')

        await self.bot.send(self._channel, description='请把你想预约的**【时长】**（单位统一为分钟）告诉我。例：`80`')
        message = await self.bot.wait_for('message', check=check)

        try:
            minutes = int(message.content)
        except ValueError:
            raise ValueError('给予的时间格式不正确！')
        
        end = start + timedelta(minutes=minutes)

        return Interval(start, end)

    async def get_members(self, payload):

        def check(message):
            return payload.user_id == message.author.id and message.channel == self._channel

        await self.bot.send(self._channel, description='请利用**【@用户名】**的方式选择其他一同预约的人。例: `@总策-Evelyn @总策-悦宁`')
        message = await self.bot.wait_for('message', check=check)
        members = [
            self.bot.guild.get_member(id) for id in 
            [payload.user_id] + [mention.id for mention in message.mentions]
        ]

        return members

    async def _cleanup(self):
        async for message in self._channel.history():
            if message.id != self.MESSAGE_ID:
                await message.delete()

    @tasks.loop(minutes=5)
    async def _cleanup_loop(self):
        await self.bot.wait_until_ready()
        async with self._lock:
            await self._cleanup()

    @tasks.loop(seconds=30)
    async def update_message_loop(self):
        await self._update_message()

    @update_message_loop.before_loop
    async def before_update_message_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=1)
    async def main_loop(self):
        
        def check(payload):
            return payload.message_id == self.MESSAGE_ID and payload.emoji.name in self._rooms

        while True:
            payload = await self.bot.wait_for('raw_reaction_add', check=check)

            room = self._rooms[payload.emoji.name]
            member = self.bot.guild.get_member(payload.user_id)
            
            async with self._lock:
                async with timeout(120), self.bot.lock_channel(self._channel, allowed_members=[member]):
                    interval = await self.get_interval(payload)
                    if not interval.in_future():
                        raise ValueError('预约时间不可以在过去！')
    
                    for booking in room._bookings.values():
                        if interval.intersects(booking.interval):
                            raise ValueError('预约的时间撞到了！')
    
                    members = await self.get_members(payload)
            
            room.create_booking(interval=interval, members=members)

            await self._cleanup()
            await self._update_message()

    @main_loop.before_loop
    async def before_main_loop(self):
        await self.bot.wait_until_ready()
        self._channel = self.bot.get_channel(self.CHANNEL_ID)
        self._fill_rooms()

    @main_loop.error
    async def on_main_loop_error(self, exception):
        await self.bot.send(self._channel, description=exception)
        await self._cleanup()
        self.main_loop.restart()


def setup(bot):
    bot.add_cog(Rooms(bot))