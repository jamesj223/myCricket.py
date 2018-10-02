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

	## Normal Stats

	#stats_Batting_Overall(playerID)

	#stats_Batting_Season(playerID)

	#stats_Batting_Club(playerID)

	#stats_Batting_DismissalBreakdown(playerID)

	#stats_Batting_Position(playerID)

	#stats_Batting_Opponent(playerID)

	#stats_Batting_Grade(playerID)

	#stats_Batting_HomeOrAway(playerID)

	## Fun Stats

	#stats_Batting_NohitBrohitLine(playerID)
	
	#stats_Batting_Bingo(playerID)

	## Bowling Stats

	#stats_Bowling_Overall(playerID)

	#stats_Bowling_Workload(playerID)

	## Higher Level Reports

	stats_Batting_Recent(playerID, 5)

	stats_Bowling_Recent(playerID, 5)
