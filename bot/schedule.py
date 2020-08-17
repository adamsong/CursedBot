import discord
from discord.ext import commands
from discord.ext.commands import Cog
from .bot import testing


class Schedule(Cog):
    def __init__(self, bot):
        self.bot = bot

    # noinspection PyUnusedLocal
    @Cog.listener()
    async def on_raw_reaction_add(self, payload):

        emoji = str(payload.emoji)
        if emoji == "📡":
            channel = self.bot.get_channel(payload.channel_id)
            channel_message = await channel.fetch_message(payload.message_id)
            if len(channel_message.embeds) == 1:
                embed = channel_message.embeds[0]
                if embed.title == "DND Schedule Poll":
                    guild = channel.guild
                    roles = guild.roles
                    role = next(x for x in roles if x.name == "Generic role #3")
                    players = role.members
                    reacted_players = set()
                    reactions = channel_message.reactions
                    chosen_responses = []
                    chosen_response_count = 0
                    for reaction in reactions:
                        if reaction.count > chosen_response_count:
                            chosen_responses = [str(reaction.emoji)]
                            chosen_response_count = reaction.count
                        elif reaction.count == chosen_response_count:
                            chosen_responses.append(str(reaction.emoji))
                        async for user in reaction.users():
                            reacted_players.add(user)
                    non_responsive = [x for x in players if x not in reacted_players]
                    if len(non_responsive) == 0:
                        mention = "@everyone" if not testing else "@all"
                        disclaimer = "However, there are 2 or more people who cannot make this session, so it will " \
                                     "be a one shot or similar if the session is still held. " if len(players) - 1 > chosen_response_count else ""
                        message = ""
                        if len(chosen_responses) == 1:
                            message = f"Hello, {mention}. The winning vote is {chosen_responses[0]}. "
                        else:
                            message = f"Hello, {mention}. The winning votes are { ', '.join(chosen_responses) }. "
                        message += disclaimer
                        await channel.send(message)
                    else:
                        message = "Please ensure that you have all responded to the scheduling poll. "
                        message = f"There is no response from { ','.join([x.mention if not testing else x.display_name for x in non_responsive]) }"
                        await channel.send(message)
                    await channel_message.clear_reaction("📡")
        else:
            await Schedule.on_reaction(payload, self.bot)

    # noinspection PyUnusedLocal
    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await Schedule.on_reaction(payload, self.bot)

    @staticmethod
    async def on_reaction(payload, bot):
        channel = bot.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if len(message.embeds) == 1:
            embed = message.embeds[0]
            if embed.title == "DND Schedule Poll":
                emoji_str = str(payload.emoji)
                reactions = message.reactions
                count = 0
                for i in range(0, len(reactions)):
                    count = reactions[i].count if str(reactions[i].emoji) == emoji_str else count
                for i in range(0, len(embed.fields)):
                    if embed.fields[i].name.startswith(emoji_str):
                        field = embed.fields[i]
                        embed.set_field_at(i, name=field.name, value=f"{count - 1} Responses",
                                           inline=field.inline)

                await message.edit(embed=embed)

    @commands.command()
    async def schedule(self, ctx, *times):
        mention = "@everyone" if not testing else "@all"
        if len(times) == 1:
            embed = discord.Embed(title="DND Schedule Poll",
                                  description=f"Hello everyone, \nThe tentative time for the next meeting is on"
                                              f" {times[0]}. Please react to this message with the emoji signifying \
                                              your attendance to this session.",
                                  color=0xff0000)
            embed.add_field(name="<:AAA:699603393605271562> - Available", value="0 Responses", inline=False)
            embed.add_field(name="<:MMM:699603435879923782> - Unavailable", value="0 Responses", inline=False)
            message = await ctx.send(mention, mbed=embed)
            await message.add_reaction("<:AAA:699603393605271562>")
            await message.add_reaction("<:MMM:699603435879923782>")
        else:
            schedule_emoji = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "0️⃣"]
            if len(times) > len(schedule_emoji):
                await ctx.send(f"Cannot support more than {len(schedule_emoji)} dates")
            else:
                embed = discord.Embed(title="DND Schedule Poll",
                                      description="Hello everyone, \nThere are multiple possible dates for the next "
                                                  "session, please react to all dates in which you can be available. "
                                                  "Only react no if none of the dates work, not all of the dates will "
                                                  "be used, this is a simple check to see which date is best.",
                                      color=0xff0000)
                for i in range(0, len(times)):
                    embed.add_field(name=f"{schedule_emoji[i]} - { times[i] }", value="0 Responses", inline=False)
                embed.add_field(name="❌ - None of the above", value="0 Responses", inline=False)
                message = await ctx.send(mention, embed=embed)
                for i in range(0, len(times)):
                    await message.add_reaction(schedule_emoji[i])
                await message.add_reaction("❌")


def setup(bot):
    bot.add_cog(Schedule(bot))
