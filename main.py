###############################################################################
# myCricket.py - A scraper and a stats analyzer for myCricket 
# jamesj223

###############################################################################
# Imports

from myCricket import *

###############################################################################
# User Input

debug = False

wipe = False # TODO Determine whether to wipe based on schema change or not
fetch = False # TODO Determine whether to fetch based on whether numMatches on myCricket == numMatches in PlayerInfo
analysis = True

# Get Player ID
playerID = int(input("Enter PlayerID: "))
clubID = int(input("Enter ClubID: "))

playerDB = "Player Databases/" + str(playerID) + ".db"

###############################################################################
# Main

print ""

createDirectory("Player Databases")

createDatabase(playerID, wipe)

if fetch:

	fetchPlayerInfo(playerID, clubID)

	seasonList = getSeasonList(playerID,clubID)

	print "Seasons found: " + str(len(seasonList))

	matchList = getMatchList(playerID, clubID, seasonList)

	#print matchList

	print "Matches found: " + str(len(matchList))

	populateDatabaseFirstPass(playerID,clubID,seasonList)

	#populateDatabaseSecondPass(playerID,clubID,matchList)

	#populateDatabaseThirdPass(playerID,clubID,matchList)

if analysis:

	stats_Overall(playerID)

	stats_Season(playerID, clubID)
