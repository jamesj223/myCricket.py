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

	stats_Overall(playerID, "Batting")
	stats_Overall(playerID, "Bowling")

	stats_Season(playerID, "Batting")
	stats_Season(playerID, "Bowling")

	stats_Club(playerID,"Batting")
	stats_Club(playerID,"Bowling")

	stats_Opponent(playerID,"Batting")
	stats_Opponent(playerID,"Bowling")

	stats_Grade(playerID,"Batting")
	stats_Grade(playerID,"Bowling")

	stats_HomeOrAway(playerID,"Batting")
	stats_HomeOrAway(playerID,"Bowling")

	stats_Recent(playerID, "Batting", 5)
	stats_Recent(playerID, "Bowling", 5)

	# Batting Only

	stats_Batting_DismissalBreakdown(playerID)

	stats_Batting_Position(playerID)

	stats_Batting_NohitBrohitLine(playerID)
	
	stats_Batting_Bingo(playerID)

	# Bowling Only

	stats_Bowling_Workload(playerID)
