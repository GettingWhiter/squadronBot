# Discord bot for WT Squadrons by Robert White

# 17/05/23 - 18/03/24
# Main part of the bot.
# Uses 'hot-swappable' cogs for each command to make maintenance less disruptive. 


# Imports
import discord
from discord.ext import commands

import glob
from decouple import config

# -----

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix = "?", 
            intents = discord.Intents.all(), 
            application_id = config("APP_ID", cast=int),
            strip_after_prefix = True,
        )

    async def setup_hook(self) -> None:
        print(f"{self.user} has connected to Discord!")

        # Load Jishaku extension (debugging and utility extenson for bots coded in discord.py)
        await self.load_extension("jishaku")

        # Load extensions that are inside cogs folder
        #for cog in glob.glob("cogs/**/*.py", recursive=True):
        for cog in glob.glob("cogs/*.py", recursive=True):
            print(cog)
            await self.load_extension(cog.replace("\\", ".").replace("/", ".").removesuffix(".py"))

    # Close bot and connections
    async def close(self) -> None:
        await super().close()


if __name__ == "__main__":
    bot = MyBot()
    bot.run(config("TOKEN"), reconnect = True)