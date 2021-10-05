from discord.ext import commands


def tabulate(rows):
    lines = ['```']
    lines.append(' '.join([f'{name}' for name in rows[0].keys()]))
    for row in rows[:10]:
        lines.append(' '.join([f'{value:>10}' if value else ' ' * 10 for value in row.values()]))
    lines.append('```')

    return '\n'.join(lines)

class SQL(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    @commands.is_owner()
    async def sql(self, ctx):
        pass

    @sql.command()
    async def execute(self, ctx, *, query):
        async with self.bot.pool.acquire() as con:
           status = await con.execute(query)
        await ctx.send('```\n' + status + '\n```')

    @sql.command()
    async def fetch(self, ctx, *, query):
        async with self.bot.pool.acquire() as con:
            rows = await con.fetch(query)
        await ctx.send(tabulate(rows))


def setup(bot):
    bot.add_cog(SQL(bot))
