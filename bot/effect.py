import discord
from discord.ext import commands
from discord.ext.commands import Cog

from bot import table
from bot.user_data import UserList, CurrentAttack, EAttackStage, AttackStage


class Effect(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True, invoke_without_command=True)
    async def effect(self, ctx, weapon_name=""):
        await Effect.do_effects(ctx, weapon_name, EAttackStage.CHECK_CASCADE)

    @effect.command(pass_context=True)
    async def new(self, ctx, weapon_name=""):
        await Effect.do_effects(ctx, weapon_name, EAttackStage.ROLL_EFFECT)

    @staticmethod
    async def do_effects(ctx, weapon_name, stage):
        user_list = UserList.get_list_for(ctx.guild.id)
        user = user_list.get_user(ctx.author.id)
        weapon = user.get_weapon(weapon_name)
        if weapon_name == "":
            await ctx.send("Please provide the weapon name")
        elif len(user.get_weapons()) == 0:
            await ctx.send("Please add at least one weapon to your user")
        elif weapon is None:
            await ctx.send("Invalid weapon name")
        else:
            current_attack = CurrentAttack.get_current_attack_for(ctx.guild.id)
            current_attack.attacker = ctx.author.id
            current_attack.weapon = weapon
            current_attack.weapon_name = weapon_name
            current_attack.full_attack = False
            current_attack.stage = stage
            await AttackStage.get_stage(current_attack.stage).prompt(ctx.message, current_attack, user)

    @effect.command(pass_context=True)
    async def translate(self, ctx, effect_id: int):
        effect_str = table.get_table(effect_id)
        await ctx.send("Effect " + str(effect_id) + ": " + effect_str)

    @effect.command(pass_context=True)
    async def learn(self, ctx, member: discord.Member, weapon_name):
        user_list = UserList.get_list_for(ctx.guild.id)
        user = user_list.get_user(member.id)
        weapon = user.get_weapon(weapon_name)
        if weapon_name == "":
            await ctx.send("Please provide the weapon name")
        elif len(user.get_weapons()) == 0:
            await ctx.send("Please add at least one weapon to your user")
        elif weapon is None:
            await ctx.send("Invalid weapon name")
        else:
            weapon.player_known = True
            await ctx.send(f"The effect was: {table.get_table(weapon.current_effect)}")


def setup(bot):
    bot.add_cog(Effect(bot))
