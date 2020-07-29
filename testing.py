import discord
from discord.ext import commands
import logging

logging.basicConfig(level=logging.INFO)
bot = commands.Bot(command_prefix='>')


@bot.command()
async def ping(ctx):
    await ctx.send('pong')


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")

bot.run('NjY5NzgzNzQwNjMyNzkzMTAw.Xik2tw.zkpycQX6JniDSa6XzAxiHj2kKdM')