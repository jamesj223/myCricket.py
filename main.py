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

playerDB = "Player Databases/" + str(playerID) + ".db"

###############################################################################
# Main

print ""

createDirectory("Player Databases")

createDatabase(playerID, wipe)

if fetch:

	fetchPlayerInfo(playerID)

	populateDatabaseFirstPass(playerID)

	#populateDatabaseSecondPass(playerID)

	#populateDatabaseThirdPass(playerID)

if analysis:

	# Normal Stats

	stats_Overall(playerID)

	stats_Season(playerID)

	#stats_DismissalBreakdown(playerID)

	#stats_Position(playerID)

	#stats_Opponent(playerID)

	#stats_Grade(playerID)

	#stats_HomeOrAway(playerID)

	# Fun Stats

	#stats_NohitBrohitLine(playerID)
	
	#stats_Bingo(playerID)
