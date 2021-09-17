from discord.ext import commands, tasks
from discord.utils import get

from collections import namedtuple
from datetime import datetime, timedelta
import asyncio

from miffy.utils import Interval, TZINFO

RoomBucket = namedtuple('RoomBucket', 'name')

class Booking:

    def __init__(self, *, interval, members):
        self.interval = interval
        self.members = members
        self.owner = members[0]


class Room:

    def __init__(self, bot, **attrs):
        self.bot = bot
        self.channel = attrs.pop('channel')
        self.role = attrs.pop('role')

        self.bookings = {}
        self.occupied = False

    @classmethod
    def from_bucket(cls, bot, bucket):
        channel = get(bot.guild.channels, name=bucket.name)
        role = get(bot.guild.roles, name=bucket.name)

        return cls(bot, channel=channel, role=role)

    def create_booking(self, *, interval, members):
        key = interval.start.timestamp()
        self.bookings[key] = booking = Booking(interval=interval, members=members)

        self.bot.loop.create_task(self._worker(booking))

        return booking
        
    async def _worker(self, booking):

        interval = booking.interval
        start, end = interval.start, interval.end
        
        for member in booking.members:
            await self.bot.send(member, title='✅预约成功!', description=f'{self.channel.name} {start.time()} - {end.time()}')

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
            if member.voice.channel == self.channel:
                member.edit(voice_channel=None)

        self.occupied = False
     

class Rooms(commands.Cog):

    CHANNEL_ID = 886922862957559848
    MESSAGE_ID = 888424563438944276

    ROOM_BUCKETS = [
        RoomBucket(name='📖学习讨论室-1'),
        RoomBucket(name='📖学习讨论室-2')
    ]
    
    def __init__(self, bot):
        self.bot = bot
        self._rooms = {}
        self._channel = None

        self.main_loop.start()

    def _fill_rooms(self):
        fmt = '{0}\ufe0f\u20e3'
        for i, bucket in enumerate(self.ROOM_BUCKETS):
            emoji = fmt.format(i)
            self._rooms[emoji] = Room.from_bucket(self.bot, bucket)
        
    async def get_interval(self, payload):

        def check(message):
            return payload.user_id == message.author.id and message.channel == self._channel

        await self.bot.send(self._channel, description='请写出预约的时间. 例: `10:00AM`')
        message = await self.bot.wait_for('message', check=check)

        try:
            dt = datetime.strptime(message.content, '%I:%M%p')
            start = datetime.now(TZINFO).replace(hour=dt.hour, minute=dt.hour)
        except ValueError:
            raise ValueError('给予的时间格式不正确！')

        await self.bot.send(self._channel, description='请写出预约为期几久（分钟）. 例: `180`')
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

    @tasks.loop(hours=1)
    async def main_loop(self):
        
        def check(payload):
            return payload.message_id == self.MESSAGE_ID and payload.emoji.name in self._rooms

        while True:
            payload = await self.bot.wait_for('raw_reaction_add', check=check)
            room = self._rooms[payload.emoji.name]
        
            interval = await self.get_interval(payload)

            if not interval.in_future():
                raise ValueError('时间不能在过去！')

            members = await self.get_members(payload)

            room.create_booking(interval=interval, members=members)

    @main_loop.before_loop
    async def before_main_loop(self):
        await self.bot.wait_until_ready()
        self._channel = self.bot.get_channel(self.CHANNEL_ID)
        self._fill_rooms()

def setup(bot):
    bot.add_cog(Rooms(bot))