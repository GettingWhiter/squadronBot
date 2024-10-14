# Discord bot for WT Squadrons by Robert White

# 17/05/23
# Cog enabling the /test <(CHO)fruits, (OPT)string> command, used for testing basic functionality
# and as a template for future cogs.


from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice

import datetime
from typing import Optional

class test_class(commands.Cog):
    # Constructor
    def __init__(self, bot):
        self.bot = bot

    # A list of choices for the parameter fruits.
    fruit_choice_list = [
        Choice(name="🍎 Apple", value="Apple"),
        Choice(name="🍊 Orange", value="Orange"),
        Choice(name="🍌 Banana", value="Banana"),
    ]

    # Declare that this command is a hybrid command. Aliases allow the command to be called in discord using a different name. so in this case ?t
    @commands.hybrid_command(name="test", description="Verifes basic bot functionality, and acts as a nice template.", aliases=["t"])
    # Add cooldown to your command.
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    # Declare that only users with a specific role may use this command.
    @commands.has_any_role(573055362425683979, "Bot admin") # role id or role name.
    # Describe the command's parameter.
    @app_commands.describe(fruits="Select your fruits.")
    # Give a list of options the parameter fruits accept.
    @app_commands.choices(fruits=fruit_choice_list)
    # Sync command to a server. Remove this if you want to make it global.
    #@app_commands.guilds(123) # Replace 123 with the server id.
    async def test(self, ctx: commands.Context, fruits: str, optional_str_param: Optional[str] = "none"):
        await ctx.send(f"You selected {fruits} and {optional_str_param}")

    @test.error
    async def error(self, ctx, error: commands.CommandError):
        # Triggers when user omitted and argument.
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send('Missing argument. `?c <fruits>, <optional_msg>`')
        # Triggers when user is on cooldown.
        if isinstance(error, commands.CommandOnCooldown):
            timeRemaining = str(
                datetime.timedelta(
                    seconds=int(error.retry_after))
            )
            await ctx.send(
                f"Please wait `{timeRemaining}` to execute this command again.",
                ephemeral=True)
        # Triggers if user is not bot owner.
        if isinstance(error, commands.NotOwner):
            await ctx.send("You're not the owner.")
        # Triggers if user does not have the required role.
        if isinstance(error, commands.MissingAnyRole):
            await ctx.send("You need to be at least <rank> to execute this command.")

async def setup(bot: commands.Bot):
    await bot.add_cog(test_class(bot))