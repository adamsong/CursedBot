import discord
from discord.ext import commands
from discord.ext.commands import Cog
from .bot import testing


class Schedule(Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyUnusedLocal
    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        await Schedule.on_reaction(reaction)

    # noinspection PyUnusedLocal
    @Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        await Schedule.on_reaction(reaction)

    @staticmethod
    async def on_reaction(reaction):
        if reaction.message.content == "" and len(reaction.message.embeds) == 1:
            embed = reaction.message.embeds[0]
            if embed.title == "DND Schedule Poll":
                emoji = reaction.emoji if type(reaction.emoji) is str \
                    else f"<:{reaction.emoji.name}:{reaction.emoji.id}>"
                for i in range(0, len(embed.fields)):
                    if embed.fields[i].name.startswith(emoji):
                        field = embed.fields[i]
                        embed.set_field_at(i, name=field.name, value=f"{reaction.count - 1} Responses",
                                           inline=field.inline)

                await reaction.message.edit(embed=embed)

    @commands.command()
    async def schedule(self, ctx, *times):
        if len(times) == 1:
            mention = "@everyone" if not testing else "@all"
            embed = discord.Embed(title="DND Schedule Poll",
                                  description=f"Hello {mention}, \nThe tentative time for the next meeting is on"
                                              f" {times[0]}. Please react to this message with the emoji signifying \
                                              your attendance to this session.",
                                  color=0xff0000)
            embed.add_field(name="<:AAA:699603393605271562> - Available", value="0 Responses", inline=False)
            embed.add_field(name="<:MMM:699603435879923782> - Unavailable", value="0 Responses", inline=False)
            message = await ctx.send(embed=embed)
            await message.add_reaction("<:AAA:699603393605271562>")
            await message.add_reaction("<:MMM:699603435879923782>")


def setup(bot):
    bot.add_cog(Schedule(bot))