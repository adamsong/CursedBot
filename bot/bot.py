import logging
import re
import json
import sys
import os
import shutil
import configparser

import discord
from discord.ext import commands
from discord.embeds import EmbedProxy

import table

### BEGIN CONFIG ###
max_rolls = 20
rolls_per_effect = 3

### END CONFIG ###


logging.basicConfig(level=logging.INFO)

if not os.path.isfile("bot/config-default.ini") and not os.path.isfile("config/config.ini"):
	logging.error("Cannot find config default or an active config, please refer to the documentation for the config file.")
	logging.error(f"Current working directory {os.getcwd()}")
	sys.exit(1)

if not os.path.isfile("config/config.ini"):
	logging.info(f"Cannot find config file at { os.path.abspath('config/config.ini') }, copying default")
	try:
		shutil.copyfile("bot/config-default.ini", "config/config.ini")
	except IOError as e:
		logging.error("Unable to create config:")
		logging.error(f"{e}")
		sys.exit(1)

config = configparser.ConfigParser()
config.read('config/config.ini')

bot = commands.Bot(command_prefix="&")
bot.owner_id = int(config['bot-data']['owner'])

users = {}

attack_stage = 0
attacker = 0
effects_to_roll = 0

@bot.event
async def on_reaction_add(reaction, user):
	print(reaction.emoji)
	if(reaction.message.content == "" and len(reaction.message.embeds) == 1):
		embed = reaction.message.embeds[0]
		if(embed.title == "DND Schedule Poll"):
			for i in range(0, len(embed.fields)):
				if(embed.fields[i].name.startswith(reaction.emoji)):
					field = embed.fields[i]
					embed.set_field_at(i, name=field.name, value=f"{reaction.count - 1} Responses", inline=field.inline)

			await reaction.message.edit(embed=embed)

@bot.event
async def on_reaction_remove(reaction, user):
	print(reaction.emoji)
	if(reaction.message.content == "" and len(reaction.message.embeds) == 1):
		embed = reaction.message.embeds[0]
		if(embed.title == "DND Schedule Poll"):
			for i in range(0, len(embed.fields)):
				if(embed.fields[i].name.startswith(reaction.emoji)):
					field = embed.fields[i]
					embed.set_field_at(i, name=field.name, value=f"{reaction.count - 1} Responses", inline=field.inline)

			await reaction.message.edit(embed=embed)

@bot.event
async def on_message(message):
	if(message.author.id != bot.user.id):
		if(attack_stage != 0 and message.author.id == 279722369260453888 and message.channel.id != 668362659611148299):
			await on_roll(message)
		await bot.process_commands(message)

async def on_roll(message):
	global attack_stage, effects_to_roll
	roll_result = int(message.content.split("\n")[1][2:])
	if(attack_stage == 1 and roll_result <= users[attacker]):
		print("Failed")
		effects_to_roll = max((users[attacker] // rolls_per_effect) + 1, 1)
		await message.channel.send("!1d20000")
		attack_stage = 2
	elif attack_stage == 2:
		attacker_user = message.guild.get_member(attacker)
		log_channel = message.guild.get_channel(668362659611148299)
		effect_str = table.get_table(roll_result)
		await log_channel.send(attacker_user.nick + " rolled effect " + str(roll_result) + ": " + effect_str)
		dice = re.findall("\\d*d\\d+\\+?\\d*", effect_str)
		for die in dice:
			await log_channel.send("!" + die)
		effects_to_roll -= 1
		if effects_to_roll > 0:
			await message.channel.send("!1d20000")
		else:
			attack_stage = 0
			users[attacker] = 0
	else:
		attack_stage = 0

@bot.command()
async def schedule(ctx, *times):
	if len(times) == 1:
		embed=discord.Embed(title="DND Schedule Poll", description=f"Hello @everyone, \nThe tenative time for the next meeting is on {times[0]}. Please react to this message with the emoji signifying your attendance to this session.", color=0xff0000)
		embed.add_field(name="✅ - Available", value="0 Responses", inline=False)
		embed.add_field(name="❌ - Unavailable", value="0 Responses", inline=False)
		message = await ctx.send(embed=embed)
		await message.add_reaction("✅")
		await message.add_reaction("❌")

@bot.group(pass_context=True)
async def attack(ctx):
	global attack_stage, attacker
	if ctx.invoked_subcommand is None:
		if not ctx.author.id in users:
			users[ctx.author.id] = 0
		users[ctx.author.id] += 1
		await ctx.send("Re-using effect, dc is " + str(users[ctx.author.id]))
		await ctx.send("!1d" + str(max_rolls))
		attack_stage = 1
		attacker = ctx.author.id

@attack.command(pass_context=True)
async def new(ctx):
	global attack_stage, attacker, effects_to_roll
	attack_stage = 2
	attacker = ctx.author.id
	effects_to_roll = 1
	await ctx.send("!1d20000")

@attack.command(pass_context=True)
async def check(ctx):
	if not ctx.author.id in users:
		users[ctx.author.id] = 0
	await ctx.send("You have used your current effect " + str(users[ctx.author.id]) + " time(s)")

@attack.command(pass_context=True)
async def set(ctx, value):
	value = int(value)
	users[ctx.author.id] = value
	await ctx.send("Updated to " + str(users[ctx.author.id]))

@attack.command(pass_context=True)
async def dump(ctx):
	log_channel = ctx.guild.get_channel(668362659611148299)
	await log_channel.send(json.dumps(users, separators=(',',':')))

@attack.command(pass_context=True)
async def load(ctx, *, data):
	global users
	loaded_users = json.loads(data)
	users = {int(x): loaded_users[x] for x in loaded_users}
	await ctx.send("Loaded data")


bot.run(config['bot-data']['api_key'])