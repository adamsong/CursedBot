from discord.ext import commands
from discord.ext.commands import Cog

weapon_help = """
Weapons
The bot will now keep track of players weapons separately, and as such they must be registered with the bot
 - &weapon new [name] [to-hit] [damage] - creates a new weapon with given to hit bonus and given damage bonus
 - &weapon new [name] magic - creates a new magical weapon (not dealing with magic)
"""
effect_help = """
Effect Commands
 - &effect [weapon] - attempts to re-use effect
 - &effect new [weapon] - rolls a new effect
 - &effect learn [user] [weapon] - flags the effect as known by the player (DM Only)
 - &effect translate [number] - gives the effect string given by [number]
"""
attack_help = """
Attack
 - &attack - begins the attack dialogue
 - &attack [weapon] - begins the attack dialogue for weapon
 - &attack [weapon] [tmp-hit] [vantage] [tmp-damage] [button?] - skip directly to rolling the attack
"""
schedule_help = """
Schedule
 - &schedule [time] - Sends a message with a tentative schedule for group availability feedback
"""
class Help(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def help(self, ctx):
        if ctx.invoked_subcommand is None:
            help_text = "```"
            help_text += weapon_help
            help_text += effect_help
            help_text += attack_help
            help_text += schedule_help
            help_text += "```"
            await ctx.send(help_text)

    @help.command(pass_context=True)
    async def weapons(self, ctx):
        help_text = "```"
        help_text += weapon_help
        help_text += "```"
        await ctx.send(help_text)

    @help.command(pass_context=True)
    async def effect(self, ctx):
        help_text = "```"
        help_text += effect_help
        help_text += "```"
        await ctx.send(help_text)

    @help.command(pass_context=True)
    async def attack(self, ctx):
        help_text = "```"
        help_text += attack_help
        help_text += "```"
        await ctx.send(help_text)

    @help.command(pass_context=True)
    async def schedule(self, ctx):
        help_text = "```"
        help_text += schedule_help
        help_text += "```"
        await ctx.send(help_text)


def setup(bot):
    bot.add_cog(Help(bot))