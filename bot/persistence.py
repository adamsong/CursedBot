import json

from discord.ext import commands
from discord.ext.commands import Cog

from bot.user_data import UserList


class Persistence(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def dump(self, ctx):
        log_channel = ctx.guild.get_channel(668362659611148299)
        await log_channel.send(json.dumps(UserList.serialize_all(), separators=(',', ':')))

    @commands.command(pass_context=True)
    async def load(self, ctx, *, data):
        loaded_data = json.loads(data)
        UserList.deserialize_all(loaded_data)
        await ctx.send("Loaded data")


def setup(bot):
    bot.add_cog(Persistence(bot))
