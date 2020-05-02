from discord.ext import commands
from discord.ext.commands import Cog

from .user_data import UserList, Weapon, WeaponType, WeaponDuplicationException


class Weapons(Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def weapon(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send("Please invoke a valid subcommand: `new`, `get`")

    @weapon.command(pass_context=True)
    async def new(self, ctx, *args):
        if (len(args) == 3) or (len(args) == 2 and args[1] == "magic"):
            name = args[0]
            user_list = UserList.get_list_for(ctx.guild.id)
            user = user_list.get_user(ctx.author.id)

            try:
                if args[1] != "magic":
                    user.add_weapon(name, Weapon(WeaponType.MUNDANE, args[1], args[2]))
                    await ctx.send(f"Created weapon {args[0]} with {args[1]} to-hit and {args[2]} damage")
                else:
                    user.add_weapon(name, Weapon(WeaponType.MAGIC))
                    await ctx.send(f"Created magical weapon {args[0]}")
            except WeaponDuplicationException:
                await ctx.send("A weapon by that name already exists")
        else:
            await ctx.send("Incorrect arguments")

    @weapon.command(pass_context=True)
    async def get(self, ctx):
        user_list = UserList.get_list_for(ctx.guild.id)
        user = user_list.get_user(ctx.author.id)
        message = "```\n"
        message += f"{'Weapon Name':<30} {'To Hit':<10} {'Damage':<10} {'Uses':<10}\n"
        weapons = user.get_weapons()
        for weapon_name in weapons:
            weapon = weapons[weapon_name]

            message += f"{weapon_name.capitalize():<30} "
            if weapon.weapon_type == WeaponType.MUNDANE:
                message += f"{weapon.to_hit:<10} {weapon.damage:<10}"
            else:
                message += f"{'':<21}"
            message += f"{weapon.uses}"
            message += "\n"
        message += "```"
        await ctx.send(message)


def setup(bot):
    bot.add_cog(Weapons(bot))
