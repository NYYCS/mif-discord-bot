from discord.ext import commands
import discord

from datetime import datetime, timedelta
from typing import Optional

from discord.ext.commands import bot

from miffy.utils import Interval, TZINFO


class StudySession:

    def __init__(self, ctx, duration):
        self.bot = ctx.bot
        self.channel = ctx.channel
        self.user = ctx.author
        if duration < 10:
            raise ValueError('请至少学习10分钟以上！不然人家懒得理你啦~')
        self.duration = duration
        start = datetime.now(TZINFO)
        end = start + timedelta(minutes=duration)
        self._interval = Interval(start, end)
        self._task = None
        self._running = False

    @property
    def time_elapsed(self):
        return datetime.now(TZINFO) - self.start
    
    @property
    def time_left(self):
        return self.end - datetime.now(TZINFO)

    async def start(self):
        if not self.running: 
            await self.bot.send(self.channel, title=f'{self.user.nick}开始学习了！真棒！', description=f'这次学习时长为{self.duration}分钟！加油！')

        self._task = self.bot.loop.create_task(self.task())
        self.running = True

        return self._task
    
    async def stop(self):
        if not self._task.done():
            self._task.cancel()

        elapsed = self.time_elapsed
        await self.bot.send(self.channel, title=f'{self.user.nick}完成学习了！休息一会吧~', description=f'你已经完成了{elapsed}分钟的学习！')
        async with self.bot.pool.acquire() as conn:
            await conn.execute('UPDATE users SET time = time + $1 WHERE id = $2', elapsed, self.user.id)

    async def task(self):
        await self._interval.wait_until_end()
        await self.stop()

class Study(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._sessions = {}

    @commands.command(name='pom')
    async def pom_command(self, ctx, minutes: int):
        if ctx.author in self._sessions:
            raise
        
        session = StudySession(ctx, minutes)
        self._sessions[ctx.author] = session
        session.start()

    @commands.command(name='stop')
    async def stop_command(self, ctx):
        if ctx.author not in self._sessions:
            raise

        session = self._sessions[ctx.author]
        await session.stop()

    @commands.command(name='rank')
    async def rank_command(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            member = ctx.author

        async with self.bot.pool.acquire() as conn:
            rank = await conn.fetchval('SELECT RANK() OVER ( ORDER BY time ) rank FROM users WHERE id = $1', member.id)
        
        await self.bot.send(ctx, title='排名', description=f'{member.nick}: 第{rank}名"')

    @commands.command(name='leaderboard')
    async def leaderboard_command(self, ctx, page: int = 1):
        async with self.bot.pool.acquire() as conn:
            rows = await conn.fetch('SELECT name, RANK() OVER ( ORDER BY time ) rank FROM user LIMIT 10 OFFSET $1' , (page - 1) * 10)

        description = '\n'.join([
            '{0}: {1.hours}小时 {1.minutes}分钟 '.format(row['name'], timedelta(minutes=row['time']))
            for row in rows
        ])

        await self.bot.send(ctx, title='排名', description=description)

    @commands.command(name='in_study')
    async def in_study_command(self, ctx):
        await self.bot.send(ctx, title='正在学习的小伙伴', description='{0} 正在学习中~~'.format(' '.join(user.nick for user in self._sessions.keys())))

    @commands.command(name='status')
    async def status_command(self, ctx):
        if ctx.author not in self._sessions:
            raise
        
        session = self._sessions[ctx.author]

        await self.bot.send(title='任务进度', description=f'你正在学习任务中，这次任务还有{session.time_left.minutes}分钟就完成了，别放弃！')