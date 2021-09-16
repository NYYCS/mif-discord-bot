from discord.ext import commands, tasks

from datetime import datetime, timedelta, timezone
import asyncio

TZINFO = timezone(timedelta(hours=8))

class ChannelBucket:
    
    def __init__(self, id, *, member_limit = None, time_limit = None):
        self.id = id
        self.member_limit = member_limit
        self.time_limit = time_limit


CHANNEL_BUCKETS = {
    '\N{HOCHO}': ChannelBucket(887370150179897385),                                   # 放映院-2
    '\N{WOLF FACE}': ChannelBucket(887359188605501471, member_limit = 5, time_limit = 2)  # 🎙预约 K房
}

async def sleep_until(dt):
     delta = max(0.0, (dt - datetime.now(TZINFO)).total_seconds())
     print(delta)
     if delta > 0.0:
         print("sleep")
         await asyncio.sleep(delta)

class TimePeriod:

    def __init__(self, start, duration):
        try:
            time = datetime.strptime(start, '%I:%M%p')
            self.start = datetime.now(TZINFO).replace(hour=time.hour, minute=time.minute)
        except ValueError:
            try:
                self.start = datetime.strptime("%d-%m-%I %M%p")
            except ValueError:
                raise

        self.duration = timedelta(minutes=duration)
        self.end = self.start + self.duration

    def in_future(self):
        return self.start > datetime.now()

    def intersects(self, obj):
        return any((
                self.start < obj.start < self.end,
                self.start < obj.end < self.end, 
                obj.start < self.start < obj.end,
                obj.start < self.end < obj.start
            ))

    def __contains__(self, dt):
        return self.start < dt < self.end

    async def wait_until_start(self):
        await sleep_until(self.start)
    
    async def wait_until_end(self):
        await sleep_until(self.end)


CHANNEL_ID = 886922862957559848
MESSAGE_ID = 887612455864389632



class _Booking(commands.Cog):

    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self._bookings = {

        }
        self.booking_loop.start()

    async def book(self, bucket, payload):
        channel = self.bot.get_channel(CHANNEL_ID)

        await channel.send('please give the time of booking')
        message = await self.bot.wait_for('message', check=lambda x: x.author.id == payload.user_id)
        start = message.content

        await channel.send('please give the duration of booking in minutes')
        message = await self.bot.wait_for('message', check=lambda x: x.author.id == payload.user_id)
        duration = int(message.content)

        period = TimePeriod(start, duration)
        print(period.start, period.end)

        task = self.bot.loop.create_task(
            self.worker(bucket, period)
        )

        print('ok')

    async def worker(self, bucket, period):
        channel = self.bot.get_channel(CHANNEL_ID)
        await period.wait_until_start()
        await channel.send('starting now')
        await period.wait_until_end()
        await channel.send('end')

    
    @tasks.loop(hours=1)
    async def booking_loop(self):
        while True:
            payload = await self.bot.wait_for('raw_reaction_add', check=lambda x: x.channel_id == CHANNEL_ID)
            bucket = CHANNEL_BUCKETS.get(payload.emoji.name)
            
            

    @commands.Cog.listener()
    async def on_ready(self):
        channel = self.bot.get_channel(CHANNEL_ID)
        message = await channel.fetch_message(MESSAGE_ID)
        for emoji in CHANNEL_BUCKETS.keys():
            await message.add_reaction(emoji)


def setup(bot):
    bot.add_cog(_Booking(bot))