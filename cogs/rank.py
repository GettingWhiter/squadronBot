# Discord bot for WT Squadrons by Robert White

# 17/05/23
# Cog enabling the /rank <(OPT)command> command.
# describe.


from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

import datetime
from typing import Optional

class rank_class(commands.Cog):
    # Constructor
    def __init__(self, bot):
        self.bot = bot

    # A list of choices for the parameter <command>.\
    command_list = [
        Choice(name="xTHCx", value="xTHCx"),
        Choice(name="vTHCv", value="vTHCv"),
    ]

    # Declare that this command is a hybrid command.
    @commands.hybrid_command(name="rank", description="Displays the position of the caller's squadron relative to the four nearest competitors.", aliases=["r"])
    # Add cooldown to your command.
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    # Declare that only users with a specific role may use this command.
    @commands.has_any_role(1024425187371929678, "Commander Social") # Can be role id or role name.
    # Describe the <command> parameter.
    @app_commands.describe(command="Select the command you wish to know more about.")
    # Give a list of options the parameter <command> accepts.
    @app_commands.choices(command=command_list)
    async def rank(self, ctx: commands.Context, command: Optional[str] = "none"):
        await ctx.send(f"You selected {command}")

    @rank.error
    async def error(self, ctx, error: commands.CommandError):
        # Triggers when user is on cooldown.
        if isinstance(error, commands.CommandOnCooldown):
            timeRemaining = str(
                datetime.timedelta(
                    seconds=int(error.retry_after))
            )
            await ctx.send(
                f"Please wait `{timeRemaining}` to execute this command again.",
                ephemeral=True)
        # Triggers if user does not have the required role.
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("You need to be at least <rank> to execute this command.")

async def setup(bot: commands.Bot):
    await bot.add_cog(rank_class(bot))