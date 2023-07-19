# Discord bot for WT Squadrons by Robert White

# 17/05/23
# Cog enabling the /tracker <(OPT)parameter> command, used to control the squadron tracking functionality of the bot.
# When called with a command argument, provides more detailed information about the given command. 


# Imports
import time
import datetime
import asyncio

from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from decouple import config

from cogs.helpers import gather, check

# ----- 

class tracker_class(commands.Cog):
    # Constructor
    def __init__(self, bot):
        self.bot = bot
        self.switch = True
        self.channel = 0

    # A list of choices for the parameter.
    switch_list = [
        Choice(name='Start', value='start'),
        Choice(name='Stop', value='stop'),
    ]

    # Declare that this command is a hybrid command. Aliases allow the command to be called in discord using a different name.
    @commands.hybrid_command(name="tracker", description="Start/Stop the logging functionality of the bot.", aliases=["s"])
    # Add cooldown to your command.
    @commands.cooldown(1, 15.0, commands.BucketType.user)
    # Declare that only owner may use this command.
    @commands.is_owner()
    # Declare that only users with a specific role may use this command.
    @commands.has_any_role(1024425187371929678, "Commander Social") # Can be role id or role name.
    # Describe the command's parameter.
    @app_commands.describe(switch="Select a parameter")
    # Give a list of parameters accepted.
    @app_commands.choices(switch=switch_list)
    async def tracker(self, ctx: commands.Context, switch: str):
        match switch:
            case 'start': 
                self.switch = True
                await ctx.send(":arrow_forward: `Tracker started`\n```Idle Polling interval: " + config("IDLE_INTERVAL") + " seconds\nEU Polling interval: " + config("EU_INTERVAL") + " seconds\nUS Polling interval: " + config("US_INTERVAL") + " seconds```")
                await scheduler(self)
            case 'stop':
                self.switch = False
                self.channel = ctx.channel
                print(self.channel)
                await ctx.send(f":pause_button: `Tracker stopping, please wait...`")
            case _:
                await ctx.send(f"Invalid argument: {switch}")

    @tracker.error
    async def error(self, ctx, error: commands.CommandError):
        # Triggers when user omitted an argument.
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("Missing argument. `?c <fruits>, <optional_msg>`")
        # Triggers when user is on cooldown.
        elif isinstance(error, commands.CommandOnCooldown):
            timeRemaining = str(datetime.timedelta(seconds=int(error.retry_after)))
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

    async def getSwitch(self):
        return self.switch

async def setup(bot: commands.Bot):
    await bot.add_cog(tracker_class(bot))


# ----- 


async def scheduler(self):

    squadronList = await createSquadronList(self)
    active = False

    while await self.getSwitch() == True:
        currentTime = (time.gmtime())
        print(f"{str(currentTime.tm_hour).rjust(2, '0')}:{str(currentTime.tm_min).rjust(2, '0')}:{str(currentTime.tm_sec).rjust(2, '0')}")

        # Current GMTime is between 14-22, thus EU session is active.
        if currentTime.tm_hour >= 14 and currentTime.tm_hour < 22 or (currentTime.tm_hour == 22 and currentTime.tm_min <= 15):
            # If this is the first loop within the EU bracket, post a new message to the log channel.
            if not active:
                sessionDate = (f"EU Session - {currentTime.tm_mday}/{currentTime.tm_mon}/{currentTime.tm_year}")
                for squadron in squadronList:
                    squadron['data'] = gather.getData(squadron['tag'])
                    squadron['wins'] = 0
                    squadron['losses'] = 0
                    squadron['startingPoints'] = str(squadron['data']['points'])
                    squadron['sessionMessage'] = await squadron['channel'].send(f"{sessionDate} - {await timeRemaining(currentTime, 'EU')}")
                checkCounter = 1
                active = True

            # Gather data from squadron pages on WT website, create objects with usable attributes.
            for squadron in squadronList:
                formattedTime = (f"{str(currentTime.tm_hour).rjust(2, '0')}:{str(currentTime.tm_min).rjust(2, '0')}:{str(currentTime.tm_sec).rjust(2, '0')}")
                if squadron['data']['time'].split(' ', 1)[1][:-1] != (formattedTime[:-1]):
                    squadron['data'] = gather.getData(squadron['tag'])

                # If there is a previous data set, check for differences between it and the current set.
                if squadron['prevData']:
                    pointChange, gainedPoints, lostPoints, playersLeft, playersJoined, playersRenamed = check.all(squadron['data'], squadron['prevData'])
                    checkCounter += 1 # increment by 1

                    # Determine if any players have joined/left/renamed, create a message with this information.
                    if len(playersLeft) != 0 or len(playersJoined) != 0 or len(playersRenamed) != 0:
                        await createTurnoverMessage(squadron['channel'], playersLeft, playersJoined, playersRenamed)

                    if pointChange != 0: 
                        squadron['messageArray'], squadron['wins'], squadron['losses'] = await updateMessageArray(squadron['messageArray'], squadron['wins'], 
                            squadron['losses'], currentTime, squadron['startingPoints'], squadron['data']['points'], pointChange, gainedPoints, lostPoints)
                    if len(squadron['messageArray']) > 0:
                        # Prepare message header
                        squadron['sessionMessage'].content = (f"{sessionDate} - {await timeRemaining(currentTime, 'EU')}")

                        # Add 'code block' with interval result strings.
                        squadron['sessionMessage'].content = (f"{squadron['sessionMessage'].content}\n```diff\nPts change      W/L    Time     Delta    Matches Won/Lost\n")
                        for messageString in squadron['messageArray']:
                            squadron['sessionMessage'].content = squadron['sessionMessage'].content + messageString
                        squadron['sessionMessage'].content = (f"{squadron['sessionMessage'].content}```")

                        # Edit session message in discord
                        await squadron['sessionMessage'].edit(content=squadron['sessionMessage'].content)
                    else:
                        squadron['sessionMessage'].content = (f"{sessionDate} - {await timeRemaining(currentTime, 'EU')}")
                        await squadron['sessionMessage'].edit(content=squadron['sessionMessage'].content)

            for squadron in squadronList: squadron['prevData'] = squadron['data']
            await asyncio.sleep(int(config("EU_INTERVAL")))

        # Current GMTime is between 1-7, thus US session is active.
        elif currentTime.tm_hour >= 1 and currentTime.tm_hour < 7 or (currentTime.tm_hour == 7 and currentTime.tm_min < 15):
            # If this is the first loop within the US bracket, post a new message to the log channel,
            if not active:
                sessionDate = (f"US Session - {currentTime.tm_mday}/{currentTime.tm_mon}/{currentTime.tm_year}")
                for squadron in squadronList:
                    squadron['data'] = gather.getData(squadron['tag'])
                    squadron['wins'] = 0
                    squadron['losses'] = 0
                    squadron['startingPoints'] = str(squadron['data']['points'])
                    squadron['sessionMessage'] = await squadron['channel'].send(f"{sessionDate} - {await timeRemaining(currentTime, 'US')}")
                checkCounter = 1
                active = True

            # Gather data from squadron pages on WT website, create objects with usable attributes.
            for squadron in squadronList:
                formattedTime = (f"{str(currentTime.tm_hour).rjust(2, '0')}:{str(currentTime.tm_min).rjust(2, '0')}:{str(currentTime.tm_sec).rjust(2, '0')}")
                if squadron['data']['time'].split(' ', 1)[1][:-1] != (formattedTime[:-1]):
                    squadron['data'] = gather.getData(squadron['tag'])

                # If there is a previous data set, check for differences between it and the current set.
                if squadron['prevData']:
                    pointChange, gainedPoints, lostPoints, playersLeft, playersJoined, playersRenamed = check.all(squadron['data'], squadron['prevData'])
                    checkCounter += 1 # increment by 1

                    # Determine if any players have joined/left/renamed, create a message with this information.
                    if len(playersLeft) != 0 or len(playersJoined) != 0 or len(playersRenamed) != 0:
                        await createTurnoverMessage(squadron['channel'], playersLeft, playersJoined, playersRenamed)

                    if pointChange != 0: 
                        squadron['messageArray'], squadron['wins'], squadron['losses'] = await updateMessageArray(squadron['messageArray'], squadron['wins'], 
                            squadron['losses'], currentTime, squadron['startingPoints'], squadron['data']['points'], pointChange, gainedPoints, lostPoints)
                    if len(squadron['messageArray']) > 0: # Prepare message header
                        squadron['sessionMessage'].content = (f"{sessionDate} - {await timeRemaining(currentTime, 'US')}")

                        # Add 'code block' with interval result strings.
                        squadron['sessionMessage'].content = (f"{squadron['sessionMessage'].content}\n```diff\nPts change      W/L    Time     Delta    Matches Won/Lost\n")
                        for messageString in squadron['messageArray']:
                            squadron['sessionMessage'].content = squadron['sessionMessage'].content + messageString
                        squadron['sessionMessage'].content = (f"{squadron['sessionMessage'].content}```")

                        # Edit session message in discord
                        await squadron['sessionMessage'].edit(content=squadron['sessionMessage'].content)
                    else:
                        squadron['sessionMessage'].content = (f"{sessionDate} - {await timeRemaining(currentTime, 'US')}")
                        await squadron['sessionMessage'].edit(content=squadron['sessionMessage'].content)

            for squadron in squadronList: squadron['prevData'] = squadron['data']
            await asyncio.sleep(int(config("US_INTERVAL")))
        
        # Current GMTime is not between 1:00-7:15 or 14:00-22:15 - neither session is active.
        else:
            # If this is the first loop after an EU or US session, set the active 
            # flag to False and update the now concluded session's message. 
            if active: 
                print("Idle, interval: " + config("IDLE_INTERVAL"))
                active = False
                for squadron in squadronList:
                    if len(squadron['messageArray']) > 0:
                        squadron['sessionMessage'].content = (f"{sessionDate} - Session closed.")
                        # Add 'code block' with interval result strings.
                        squadron['sessionMessage'].content = (f"{squadron['sessionMessage'].content}\n```diff\nPts change      W/L    Time     Delta    Matches Won/Lost\n")
                        for messageString in squadron['messageArray']:
                            squadron['sessionMessage'].content = squadron['sessionMessage'].content + messageString
                        squadron['sessionMessage'].content = (f"{squadron['sessionMessage'].content}```{checkCounter} checks - {squadron['startingPoints']} --> {squadron['data']['points']}")
                        await squadron['sessionMessage'].edit(content=squadron['sessionMessage'].content)
                        squadron['messageArray'].clear()
                    else:
                        squadron['sessionMessage'].content = (f"{sessionDate} - Session closed.\n```No games played```{checkCounter} checks - {squadron['startingPoints']} --> {squadron['data']['points']}")
                        await squadron['sessionMessage'].edit(content=squadron['sessionMessage'].content)

            for squadron in squadronList:
                # Gather data from the squadron's page on WT website, create object with usable attributes.
                squadron['data'] = gather.getData(squadron['tag'])

                # If there is a previous data set, check for differences between it and the current set.
                # Determine if these are as a result of wins/losses/member changes. Update session message.
                if squadron['prevData']:
                    pointChange, gainedPoints, lostPoints, playersLeft, playersJoined, playersRenamed = check.all(squadron['data'], squadron['prevData'])
                    # Determine if any players have joined/left/renamed, create a message with this information.
                    if len(playersLeft) != 0 or len(playersJoined) != 0 or len(playersRenamed) != 0:
                        await createTurnoverMessage(squadron['channel'], playersLeft, playersJoined, playersRenamed)

            squadron['prevData'] = squadron['data']
            await asyncio.sleep(int(config("IDLE_INTERVAL")))

        # Inform the user that the tracker loop has stopped.
        if await self.getSwitch() == False:
            await self.bot.get_channel(1024425191360708611).send(':stop_button: `Tracker stopped`')


async def createSquadronList(self):
    squadronList = []
    for squadron in ['xTHCx', 'vTHCv']:
        channel = self.bot.get_channel(int(config(f"{squadron.upper()}_WL_CHANNEL"))) #_WL_CHANNEL")) #_TEST_CHANNEL"))
        squadronList.append({'tag': squadron, 'data': None, 'prevData': None,
            'channel': channel, 'activeMessage': None, 'messageArray': [], 'startingPoints': None, 'wins': 0, 'losses': 0})
    return squadronList

async def timeRemaining(currentTime, session):
    if session == 'EU' and (22 - currentTime.tm_hour > 1 and currentTime.tm_min == 0):
        timeRemaining = (f"{22 - currentTime.tm_hour} hours remaining.")
    elif session == 'EU' and (22 - currentTime.tm_hour > 1):
        timeRemaining = (f"{21 - currentTime.tm_hour} hours, {60 - currentTime.tm_min} minutes remaining.")
    elif session == 'EU' and (22 - currentTime.tm_hour == 1 and currentTime.tm_min == 0):
        timeRemaining = (f"{22 - currentTime.tm_hour} hour remaining.")
    elif session == 'EU' and (21 - currentTime.tm_hour == 1):
        timeRemaining = (f"1 hour, {60 - currentTime.tm_min} minutes remaining.")
    elif session == 'EU' and (21 - currentTime.tm_hour == 0):
        timeRemaining = (f"{60 - currentTime.tm_min} minutes remaining.")

    elif session == 'US' and (7 - currentTime.tm_hour > 1 and currentTime.tm_min == 0):
        timeRemaining = (f"{7 - currentTime.tm_hour} hours remaining.")
    elif session == 'US' and (7 - currentTime.tm_hour > 1):
        timeRemaining = (f"{6 - currentTime.tm_hour} hours, {60 - currentTime.tm_min} minutes remaining.")
    elif session == 'US' and (7 - currentTime.tm_hour == 1 and currentTime.tm_min == 0):
        timeRemaining = (f"{7 - currentTime.tm_hour} hour remaining.")
    elif session == 'US' and (6 - currentTime.tm_hour == 1):
        timeRemaining = (f"1 hour, {60 - currentTime.tm_min} minutes remaining.")
    elif session == 'US' and (6 - currentTime.tm_hour == 0):
        timeRemaining = (f"{60 - currentTime.tm_min} minutes remaining.")

    else:
        timeRemaining = (f"Session closed.")
    return timeRemaining

async def updateMessageArray(messageArray, wins, losses, currentTime, startingPoints, currentPoints, pointChange, gainedPoints, lostPoints):
    matchesWon = 0
    matchesLost = 0
    if 4 < gainedPoints < 9:
        matchesWon = 1
        wins += 1
    elif 12 < gainedPoints < 17:
        matchesWon = 2
        wins += 2
    elif 20 < gainedPoints:
        matchesWon = 3
        wins += 3
    
    if 4 < lostPoints < 9:
        matchesLost = 1
        losses += 1
    elif 12 < lostPoints < 17:
        matchesLost = 2
        losses += 2
    elif 20 < lostPoints:
        matchesLost = 3
        losses += 3

    # If at least one match has been won/lost, prepare this interval's string.
    if matchesWon != 0 or matchesLost != 0:

        # Create the points change section.
        if pointChange < 0:
            pointSummary = (f"- {pointChange * -1} points").ljust(16, ' ')
        else:
            pointSummary = (f"+ {pointChange} points").ljust(16, ' ')

        # Create the Win/Loss section.
        wlSummary = (f"{wins}/{losses}").ljust(7, ' ')

        # Create the time section.
        hourString = str(currentTime.tm_hour)
        if len(hourString) == 1:
            # Add a leading 0 to make time consistent.
            hourString = (f"0{hourString}") 
        minuteString = str(currentTime.tm_min)
        if len(minuteString) == 1:
            # Add a leading 0 to make time consistent.
            minuteString = (f"0{minuteString}") 
        timeSummary = (f"{hourString}:{minuteString}").ljust(9, ' ')

        # Create the session delta section.
        deltaSummary = (f"{int(currentPoints) - int(startingPoints)}").ljust(9, ' ')
        
        # Store an appropriate 'matchSummary' to indicate the numbers of matches won 
        # or lost during this interval.
        if matchesWon == 0:
            if matchesLost == 1:
                matchSummary = (f"{matchesLost} match lost   ")
            else:
                matchSummary = (f"{matchesLost} matches lost ")
        elif matchesLost == 0:
            if matchesWon == 1:
                matchSummary = (f"{matchesWon} match won    ")
            else:
                matchSummary = (f"{matchesWon} matches won  ")
        else: 
            matchSummary = (f"{matchesWon} won, {matchesLost} lost  ")

        sessionString = (f"{pointSummary}{wlSummary}{timeSummary}{deltaSummary}{matchSummary}\n")
        messageArray.append(sessionString)

    return messageArray, wins, losses

async def createTurnoverMessage(channel, playersLeft, playersJoined, playersRenamed):
    for player in playersLeft:
        print(f"Player Left: {player}")
        await channel.send(f"`{player['name']}` left: (`pts: {player['points']}, act: {player['activity']}, role: {player['role']}, joinDate: {player['joinDate']})`")
    for player in playersJoined:
        print(f"Player joined: {player}")
        await channel.send(f"`{player['name']}` joined")
    for player in playersRenamed:
        print(f"Player renamed: {player}")
        await channel.send(f"Player renamed: {player}")
    playersLeft.clear()
    playersJoined.clear()
    playersRenamed.clear()