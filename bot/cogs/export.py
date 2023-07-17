# Discord bot for WT Squadrons by Robert White

# 17/05/23
# Cog enabling the /tracker <(OPT)parameter> command, used to control the squadron tracking functionality of the bot.
# When called with a command argument, provides more detailed information about the given command. 


# Imports
import time
import datetime
import asyncio

import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice


from cogs.helpers import gather

# ----- 

class export_class(commands.Cog):
    # Constructor
    def __init__(self, bot):
        self.bot = bot

    # A list of choices for the parameter.
    squadron_list = [
        Choice(name='xTHCx', value='xthcx'),
        Choice(name='vTHCv', value='vthcv'),
        Choice(name='xTHCv', value='xthcv'),
        Choice(name='vTHCx', value='vthcx'),
    ]

    # Declare that this command is a hybrid command. Aliases allow the command to be called in discord using a different name.
    @commands.hybrid_command(name="export", description="Exports squadronData to a JSON file.", aliases=["e"])
    # Add cooldown to your command.
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    # Declare that only owner may use this command.
    @commands.is_owner()
    # Declare that only users with a specific role may use this command.
    @commands.has_any_role(1024425187371929678, "Commander Social") # Can be role id or role name.
    # Describe the command's parameter.
    @app_commands.describe(squadron="Select a squadron")
    # Give a list of parameters accepted.
    @app_commands.choices(squadron=squadron_list)
    # Sync command to a server. Remove this if you want to make it global.
    #@app_commands.guilds(123) # Replace 123 with the server id.
    async def export(self, ctx: commands.Context, squadron: str):

        filePath = gather.saveData(squadron)
        await ctx.send(file=discord.File(filePath))
        print(f"{squadron} squadronData saved and exported.")

    @export.error
    async def error(self, ctx, error: commands.CommandError):
        # Triggers when user omitted and argument.
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Missing argument. `?e <squadron>`")
        # Triggers when user is on cooldown.
        elif isinstance(error, commands.CommandOnCooldown):
            timeRemaining = str(
                datetime.timedelta(
                    seconds=int(error.retry_after))
            )
            await ctx.send(
                f"Please wait `{timeRemaining}` to execute this command again.", ephemeral=True)
        # Triggers if user is not bot owner.
        elif isinstance(error, commands.NotOwner):
            await ctx.send("You're not the owner.", ephemeral=True)
        # Triggers if user does not have the required role.
        elif isinstance(error, commands.MissingAnyRole):
            await ctx.send("You need to be at least <rank> to execute this command.", ephemeral=True)
        else:
            print("  -- Error --  ")
            print(error)
            await ctx.send(error)

async def setup(bot: commands.Bot):
    await bot.add_cog(export_class(bot))


# ----- 










