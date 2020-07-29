import re

from discord.ext.commands import Cog

from bot import table
from bot.bot import rolls_per_effect
from bot.user_data import CurrentAttack, EAttackStage, UserList, AttackStage, User, WeaponType, VantageEnum


class MessageHandler(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, message):
        if message.author.id == self.bot.user.id \
                or message.channel.name == "effect-log" \
                or message.content.startswith(self.bot.command_prefix):
            return
        current_attack = CurrentAttack.get_current_attack_for(message.guild.id)
        if current_attack.stage != EAttackStage.NONE:
            await self.on_attack(message)

    async def on_attack(self, message):
        current_attack = CurrentAttack.get_current_attack_for(message.guild.id)
        user_list = UserList.get_list_for(message.guild.id)
        user = user_list.get_user(current_attack.attacker)
        if message.content.lower() == "cancel":
            CurrentAttack.reset_for(message.guild.id)
            return

        is_attacker = current_attack.attacker == message.author.id
        is_bot = message.author.id == 279722369260453888
        prev_stage = current_attack.stage.stage_num
        await AttackStage.get_stage(current_attack.stage, is_attacker, is_bot).respond(message, current_attack, user)
        if prev_stage != current_attack.stage.stage_num:
            await AttackStage.get_stage(current_attack.stage).prompt(message, current_attack, user)


def setup(bot):
    bot.add_cog(MessageHandler(bot))
    register_stages()


def make_summary(current_attack: CurrentAttack) -> str:
    summary = "Attack Summary\n"
    if current_attack.weapon.weapon_type == WeaponType.MUNDANE and current_attack.full_attack:
        summary += f"Attack {'hit' if current_attack.hit else 'missed'} with " \
                   f"{current_attack.hit_roll}\n"
        if current_attack.hit:
            summary += f"Attack dealt {current_attack.damage_roll} damage\n"
    if current_attack.weapon.weapon_type == WeaponType.MAGIC or current_attack.hit or not current_attack.full_attack:
        known = current_attack.weapon.player_known
        effect_id = current_attack.weapon.current_effect
        translation = table.get_table(int(effect_id))
        summary += f"The effect was: {'Unknown' if not known else translation}\n"
    return summary


# noinspection DuplicatedCode
def register_stages():
    # AttackStage.register_stage(EAttackStage.TEMP_HIT, AttackStage(template_prompt, template_response))
    AttackStage.register_stage(EAttackStage.WEAPON_NAME, AttackStage(weapon_name_prompt, weapon_name_response))
    AttackStage.register_stage(EAttackStage.TEMP_HIT, AttackStage(temp_hit_prompt, temp_hit_response))
    AttackStage.register_stage(EAttackStage.VANTAGE, AttackStage(vantage_prompt, vantage_response))
    AttackStage.register_stage(EAttackStage.TEMP_DAMAGE, AttackStage(temp_damage_prompt, temp_damage_response))
    AttackStage.register_stage(EAttackStage.MUNDANE_BUTTON, AttackStage(mundane_button_prompt, mundane_button_response))
    AttackStage.register_stage(EAttackStage.ROLL_TO_HIT, AttackStage(to_hit_prompt, to_hit_response))
    AttackStage.register_stage(EAttackStage.DID_HIT, AttackStage(did_hit_prompt, did_hit_response))
    AttackStage.register_stage(EAttackStage.ROLL_DAMAGE, AttackStage(roll_damage_prompt, roll_damage_response))
    AttackStage.register_stage(EAttackStage.MAGIC_BUTTON, AttackStage(magic_button_prompt, magic_button_response))
    AttackStage.register_stage(EAttackStage.CHECK_CASCADE, AttackStage(check_cascade_prompt, check_cascade_response))
    AttackStage.register_stage(EAttackStage.ROLL_EFFECT, AttackStage(roll_effect_prompt, roll_effect_response))


async def template_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    pass


async def template_response(message, current_attack: CurrentAttack, user: User) -> None:
    pass


async def weapon_name_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send(f'With what weapon are you attacking? [{", ".join(user.get_weapons().keys())}]')


async def weapon_name_response(message, current_attack: CurrentAttack, user: User) -> None:
    weapon_name = message.content
    current_attack.weapon_name = weapon_name
    if current_attack.load_weapon(user):
        if current_attack.weapon.weapon_type == WeaponType.MUNDANE:
            current_attack.stage = EAttackStage.TEMP_HIT
        else:
            current_attack.stage = EAttackStage.MAGIC_BUTTON
    else:
        await message.channel.send("Please enter a valid weapon")


async def temp_hit_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send("What is your temporary hit modifier?")


async def temp_hit_response(message, current_attack: CurrentAttack, user: User) -> None:
    current_attack.tmp_hit = message.content
    current_attack.stage = EAttackStage.VANTAGE


async def vantage_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send("Do you have advantage or disadvantage?")


async def vantage_response(message, current_attack: CurrentAttack, user: User) -> None:
    vantages = {
        "advantage": VantageEnum.ADVANTAGE,
        "a": VantageEnum.ADVANTAGE,
        "disadvantage": VantageEnum.DISADVANTAGE,
        "d": VantageEnum.DISADVANTAGE,
        "no": VantageEnum.NO,
        "n": VantageEnum.NO
    }

    vantage = message.content.lower()
    if vantage in vantages:
        current_attack.vantage = vantages[vantage]
        current_attack.stage = EAttackStage.TEMP_DAMAGE
    else:
        await message.channel.send("Please respond with `advantage`, `disadvantage`, or `no`")


async def temp_damage_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send("What is your temporary damage modifier?")


async def temp_damage_response(message, current_attack: CurrentAttack, user: User) -> None:
    current_attack.tmp_damage = message.content
    current_attack.stage = EAttackStage.MUNDANE_BUTTON


async def mundane_button_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send("Do you press the button?")


async def mundane_button_response(message, current_attack: CurrentAttack, user: User) -> None:
    if message.content.lower() in ["yes", "no", "y", "n"]:
        current_attack.button = (message.content.lower() in ["yes", "y"])
        current_attack.stage = EAttackStage.ROLL_TO_HIT
    else:
        await message.channel.send("Please respond with `yes` or `no`")


async def to_hit_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    dice = 'd20' if current_attack.vantage == VantageEnum.NO \
        else ('2d20' + ('k1' if current_attack.vantage == VantageEnum.ADVANTAGE else 'kl1'))
    await message.channel.send(f"!{dice}+{current_attack.weapon.to_hit}+{current_attack.tmp_hit}")


async def to_hit_response(message, current_attack: CurrentAttack, user: User) -> None:
    roll_result = int(message.content.split("\n")[1][2:])
    current_attack.hit_roll = roll_result
    current_attack.stage = EAttackStage.DID_HIT


async def did_hit_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send(f"Does a {current_attack.hit_roll} hit?")


async def did_hit_response(message, current_attack: CurrentAttack, user: User) -> None:
    if message.content.lower() in ["yes", "no", "y", "n"]:
        current_attack.hit = (message.content.lower() in ["yes", "y"])
        if current_attack.hit:
            current_attack.stage = EAttackStage.ROLL_DAMAGE
        else:
            await message.channel.send(make_summary(current_attack))
            CurrentAttack.reset_for(message.guild.id)


async def roll_damage_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send(f"!{current_attack.weapon.damage}+{current_attack.tmp_damage}")


async def roll_damage_response(message, current_attack: CurrentAttack, user: User) -> None:
    roll_result = int(message.content.split("\n")[1][2:])
    current_attack.damage_roll = roll_result
    current_attack.stage = EAttackStage.ROLL_EFFECT if current_attack.button else EAttackStage.CHECK_CASCADE


async def magic_button_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send("Do you press the button?")


async def magic_button_response(message, current_attack: CurrentAttack, user: User) -> None:
    if message.content.lower() in ["yes", "no", "y", "n"]:
        current_attack.button = (message.content.lower() == "yes" or message.content.lower == "y")
        current_attack.stage = EAttackStage.ROLL_EFFECT if current_attack.button else EAttackStage.CHECK_CASCADE
    else:
        await message.channel.send("Please respond with `yes` or `no`")


async def check_cascade_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    current_attack.weapon.uses += 1
    await message.channel.send(
        f"Checking for cascade, DC is " +
        f"{current_attack.weapon.uses}")
    await message.channel.send("!d20")


async def check_cascade_response(message, current_attack: CurrentAttack, user: User) -> None:
    roll_result = int(message.content.split("\n")[1][2:])
    if roll_result <= current_attack.weapon.uses:
        current_attack.effects_to_roll = max((current_attack.weapon.uses // rolls_per_effect) + 1, 1)
        current_attack.stage = EAttackStage.ROLL_EFFECT
    else:
        effect_num = current_attack.weapon.current_effect
        attacker_user = message.guild.get_member(current_attack.attacker)
        log_channel = message.guild.get_channel(668362659611148299)
        effect_str = table.get_table(effect_num)
        await log_channel.send(
            attacker_user.display_name + " re-used effect " + str(effect_num) + ": " + effect_str)
        dice = re.findall("\\d*d\\d+\\+?\\d*", effect_str)
        for die in dice:
            await log_channel.send("!" + die)

        await message.channel.send(make_summary(current_attack))
        CurrentAttack.reset_for(message.guild.id)


async def roll_effect_prompt(message, current_attack: CurrentAttack, user: User) -> None:
    await message.channel.send("!1d20000")


async def roll_effect_response(message, current_attack: CurrentAttack, user: User) -> None:
    roll_result = int(message.content.split("\n")[1][2:])
    attacker_user = message.guild.get_member(current_attack.attacker)
    log_channel = message.guild.get_channel(668362659611148299)
    effect_str = table.get_table(roll_result)
    await log_channel.send(attacker_user.display_name + " rolled effect " + str(roll_result) + ": " + effect_str)
    dice = re.findall("\\d*d\\d+\\+?\\d*", effect_str)
    for die in dice:
        await log_channel.send("!" + die)

    current_attack.weapon.current_effect = roll_result
    current_attack.weapon.player_known = False
    current_attack.weapon.uses = 0

    current_attack.effects_to_roll -= 1
    if current_attack.effects_to_roll > 0:
        await message.channel.send("!1d20000")
    else:
        await message.channel.send(make_summary(current_attack))
        CurrentAttack.reset_for(message.guild.id)
