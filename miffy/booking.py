from discord.utils import get
from datetime import datetime, timezone, timedelta
import asyncio

# Kuala Lumpur, Malaysia GMT+8
TZINFO = timezone(timedelta(hour = 8))

async def sleep_until(dt, tzinfo = TZINFO):
    delta = max(0.0, (dt - datetime.now(tzinfo)).total_seconds())
    if delta > 0.0:
        await asyncio.sleep(delta)

class TimeInterval:

    def __init__(self, start, duration, *, tzinfo = TZINFO):
        try:
            dt = datetime.strptime('')
            self.start = datetime.now(tzinfo).replace(hour=dt.hour, minute=dt.minute)
        except ValueError:
            raise 

        if self.start is None:
            raise ValueError

        self.duration = timedelta(minute=duration)
        self.end = self.start + self.duration

    async def wait_until_start(self):
        await sleep_until(self.start)
    
    async def wait_until_end(self):
        await sleep_until(self.end)
 
    def in_future(self):
        return self.start > datetime.now()

    def intersects(self, obj):
        return any((
            self.start < obj.start < self.end, self.start < obj.end < self.end, 
            obj.start < self.start < obj.end, obj.start < self.end < obj.start
        ))

    def __contains__(self, dt):
        return self.start < dt < self.end

class Worker:

    def __init__(self, bot, *, data):
        self.bucket = data.pop('bucket')
        self.period = data.pop('data')
        self.channel = data.pop 
        self._task = bot.loop.create_task

    async def task(self):
        await 

