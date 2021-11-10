from discord import member
from discord.ext import commands, menus, tasks
from typing import Optional
from datetime import datetime, timedelta, tzinfo
 
from .utils.paginator import SimplePaginator
from .utils.time import TZINFO, Period
from .utils import time

import discord
import math


class StudyError(commands.CheckFailure):
    pass

def nick_or_name(member):
    return member.nick if member.nick is not None else member.name

def to_round(x):
    return int(round(x))

def to_minutes(delta):
    if isinstance(delta, timedelta):
        delta = delta.total_seconds()

    return to_round(delta // 60)

def to_hours_minutes(delta):
    if isinstance(delta, timedelta):
        delta = delta.total_seconds()
    
    return to_round(delta // 60), to_round(delta % 60)

def to_readable_time(delta):
    hours, minutes = to_hours_minutes(delta)
    return f'{hours}小时{minutes:02}分钟'

def get_next_reset():
    now = datetime.now(time.TZINFO)
    next_reset = now + timedelta(days = 1 - now.weekday())
    next_reset.replace(hour=4, minute=0, second=0)
    if next_reset <= now:
        next_reset += timedelta(days=7)
    return next_reset

class StudySession:

    def __init__(self, ctx, period):
        self.bot = ctx.bot
        self.cog = ctx.cog
        self.member = ctx.author
        self.channel = ctx.channel
        self.period = period
        self._task = None

    @property
    def duration(self):
        return self.period.duration

    def time_elapsed(self):
        return time.dtnow() - self.period.start

    def time_remaining(self):
        return self.period.end - time.dtnow()

    async def _update_time(self):

        query = '''INSERT INTO users (id, name, weekly, total) 
                   VALUES ($1, $2, $3, $3) ON CONFLICT (id)
                   DO UPDATE SET
                        name = $2,
                        weekly = users.weekly + $3, 
                        total = users.total + $3
                '''
        async with self.bot.pool.acquire() as con:
            await con.execute(query, self.member.id, nick_or_name(self.member), to_minutes(self.time_elapsed()))

    async def _internal_task(self):
        await self.period.wait_until_end()
        await self.end()

    async def start(self):
        self._task = self.bot.loop.create_task(self._internal_task())

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f'{nick_or_name(self.member)}开始学习了！真棒！'
        embed.description = f'这次学习时长为`{to_minutes(self.duration)}分钟`！加油！'

        await self.channel.send(self.member.mention, embed=embed)

    async def end(self):

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = f'{nick_or_name(self.member)}完成学习了！休息一会吧~'
        embed.description = f'你已经完成了`{to_minutes(self.time_elapsed())}`分钟的学习！'

        await self._update_time()
        self.cog.sessions.pop(self.member)

        await self.channel.send(self.member.mention, embed=embed)

        self._task.cancel()
    

class StudyLeaderboardSource(menus.PageSource):

    def __init__(self, bot):
        self.bot = bot
        self._entries = []

    async def prepare(self):
        query = 'SELECT name, weekly, RANK() OVER ( ORDER BY weekly DESC ) FROM users WHERE weekly > 0'
        async with self.bot.pool.acquire() as con:
            self._entries = await con.fetch(query)

    async def get_page(self, page_number):
        if page_number > self.get_max_pages() or page_number < 0:
            raise ValueError('Invalid page number.')
        return self._entries[(page_number - 1) * 10: min(page_number * 10, len(self._entries))]
    
    def get_max_pages(self):
        return math.ceil(len(self._entries) / 10)
    
    def format_page(self, menu, page):
        lines = ['```']
        fmt = '#{rank:<2} {name} - {time}'

        for line in page:
            hours, minutes = to_hours_minutes(line['weekly'])
            line = fmt.format(
                rank=line['rank'],
                name=line['name'],
                time=f'{hours}小时{minutes:02}分钟'
            )
            lines.append(line)
        
        lines.append('```')

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = '这星期的排名'
        embed.description = '\n'.join(lines)

        return embed


MAX_STUDY_SESSION_MINUTES = 24 * 60


class Study(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.sessions = {}
        self.reset_loop.start()

    @tasks.loop(hours=1)
    async def reset_loop(self):
        while True:
            next_reset = get_next_reset()
            await time.sleep_until(next_reset)
            async with self.bot.pool.acquire() as con:
                query = '''WITH lookup AS (
                            SELECT id, RANK() OVER ( ORDER BY weekly DESC ) rank
                            FROM users
                            WHERE weekly > 0
                           ) 
                           SELECT id FROM lookup WHERE rank = 1;
                        '''
                member_id = await con.fetchval(query)
                await con.execute('UPDATE users SET weekly = 0')
                await con.execute('UPDATE users SET king = CASE WHEN id = $1 THEN TRUE ELSE FALSE END', member_id)


    @commands.group(invoke_without_command=True)
    async def pom(self, ctx, minutes: int):
        if ctx.author in self.sessions:
            session = self.sessions[ctx.author]
            raise StudyError(f'{nick_or_name(ctx.author)}, 您目前已经有了学习任务！还剩`{to_minutes(session.time_remaining())}分钟`！')
        if minutes > MAX_STUDY_SESSION_MINUTES:
            raise StudyError('你还ok吗.')
        if minutes < 0:
            async with self.bot.pool.acquire() as con:
                query = '''UPDATE users SET weekly = weekly + $1 WHERE id = $2'''
                await con.execute(query, minutes, ctx.author.id)
            raise StudyError(f'扣了{minutes}，爽了吗')
        
        period = Period.from_duration(minutes=minutes)
        self.sessions[ctx.author] = session = StudySession(ctx, period)
        await session.start()

    @pom.command(aliases=['stop'])
    async def end(self, ctx):
        if ctx.author not in self.sessions:
            raise StudyError(f'{nick_or_name(ctx.author)}, 您目前没有学习任务，现在马上开始学习吧！')
        session = self.sessions[ctx.author]
        await session.end()

    @pom.command()
    async def status(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            member = ctx.author
        if member not in self.sessions:
            raise StudyError(f'{nick_or_name(member)}, 您目前没有学习任务，现在马上开始学习吧！')
        session = self.sessions[member]

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = '任务进度'
        embed.description = f'你正在学习任务中，这次任务还有`{to_minutes(session.time_remaining())}分钟`就完成了，别放弃！'

        await ctx.send(embed=embed)

    @pom.command()
    @commands.is_owner()
    async def save(self, ctx):
        for session in self.sessions.copy().values():
            await session.end()

    @pom.command()
    async def rank(self, ctx, member: Optional[discord.Member] = None):
        if member is None:
            member = ctx.author
            
        query = '''WITH ranked AS (
                        SELECT *, RANK() OVER ( ORDER BY weekly DESC ) rank
                        FROM users
                        WHERE weekly > 0
                   )
                   SELECT * FROM ranked
                   WHERE id = $1
                '''

        async with self.bot.pool.acquire() as con:
            member = await con.fetchrow(query, member.id)

        if member is None:
            raise StudyError('你这星期还没完成学习任务，现在马上开始学习吧！')

        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = '这星期排名'
        embed.description = f'**第{member["rank"]}名 {member["name"]}**\n'     \
                            f'这星期总学习时间: `{to_readable_time(member["weekly"])}`\n'   \
                            f'整体总学习时间: `{to_readable_time(member["total"])}`'
        
        await ctx.send(embed=embed)

    @pom.command()
    async def who(self, ctx):
        if self.sessions:
            who = ', '.join([f'`{nick_or_name(member)}`' for member in self.sessions.keys()])
            await ctx.send(embed=discord.Embed(title='正在学习的小伙伴', description=f'{who}正在学习中~！', color=discord.Color.blurple()))
        else:
            await ctx.send(embed=discord.Embed(title='目前没有人拥有学习任务', description='现在马上开始学习吧！', color=discord.Color.blurple()))

    @pom.command()
    async def leaderboard(self, ctx, page: int = 1):
        source = StudyLeaderboardSource(self.bot)
        paginator = SimplePaginator(ctx, source, page=page)
        await paginator.start()


def setup(bot):
    bot.add_cog(Study(bot))