# Discord bot for WT Squadrons by Robert White

# 08/06/23 - 23/03/24
# Collection of helper functions for gathering, parsing and 
# objectifiying squadron data from the War Thunder website.


# Requires requests, bs4 and lxml to be installed.

# Imports
import re # Regular expressions, yeehaw - parser() function.
import json # Used to store organised object data parsed and assembled from the HTML source in the parser() function.
import requests # Requests module used for webscraping in the scraper() function.
import asyncio
import aiohttp # async replacement of requests
import datetime
import time
from bs4 import BeautifulSoup

from decouple import config

# -----

# Saves the resultant squadronInfo from a scraper call to a JSON file.
async def saveData(squadron):
    squadronInfo = await getData(squadron)
    # Export squadronInfo as squadronData.json 
    # TODO: create a folder if one does not already exist
    filePath = 'squadronData/' + squadronInfo['tag'] + datetime.datetime.now().strftime("-%Y%m%d-%H%M%S") +'.json'
    with open(filePath, 'w') as outfile:
        json.dump(squadronInfo, outfile, indent = 4)
    return filePath

# Forms a complete URL pointing to the appropriate squadron page, then calls the scraper function using said URL.
async def getData(squadron):
    match squadron.lower():
        case '':
            #TODO: Make this an error.
            print('Error - No identifier set, please enter one of the following: ("Comp", "Social", "Casual" or "Legacy").')
        case 'xthcx': #comp
            return await asyncScraper(config("BASE_URL") + config("COMP_SUFFIX"))
        case 'vthcv': #social
            return await asyncScraper(config("BASE_URL") + config("SOCIAL_SUFFIX"))
        case 'xthcv': #casual
            return await asyncScraper(config("BASE_URL") + config("CASUAL_SUFFIX"))
        case 'vthcx': #legacy
            return await asyncScraper(config("BASE_URL") + config("LEGACY_SUFFIX"))
        case _:
            #TODO: Make this an error.
            print('The squadron name (' + squadron + ') is not supported.')
    return

# Scrapes data from the provided URL (TODO: consider using callbacks in this to make the function more readily usable)
def scraper(url):
        try:
            retries = 0
            response = requests.get(url, timeout=60)
            #print(response)
            content = BeautifulSoup(response.content, "lxml")
            if content.find('div', attrs={"class": "squadrons-info__title"}) != None:
                return parser(content)
            else:
                if retries <= 15:
                    print(f"Scraper failed to retrieve usable webpage content, retrying in {config('RETRY_INTERVAL')} seconds.\nContent retrieved: {content}")
                    retries += 1
                    time.sleep(config("RETRY_INTERVAL"))
                    scraper(url)
                else:
                    print(f"Scraper unable to retrieve usable data, aborting.")
                    return
        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            print('Timeout raised and caught.')
            return
        except Exception as e:
            print(f"Error raised in 'gather.scraper' function: {e}")
        return

# Scrapes data from the provided URL asyncronously. (TODO: consider using callbacks in this to make the function more readily usable)
async def asyncScraper(url):
        try:
            retries = 0
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=60) as response:
                    content = BeautifulSoup(await response.text(), "lxml")

            if content.find('div', attrs={"class": "squadrons-info__title"}) != None:
                return parser(content)
            else:
                if retries <= 15:
                    print(f"Scraper failed to retrieve usable webpage content, retrying in {config('RETRY_INTERVAL')} seconds.\nContent retrieved: {content}")
                    retries += 1
                    asyncio.sleep(config("RETRY_INTERVAL"))
                    await asyncScraper(url)
                else:
                    print(f"Scraper unable to retrieve usable data, aborting.")
                    return
        #except (aiohttp.exceptions.Timeout, aiohttp.exceptions.ReadTimeout):
        #    print('Timeout raised and caught.')
        #    return
        except Exception as e:
            await print(f"Error raised in 'gather.scraper' function: {e}")
        return

# Parser for content scraped from the War Thunder squadron pages
def parser(content):
    try:
        title = ((content.find('div', attrs={"class": "squadrons-info__title"}).text).strip().encode('ascii', 'ignore')).decode()
        currentTime = (time.gmtime())
        squadronInfo = {
            #format: 2022/09/15, 15:36:40
            'time': (f"{str(currentTime.tm_year)}/{str(currentTime.tm_mon).rjust(2, '0')}/{str(currentTime.tm_mday).rjust(2, '0')}, {str(currentTime.tm_hour).rjust(2, '0')}:{str(currentTime.tm_min).rjust(2, '0')}:{str(currentTime.tm_sec).rjust(2, '0')}"),
            #'time': datetime.datetime.now().strftime("%Y/%m/%d, %H:%M:%S"),
            'tag': (title.split(' ', 1))[0], # Get the squadron tag.
            'name': (title.split(' ', 1))[1], # Get the squadron name.
            'playerCount': (content.find('div', attrs={
                "class": "squadrons-info__meta-item"}).text).strip().replace('Number of players: ', ''), # Get the squadron player count
            'description': (content.find('div', attrs={
                "class": "squadrons-info__description squadrons-info__description--full"}).text).strip(), # Get the full squadron description
            'creationDate': (content.find('div', attrs={
                "class": "squadrons-info__meta-item squadrons-info__meta-item--date"}).text).strip().replace('date of creation: ', ''),  # Get the date of squadron creation
            'points': '',
            'activity': '',
            'airKills': '',
            'groundKills': '',
            'deaths': '', 
            'timePlayed': '',
            'players': []
        }
        counter = 0
        for dataItem in content.findAll('div', attrs={"class": "squadrons-counter__value"}):
            if counter == 0:
                squadronInfo['points'] = dataItem.text.strip()
            elif counter == 1:
                squadronInfo['activity'] = dataItem.text.strip()
            counter += 1 # Increment counter by one.

        counter = 0
        for dataItem in content.findAll('li', attrs={"class": "squadrons-stat__item-value"}):
            if counter < 6: pass # Do nothing
            elif counter == 6:
                squadronInfo['groundKills'] = dataItem.text.strip()
            elif counter == 7:
                squadronInfo['airKills'] = dataItem.text.strip()
            elif counter == 8:
                squadronInfo['deaths'] = dataItem.text.strip()
            elif counter == 9:
                squadronInfo['timePlayed'] = dataItem.text.strip()
            counter += 1 # Increment counter by one.

        counter = 0
        for dataItem in content.findAll('div', attrs={"class": "squadrons-members__grid-item"}):
            if counter < 7: pass # Do nothing
            elif counter == 7: # Get player name from the link element.
                name = (dataItem.find('a').get('href')).replace('en/community/userinfo/?nick=', '')
            elif counter == 8: # Get player points
                points = re.sub(r'\s+', '', dataItem.text)
            elif counter == 9: # Get player activity
                activity = re.sub(r'\s+', '', dataItem.text)
            elif counter == 10: # Get player role
                role = re.sub(r'\s+', '', dataItem.text)
            elif counter == 11: # Get player join date
                joinDate = re.sub(r'\s+', '', dataItem.text)
            elif counter == 12:
                # Create an object using the previous variables, append it to the playerArray.
                squadronInfo['players'].append({'name': name, 'points': points, 'activity': activity,
                'role': role, 'joinDate': joinDate})
                counter = 6
            counter+=1 # Increment by one

        #print(squadronInfo)
        return squadronInfo
    except Exception as e: 
        print(f"Error raised in 'gather.parser' function: {e}")
        return

    # Export squadronInfo as squadronData.json
    #with open('squadronData/' + squadronInfo['tag'] + datetime.datetime.now().strftime("-%Y%m%d-%H%M%S") +'.json', 'w') as outfile:
    #    json.dump(squadronInfo, outfile, indent = 4)

#testing
#getData('Social')