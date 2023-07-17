# Discord bot for WT Squadrons by Robert White

# 07/06/23
# Collection of helper functions for comparing two squadronData
# objects, identfiying changes between them.


# Imports


# -----

# Checks for member changes (joins, leaves, name changes), in addition to the number of games won/lost. 
# Returns three integers and three lists: pointChange, gainedPoints, lostPoints, playersLeft, playersJoined, playersRenamed. 
def all(squadronData, prevSquadronData):
    pointChange = int(squadronData['points']) - int(prevSquadronData['points']) # Store a change in points.
    gainedPoints = 0
    lostPoints = 0
    playersLeft = []
    playersJoined = []
    playersRenamed = []

    #print("i", end="")

    # Check for members leaving
    for prevMember in prevSquadronData['players']:
        matched = False
        for currMember in squadronData['players']:
            if currMember['name'] == prevMember['name']:
                matched = True
                break
        if matched == False:
            playersLeft.append(prevMember)

    # Check for new members, and count the number of players who've gained/lost points.
    for currMember in squadronData['players']:
        matched = False
        for prevMember in prevSquadronData['players']:
            if currMember['name'] == prevMember['name']:
                matched = True

                # Checks the number of players whose points have changed, to determine if concurrent squads have won/lost simultaneously.
                if currMember['points'] > prevMember['points']:
                    gainedPoints += 1
                    print(f"Player {currMember['name']} gained points.")
                elif currMember['points'] < prevMember['points']:
                    lostPoints += 1
                    print(f"Player {currMember['name']} lost points.")
                break
        if matched == False:
            playersJoined.append(currMember)

    for leftPlayer in playersLeft: 
        for joinedPlayer in playersJoined:
            if leftPlayer["points"] == joinedPlayer["points"] and leftPlayer["joinDate"] == joinedPlayer["joinDate"]:
                playersJoined.remove(joinedPlayer)
                playersLeft.remove(leftPlayer)
                playersRenamed.append({'prev': leftPlayer['name'], 'curr': joinedPlayer['name']})
    
    #print(f"gainedPoints: {gainedPoints}, lost points: {lostPoints}")

    if len(playersRenamed) > 0:
        for renamedPlayer in playersRenamed: 
            print(renamedPlayer['prev'] + " has changed thier IGN to: " + renamedPlayer['curr'])

    return pointChange, gainedPoints, lostPoints, playersLeft, playersJoined, playersRenamed