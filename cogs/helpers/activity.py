# WT Squadron activity monitor by Robert White, built using aspects of 
# Prototype webscraper built for a university project.
# 25/04/23

# Requires requests, bs4 and lxml to be installed.

# Imports
import re # Regular expressions, yeehaw - parser() function.
import json # Used to store organised object data parsed and assembled from the HTML source in the parser() function.
import requests # Requests module used for webscraping in the scraper() function.
import datetime
from bs4 import BeautifulSoup


# --- PUBLIC VARIABLES (Global) ---

# Target URL components
baseURL = 'https://warthunder.com/en/community/claninfo/'
squad1 = 'Try%20Hard%20Coalition' #Comp
squad2 = 'Try%20Hard%20Coalition%20Social' #Social
squad3 = 'Try%20Hard%20Coalition%20Casuals' #Casual
squad4 = 'Try%20Hard%20Coalition%20Legacy' #Legacy

# --- PUBLIC FUNCTIONS ---

# Forms a complete URL pointing to the appropriate squadron page, then calls the scraper function using said URL.
def getData(squadron):

    match squadron.lower():
        case '':
            #TODO: Make this an error.
            print('Error - No identifier set, please enter one of the following: ("Comp", "Social", "Casual" or "Legacy").')
        case 'comp':
            scraper(baseURL + squad1)
        case 'social':
            scraper(baseURL + squad2)
        case 'casual':
            scraper(baseURL + squad3)
        case 'legacy':
            scraper(baseURL + squad4)
        case _:
            #TODO: Make this an error.
            print('The squadron name (' + squadron + ') is not supported.')
    return

# Scrapes data from the provided URL (TODO: consider using callbacks in this to make the function more readily usable)
def scraper(url):
        try:
            response = requests.get(url, timeout=60)
            content = BeautifulSoup(response.content, "lxml")
            #print(content)
            parser(content)
            return

        except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
            print('Timeout raised and caught.')
            return

# Funtion for importing HTML data via a downloaded webpage.
def fileInput(address):
    with open(address, "r", encoding='utf-8') as f:
        text= f.read()
    content = BeautifulSoup(text, "lxml")
    parser(content)
    return

# Parser for content scraped from the War Thunder squadron pages
def parser(content):
    title = ((content.find('div', attrs={"class": "squadrons-info__title"}).text).strip().encode('ascii', 'ignore')).decode()
    squadronInfo = {
        #TODO: Finish these first two off with some string manipulation
        'time': datetime.datetime.now().strftime("%Y/%m/%d, %H:%M:%S"),
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

    # Export squadronInfo as squadronData.json
    with open('squadronData/' + squadronInfo['tag'] + datetime.datetime.now().strftime("-%Y%m%d-%H%M%S") +'.json', 'w') as outfile:
        json.dump(squadronInfo, outfile, indent = 4)

# Function to open and compile data from previous seasons to present in a more useful form.
def generateReport(squadName):
    match squadName.lower():
        case '':
            print('Error - No identifier set, please enter one of the following: ("Comp", "Social", "Casual" or "Legacy").')
        case 'comp': 
            mergeData('[xTHCx]')
        case 'social':
            mergeData('[vTHCv]')
        case 'casual':
            mergeData('[xTHCv]')
        case 'legacy':
            print('This squadron does not require activity.')
        case _:
            print('The squadron name (' + squadName + ') is not supported.')
    return

def mergeData(squadTag):
    return

#testing
#getData('Social')

# Import HTML file.
#fileInput('squadronData/vthcv/Profile of squadron Try Hard Coalition Social - Squadron Leaderboards - Community - War Thunder.html')