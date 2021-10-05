from datetime import (
    datetime, 
    timedelta, 
    timezone
)
import asyncio

TZINFO = timezone(timedelta(hours = 8))


def dtnow(tzinfo=TZINFO):
    return datetime.now(tzinfo)


async def sleep_until(dt):
    delta = max(0.0, (dt - dtnow()).total_seconds())
    if delta > 0.0:
        await asyncio.sleep(delta)

class Period:

    def __init__(self, start, end):
        if end < start:
            raise ValueError('The end is earlier than the start.')
        self.start = start
        self.end = end
        self.duration = end - start

    async def wait_until_start(self):
        await sleep_until(self.start)

    async def wait_until_end(self):
        await sleep_until(self.end)

    def in_future(self):
        return dtnow() < self.start

    def intersects(self, period):
        return any((
            self.start < period.start < self.end, self.start < period.end < self.end, 
            period.start < self.start < period.end, period.start < self.end < period.start
        ))
        
    @classmethod
    def from_duration(cls, *, start = None, **duration):
        self = cls.__new__(cls)
        self.start = start
        if start is None:
            self.start = dtnow()
        self.end = self.start  + timedelta(**duration)
        self.duration = self.end - self.start

        return self

        
    
