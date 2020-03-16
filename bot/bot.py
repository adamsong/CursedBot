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
current_attack = {}
effects_to_roll = 0
attack_stage = 0

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

@bot.command()
async def schedule(ctx, *times):
	if len(times) == 1:
		embed=discord.Embed(title="DND Schedule Poll", description=f"Hello @everyone, \nThe tenative time for the next meeting is on {times[0]}. Please react to this message with the emoji signifying your attendance to this session.", color=0xff0000)
		embed.add_field(name="✅ - Available", value="0 Responses", inline=False)
		embed.add_field(name="❌ - Unavailable", value="0 Responses", inline=False)
		message = await ctx.send(embed=embed)
		await message.add_reaction("✅")
		await message.add_reaction("❌")

@bot.event
async def on_message(message):
	if(message.author.id != bot.user.id):
		if attack_stage != 0 and message.channel.id != 668362659611148299:
			await on_attack(message)
		await bot.process_commands(message)

async def on_attack(message):
	global attack_stage, current_attack, users

	if message.content == "cancel":
		current_attack = {}
		attack_stage = 0
		return

	if attack_stage == 1 and current_attack["attacker"] == message.author.id:
		weapon_name = message.content
		if weapon_name in users[current_attack["attacker"]]["weapons"]:
			current_attack["weapon"] = users[current_attack["attacker"]]["weapons"][weapon_name]
			current_attack["weapon"]["name"] = weapon_name
			if current_attack["weapon"]["weapon-type"] == "mundane":
				await message.channel.send("What is your temporary hit modifier?")
				attack_stage = 2
			else:
				await message.channel.send("Do you press the button?")
				attack_stage = 101
		else:
			await message.channel.send("Please enter a valid weapon")
	elif attack_stage == 2 and current_attack["attacker"] == message.author.id:
		current_attack["tmp-hit"] = message.content
		attack_stage = 3
		await message.channel.send("Do you have advantage or disadvantage?")
	elif attack_stage == 3 and current_attack["attacker"] == message.author.id:
		if message.content in ["advantage", "disadvantage", "no"]:
			current_attack["advantage"] = message.content
			attack_stage = 4
			await message.channel.send("What is your temporary damage modifier?")
		else:
			await message.channel.send("Please respond with `advantage`, `disadvantage`, or `no`")
	elif attack_stage == 4 and current_attack["attacker"] == message.author.id:
		current_attack["tmp-damage"] = message.content
		attack_stage = 5
		await message.channel.send("Do you press the button?")
	elif attack_stage == 5 and current_attack["attacker"] == message.author.id:
		if message.content in ["yes", "no"]:
			current_attack["button"] = message.content
			attack_stage = 6
			dice = f"{'d20' if current_attack['advantage'] == 'no' else ('2d20' + ('k1' if current_attack['advantage'] == 'advantage' else 'kl1'))}"
			await message.channel.send(f"!{dice}+{current_attack['weapon']['to-hit']}+{current_attack['tmp-hit']}")
		else:
			await message.channel.send("Please respond with `yes` or `no`")
	elif attack_stage == 7:
		if message.content in ["yes", "no"]:
			current_attack["hit"] = message.content
			if message.content == "yes":
				if not "uses" in users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]:
					users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["uses"] = 0
				users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["uses"] += 1

				attack_stage = 8
				await message.channel.send(f"!{current_attack['weapon']['damage']}+{current_attack['tmp-damage']}")
			else:
				await message.channel.send(make_summary())
				attack_stage = 0
				current_attack = {}
		else:
			await message.channel.send("Please respond with `yes` or `no`")
	elif attack_stage == 101 and current_attack["attacker"] == message.author.id:
		if message.content in ["yes", "no"]:
			current_attack["button"] = message.content
			if current_attack["button"] == "yes":
				attack_stage = 202
				effects_to_roll = 1
				await message.channel.send("!1d20000")
			else:
				attack_stage = 201
				users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses'] += 1
				await message.channel.send(f"Checking for cascade, DC is {users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses']}")
				await message.channel.send("!d20")
		else:
			await message.channel.send("Please respond with `yes` or `no`")
	elif attack_stage in [6, 8, 201, 202] and message.author.id == 279722369260453888:
		await on_attack_roll(message)

async def on_attack_roll(message):
	global attack_stage, effects_to_roll, current_attack, users
	roll_result = int(message.content.split("\n")[1][2:])

	if attack_stage == 6:
		current_attack["attack-roll"] = roll_result
		attack_stage = 7
		await message.channel.send(f"Does a {roll_result} hit?")
	elif attack_stage == 8:
		current_attack["damage-roll"] = roll_result
		if current_attack["button"] == "yes":
			attack_stage = 202
			effects_to_roll = 1
			await message.channel.send("!1d20000")
		else:
			attack_stage = 201
			await message.channel.send(f"Checking for cascade, DC is {users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses']}")
			await message.channel.send("!d20")
	elif attack_stage == 201:
		if roll_result <= users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["uses"]:
			print("Failed")
			effects_to_roll = max((users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["uses"] // rolls_per_effect) + 1, 1)
			await message.channel.send("!1d20000")
			attack_stage = 202
		else:
			effect_num = users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["current-effect"]
			attacker_user = message.guild.get_member(current_attack["attacker"])
			log_channel = message.guild.get_channel(668362659611148299)
			effect_str = table.get_table(effect_num)
			await log_channel.send(attacker_user.display_name + " re-used effect " + str(effect_num) + ": " + effect_str)
			dice = re.findall("\\d*d\\d+\\+?\\d*", effect_str)
			for die in dice:
				await log_channel.send("!" + die)
			
			await message.channel.send(make_summary())
			attack_stage = 0
			current_attack = {}

	elif attack_stage == 202:
		attacker_user = message.guild.get_member(current_attack["attacker"])
		log_channel = message.guild.get_channel(668362659611148299)
		effect_str = table.get_table(roll_result)
		await log_channel.send(attacker_user.display_name + " rolled effect " + str(roll_result) + ": " + effect_str)
		dice = re.findall("\\d*d\\d+\\+?\\d*", effect_str)
		for die in dice:
			await log_channel.send("!" + die)
		
		users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["current-effect"] = roll_result
		users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["player-known"] = "false"

		effects_to_roll -= 1
		if effects_to_roll > 0:
			await message.channel.send("!1d20000")
		else:
			await message.channel.send(make_summary())
			attack_stage = 0
			users[current_attack["attacker"]]["weapons"][current_attack['weapon']['name']]["uses"] = 0
			current_attack = {}
	else:
		attack_stage = 0

def make_summary():
	summary = "Attack Summary\n"
	if current_attack['weapon']['weapon-type'] == "mundane":
		summary += f"Attack {'hit' if current_attack['hit'] == 'yes' else 'missed'} with {current_attack['attack-roll']}\n"
		if current_attack['hit'] == 'yes':
			summary += f"Attack dealt {current_attack['damage-roll']} damage\n"
	if current_attack['weapon']['weapon-type'] == "magic" or current_attack['hit'] == "yes":
		summary += f"The effect was: {'Unknown' if users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['player-known'] == 'false' else table.get_table(int(users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['current-effect']))}\n"
	return summary

@bot.command(pass_context=True)
async def attack(ctx, *args):
	global attack_stage, current_attack, effects_to_roll
	if ctx.invoked_subcommand is None:
		if not ctx.author.id in users or not "weapons" in users[ctx.author.id] or len(users[ctx.author.id]["weapons"]) == 0:
			await ctx.send("Please add at least one weapon to your user")
			return

		if len(args) != 0:
			if args[0] in users[ctx.author.id]["weapons"]:
				current_attack["attacker"] = ctx.author.id
				current_attack["weapon"] = users[current_attack["attacker"]]["weapons"][args[0]]
				current_attack["weapon"]["name"] = args[0]
				if current_attack["weapon"]["weapon-type"] == "mundane":
					if len(args) == 1:
						await ctx.send("What is your temporary hit modifier?")
						attack_stage = 2
					elif len(args) == 5:
						if args[2] in ["advantage", "disadvantage", "no"] and args[4] in ["yes", "no"]:
							current_attack["tmp-hit"] = args[1]
							current_attack["advantage"] = args[2]
							current_attack["tmp-damage"] = args[3]
							current_attack["button"] = args[4]

							attack_stage = 6
							dice = f"{'d20' if current_attack['advantage'] == 'no' else ('2d20' + ('k1' if current_attack['advantage'] == 'advantage' else 'kl1'))}"
							await ctx.send(f"!{dice}+{current_attack['weapon']['to-hit']}+{current_attack['tmp-hit']}")
						else:
							await ctx.send("Invalid arguments")
					else:
						await ctx.send("Invalid number of arguments")

				else:
					if len(args) == 1:
						await ctx.send("Do you press the button?")
						attack_stage = 101
					elif len(args) == 2:
						if args[1] in ["yes", "no"]:
							current_attack["button"] = args[1]

							if current_attack["button"] == "yes":
								attack_stage = 202
								effects_to_roll = 1
								await ctx.send("!1d20000")
							else:
								attack_stage = 201
								users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses'] += 1
								await ctx.send(f"Checking for cascade, DC is {users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses']}")
								await ctx.send("!d20")
						else:
							await ctx.send("Invalid arguments")
					else:
						await ctx.send("Invalid number of arguments")
			else:
				await ctx.send("Weapon not found")
		else:

			await ctx.send(f'With what weapon are you attacking? [{", ".join(users[ctx.author.id]["weapons"].keys())}]')
			attack_stage = 1
			current_attack["attacker"] = ctx.author.id

@bot.group(pass_context=True)
async def weapon(ctx):
	if ctx.invoked_subcommand is None:
		await ctx.send("Please invoke a valid subcommand: `new`, `remove`")

@weapon.command(pass_context=True)
async def new(ctx, *args):
	if (len(args) == 3) or (len(args) == 2 and args[1] == "magic"):
		if not ctx.author.id in users:
			users[ctx.author.id] = {}
		if not "weapons" in users[ctx.author.id]:
			users[ctx.author.id]["weapons"] = {}

		users[ctx.author.id]["weapons"][args[0]] = {}
		users[ctx.author.id]["weapons"][args[0]]["weapon-type"] = "magic" if args[1] == "magic" else "mundane"
		users[ctx.author.id]["weapons"][args[0]]["uses"] = 0
		users[ctx.author.id]["weapons"][args[0]]["player-known"] = "false"
		users[ctx.author.id]["weapons"][args[0]]["current-effect"] = 0
		if args[1] != "magic":
			users[ctx.author.id]["weapons"][args[0]]["to-hit"] = args[1]
			users[ctx.author.id]["weapons"][args[0]]["damage"] = args[2]
			await ctx.send(f"Created weapon {args[0]} with {args[1]} to-hit and {args[2]} damage")
		else:
			await ctx.send(f"Created magical weapon {args[0]}")
	else:
		await ctx.send("Incorrect arguments")

@bot.command(pass_context=True)
async def check(ctx):
	checkstring = "Effect Data:\n```\n"
	if not ctx.author.id in users:
		users[ctx.author.id] = {}
	if not "weapons" in users[ctx.author.id] or len(users[ctx.author.id]["weapons"]) == 0:
		await ctx.send("You have no weapons")
		return
	
	checkstring += "\n".join(f"{weapon:<30}: {users[ctx.author.id]['weapons'][weapon]['uses']}" for weapon in users[ctx.author.id]["weapons"])
	checkstring += "\n```"
	await ctx.send(checkstring)

@bot.command(pass_context=True)
async def dump(ctx):
	log_channel = ctx.guild.get_channel(668362659611148299)
	await log_channel.send(json.dumps(users, separators=(',',':')))

@bot.command(pass_context=True)
async def load(ctx, *, data):
	global users
	loaded_users = json.loads(data)
	users = {int(x): loaded_users[x] for x in loaded_users}
	await ctx.send("Loaded data")

@bot.group(pass_context=True, invoke_without_command=True)
async def effect(ctx, weapon_name=""):
	global attack_stage, current_attack
	if not ctx.invoked_subcommand:
		if weapon_name == "":
			await ctx.send("Please provide the weapon name")
		elif not ctx.author.id in users or not "weapons" in users[ctx.author.id] or len(users[ctx.author.id]["weapons"]) == 0:
			await ctx.send("Please add at least one weapon to your user")
		elif not weapon_name in users[ctx.author.id]['weapons']:
			await ctx.send("Invalid weapon name")
		else:
			current_attack["attacker"] = ctx.author.id
			current_attack['weapon'] = users[ctx.author.id]['weapons'][weapon_name]
			current_attack['weapon']['name'] = weapon_name
			current_attack['weapon']['weapon-type'] = "magic"

			attack_stage = 201
			users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses'] += 1
			await ctx.send(f"Checking for cascade, DC is {users[current_attack['attacker']]['weapons'][current_attack['weapon']['name']]['uses']}")
			await ctx.send("!d20")	

@effect.command(pass_context=True)
async def new(ctx, weapon_name=""):
	global attack_stage, current_attack
	if weapon_name == "":
		await ctx.send("Please provide the weapon name")
	elif not ctx.author.id in users or not "weapons" in users[ctx.author.id] or len(users[ctx.author.id]["weapons"]) == 0:
		await ctx.send("Please add at least one weapon to your user")
	elif not weapon_name in users[ctx.author.id]['weapons']:
		await ctx.send("Invalid weapon name")
	else:
		current_attack["attacker"] = ctx.author.id
		current_attack['weapon'] = users[ctx.author.id]['weapons'][weapon_name]
		current_attack['weapon']['name'] = weapon_name
		current_attack['weapon']['weapon-type'] = "magic"

		attack_stage = 202
		effects_to_roll = 1
		await ctx.send("!1d20000")

@effect.command(pass_context=True)
async def translate(ctx, effect: int):
	effect_str = table.get_table(effect)
	await ctx.send("Effect " + str(effect) + ": " + effect_str)

@effect.command(pass_context=True)
async def learn(ctx, member: discord.Member, weapon_name):
	if not member.id in users or not "weapons" in users[member.id] or len(users[member.id]["weapons"]) == 0:
		await ctx.send("Please add at least one weapon to your user")
	elif not weapon_name in users[member.id]['weapons']:
		await ctx.send("Invalid weapon name")
	else:
		users[member.id]['weapons'][weapon_name]['player-known'] = "true"
		await ctx.send(f"The effect was: {table.get_table(users[member.id]['weapons'][weapon_name]['current-effect'])}")

bot.run(config['bot-data']['api_key'])