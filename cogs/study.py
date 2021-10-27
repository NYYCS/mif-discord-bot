from discord.ext import commands
import discord

from datetime import datetime, timedelta
from typing import Optional

from miffy import utils

class StudySession:

    def __init__(self, ctx, duration):
        self.bot = ctx.bot
        self.cog = ctx.command.cog
        self.channel = ctx.channel
        self.user = ctx.author
        self.duration = duration
        if duration < 10:
            raise RuntimeError('请至少学习10分钟以上！不然人家懒得理你啦~')
        start = datetime.now(utils.TZINFO)
        end = start + timedelta(minutes=duration)
        self._interval = utils.Interval(start, end)
        self._task = None
        self._running = False

    @property
    def time_elapsed(self):
        return utils.to_round((datetime.now(utils.TZINFO) - self._interval.start).total_seconds() // 60)
    
    @property
    def time_left(self):
        return utils.to_round((self._interval.end - datetime.now(utils.TZINFO)).total_seconds() // 60)

    async def start(self):
        if not self._running: 
            await self.bot.send(self.channel, content=self.user.mention, title=f'{self.user.nick}开始学习了！真棒！', description=f'这次学习时长为{self.duration}分钟！加油！')
        self._task = self.bot.loop.create_task(self.task())
        self.running = True
    
    async def stop(self):
        elapsed = self.time_elapsed
        await self.bot.send(self.channel, content=self.user.mention, title=f'{self.user.nick}完成学习了！休息一会吧~', description=f'你已经完成了{elapsed}分钟的学习！')
        async with self.bot.pool.acquire() as conn:
            await conn.execute('INSERT INTO users (id, name) VALUES ($1, $2) ON CONFLICT DO NOTHING', self.user.id, self.user.nick)
            await conn.execute('UPDATE users SET time = time + $1 WHERE id = $2', elapsed, self.user.id)
        
        self.cog._sessions.pop(self.user)
        self._task.cancel()

    async def task(self):
        await self._interval.wait_until_end()
        await self.stop()

class Study(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._sessions = {}
    
    @commands.group(invoke_without_command=True)
    async def pom(self, ctx, *, minutes: int): 
        if ctx.author in self._sessions:
            session = self._sessions[ctx.author]
            raise RuntimeError(f'您目前已经有了学习任务！还剩{session.time_left}分钟！')
        
        session = StudySession(ctx, minutes)
        self._sessions[ctx.author] = session
        await session.start()

    @pom.command(aliases=['end'], name='stop')
    async def end_command(self, ctx):
        if ctx.author not in self._sessions:
            raise RuntimeError(f'{ctx.author.nick}，您目前没有学习任务，现在马上开始学习吧！')

        session = self._sessions[ctx.author]
        await session.stop()

    @commands.command(name='rank')
    async def rank_command(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            member = ctx.author

        async with self.bot.pool.acquire() as conn:
            query = '''
                SELECT rank, time FROM (
                    SELECT 
                        RANK() OVER ( ORDER BY time DESC ) as rank,
                        id, 
                        time
                    FROM users
                ) AS ranked WHERE id = $1;
            '''

            rank, time = await conn.fetchrow(query, member.id)
        
        await self.bot.send(ctx, title='排名', description=f'{member.nick}: **第{rank}名**\n总时间: `{utils.format_timedelta(timedelta(minutes=time))}`')

    @commands.command(name='leaderboard')
    async def leaderboard_command(self, ctx, page: int = 1):
        async with self.bot.pool.acquire() as conn:
            query = '''
                SELECT * FROM (
                    SELECT 
                        RANK() OVER ( ORDER BY time DESC ) as rank,
                        name,
                        time
                    FROM users
                ) AS ranked LIMIT 10 OFFSET $1;
            '''
            rows = await conn.fetch(query, (page - 1) * 10)

        description = '\n'.join([
            '**#{0}** {1}: `{2}` '.format(rank, name, utils.format_timedelta(timedelta(minutes=time)))
            for rank, name, time in rows
        ])

        await self.bot.send(ctx, title='排名', description=description)

    @commands.command(name='in_study')
    async def in_study_command(self, ctx):
        await self.bot.send(ctx, title='正在学习的小伙伴', description='{0} 正在学习中~~'.format(' '.join(f'`{user.nick}`' for user in self._sessions.keys())))

    @commands.command(name='status')
    async def status_command(self, ctx):
        if ctx.author not in self._sessions:
            raise RuntimeError(f'{ctx.author.nick}，您目前没有学习任务，现在马上开始学习吧！')
        
        session = self._sessions[ctx.author]

        await self.bot.send(ctx, title='任务进度', description=f'你正在学习任务中，这次任务还有{session.time_left}分钟就完成了，别放弃！')

def setup(bot):
    bot.add_cog(Study(bot))