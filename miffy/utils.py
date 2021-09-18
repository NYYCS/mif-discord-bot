
from datetime import datetime, timezone, timedelta
import random
import string

import asyncio

TZINFO = timezone(timedelta(hours = 8))

def random_hash(k):
    return ''.join(random.sample(string.ascii_letters, k))

def keypad_emoji(num):
    return f'{num}\ufe0f\u20e3'

async def sleep_until(dt, tzinfo = TZINFO):
    delta = max(0.0, (dt - datetime.now(tzinfo)).total_seconds())
    if delta > 0.0:
        await asyncio.sleep(delta)

class Interval:

    def __init__(self, start, end):
        if start > end:
            raise ValueError('end is earlier than the start')

        self.start = start
        self.end = end

        self.duration = self.end - self.start

    async def wait_until_start(self):
        await sleep_until(self.start)
    
    async def wait_until_end(self):
        await sleep_until(self.end)
 
    def in_future(self, *, tzinfo = TZINFO):
        return self.start > datetime.now(tzinfo)

    def intersects(self, obj):
        return any((
            self.start < obj.start < self.end, self.start < obj.end < self.end, 
            obj.start < self.start < obj.end, obj.start < self.end < obj.start
        ))

    def __contains__(self, dt):
        return self.start < dt < self.end
