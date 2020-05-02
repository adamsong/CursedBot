from discord.ext import commands
from discord.ext.commands import Cog

from bot.user_data import UserList, CurrentAttack, EAttackStage, AttackStage, WeaponType, VantageEnum


class Attack(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def attack(self, ctx, *args):
        user_list = UserList.get_list_for(ctx.guild.id)
        user = user_list.get_user(ctx.author.id)
        CurrentAttack.reset_for(ctx.guild.id)
        current_attack = CurrentAttack.get_current_attack_for(ctx.guild.id)
        if len(user.get_weapons()) == 0:
            await ctx.send("Please add at least one weapon to your user")
            return

        if len(args) != 0:
            if args[0] in user.get_weapons():
                current_attack.attacker = ctx.author.id
                current_attack.weapon = user.get_weapon(args[0])
                current_attack.weapon_name = args[0]
                if current_attack.weapon.weapon_type == WeaponType.MUNDANE:
                    if len(args) == 1:
                        current_attack.stage = EAttackStage.TEMP_HIT
                    elif len(args) == 5:
                        if args[2].lower() in ["advantage", "a", "disadvantage", "d", "no", "n"] \
                                and args[4].lower() in ["yes", "y", "no", "n"]:
                            current_attack.tmp_hit = args[1]
                            current_attack.vantage = {
                                "advantage": VantageEnum.ADVANTAGE,
                                "a": VantageEnum.ADVANTAGE,
                                "disadvantage": VantageEnum.DISADVANTAGE,
                                "d": VantageEnum.DISADVANTAGE,
                                "no": VantageEnum.NO,
                                "n": VantageEnum.NO
                            }[args[2].lower()]
                            current_attack.tmp_damage = args[3]
                            current_attack.button = args[4] in ["yes", "y"]
                            current_attack.stage = EAttackStage.ROLL_TO_HIT
                        else:
                            await ctx.send("Invalid arguments")
                    else:
                        await ctx.send("Invalid number of arguments")
                else:
                    if len(args) == 1:
                        current_attack.stage = EAttackStage.MAGIC_BUTTON
                    elif len(args) == 2:
                        if args[1].lower() in ["yes", "y", "no", "n"]:
                            current_attack.button = args[1] in ["yes", "y"]

                            current_attack.stage = EAttackStage.ROLL_EFFECT if current_attack.button \
                                else EAttackStage.CHECK_CASCADE
                        else:
                            await ctx.send("Invalid arguments")
                    else:
                        await ctx.send("Invalid number of arguments")
            else:
                await ctx.send("Weapon not found")
        else:
            current_attack.stage = EAttackStage.WEAPON_NAME
            current_attack.attacker = ctx.author.id

        await AttackStage.get_stage(current_attack.stage).prompt(ctx.message, current_attack, user)


def setup(bot):
    bot.add_cog(Attack(bot))
