###############################################################################
# myCricket.py - A scraper and a stats analyzer for myCricket 
# jamesj223

###############################################################################
# Imports

from __future__ import division

import os, requests, bs4, re, sqlite3, time

from numpy import median

###############################################################################
# DB Schemas

playerInfoTable = "PlayerInfo (PlayerID INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, NumMatches INTEGER)"

clubsTable = "Clubs (ClubID INTEGER PRIMARY KEY, ClubName TEXT)"

matchesTable = "Matches (MatchID INTEGER PRIMARY KEY, ClubID INTEGER, Season TEXT, Round INTEGER, Grade TEXT, Opponent TEXT, Ground TEXT, HomeOrAway TEXT, WinOrLoss TEXT, FullScorecardAvailable TEXT, Captain TEXT, FOREIGN KEY (ClubID) REFERENCES Clubs(ClubID))"

battingTable = "Batting (BattingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Innings INTEGER, Runs INTEGER, Position INTEGER, HowDismissed TEXT, Fours INTEGER, Sixes INTEGER, TeamWicketsLost INTEGER, TeamScore INTEGER, TeamOversFaced TEXT, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

bowlingTable = "Bowling (BowlingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Innings INTEGER, Overs TEXT, Wickets INTEGER, Runs INTEGER, Maidens INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

fieldingTable = "Fielding (FieldingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Catches INTEGER, RunOuts INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"



# Not Yet Implemented

teamMatesTable = "TeamMates (PlayerID INTEGER PRIMARY KEY, FirstName TEXT, LastName Text)"

teamMatesMatchesTable = "TeamMatesMatches (MatchID INTEGER, PlayerID INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID), FOREIGN KEY (PlayerID) REFERENCES TeamMates(PlayerID))"

unknown = "Unknown"

###############################################################################
# Functions

debug = False

### Phase 1 - Fetch data from MyCricket

# Creates a directory d if it doesnt already exist
def createDirectory(d,parent=None):
	if not os.path.exists(d):
		os.mkdir(d)

# Fetches a url using requests and then extracts the 'soup' for the loaded page
def getSoup(url):

	a = url

	if debug:
			print('Downloading page')# %s' % url)

	res = requests.get(a)
	res.raise_for_status()

	if debug:
		print "Returned status code: " + str( res )

	soup = bs4.BeautifulSoup(res.text, "html.parser")

	return soup

# Creates the player database. Specifically the PlayerInfo, Matches, Batting, Bowling and Fielding tables
def createDatabase(playerID, wipe=False):
	
	playerDB = "Player Databases/" + str(playerID) + ".db"

	# If Database doesnt exist, create one.
	if not os.path.exists(playerDB):
		open(playerDB, 'a').close()

	conn = sqlite3.connect(playerDB)

	c = conn.cursor()

	if wipe:
		c.execute("DROP TABLE IF EXISTS PlayerInfo;")
		c.execute("DROP TABLE IF EXISTS Clubs;")
		c.execute("DROP TABLE IF EXISTS Matches;")
		c.execute("DROP TABLE IF EXISTS Batting;")
		c.execute("DROP TABLE IF EXISTS Bowling;")
		c.execute("DROP TABLE IF EXISTS Fielding;")
		conn.commit()

		if debug:
			print "Dropping all existing tables."

	# PlayerInfo

	c.execute("CREATE TABLE IF NOT EXISTS " + playerInfoTable + ";")
	conn.commit()
	if debug:
		print "Created table: PlayerInfo" 

	c.execute("CREATE TABLE IF NOT EXISTS " + clubsTable + ";")
	conn.commit()
	if debug:
		print "Created table: Clubs" 

	# Matches - Teammates Extracted out into Join Table?
	c.execute("CREATE TABLE IF NOT EXISTS " + matchesTable + ";")
	conn.commit()
	if debug:
		print "Created table: Matches" 

	# Batting
	c.execute("CREATE TABLE IF NOT EXISTS " + battingTable + ";")
	conn.commit()
	if debug:
		print "Created table: Batting" 

	# Bowling
	c.execute("CREATE TABLE IF NOT EXISTS " + bowlingTable + ";")
	conn.commit()
	if debug:
		print "Created table: Bowling" 

	# Fielding
	c.execute("CREATE TABLE IF NOT EXISTS " + fieldingTable + ";")
	conn.commit()
	if debug:
		print "Created table: Fielding" 

	conn.close()

# Runs the supplied query against the specified database
def dbQuery(database, query, values=() ):
	conn = sqlite3.connect(database)
	c = conn.cursor()
	if len(values) > 0:
		c.execute(query,values)
	elif len(values) == 0:
		c.execute(query)
	else:
		if debug:
			print "Incorrect arguement for 'values' in function dbQuery"
	conn.commit()
	returnValue = c.fetchall()
	if debug:
		print str(c.rowcount) + " rows affected"
	conn.close()

	return returnValue

# Fetches player info, and populates the PlayerInfo table
def fetchPlayerInfo(playerID):

	soup = getSoup( "http://mycricket.cricket.com.au/common/pages/public/rv/cricket/viewplayer.aspx?playerid="+str(playerID) )

	# Get Player Name
	fullName = soup.select("#lblPlayerName")[0].text
	
	firstName = fullName.split(" ")[0]
	lastName = fullName.split(" ")[1]

	if debug:
		print "First Name: " + firstName
		print "Last Name: " + lastName

	# Get Number of Matches Played
	numMatches = int(soup.select("#lblMatches")[0].text)

	if debug:
		print "Matches played: " + str(numMatches)

	# Insert into PlayerInfo table
	playerDB = "Player Databases/" + str(playerID) + ".db"
			
	query = "INSERT OR IGNORE INTO PlayerInfo (PlayerID, FirstName, LastName, NumMatches) VALUES (?,?,?,?)"
	values = (playerID, firstName, lastName, numMatches)
	dbQuery(playerDB,query,values)

	query = "UPDATE PlayerInfo SET NumMatches=? WHERE PlayerID = ?"
	values = (numMatches, playerID)
	dbQuery(playerDB,query,values)

	if debug:
		print "PlayerInfo Table Updated."

	# Get clubs
	clubList = soup.select('#ddlOtherClubs > option')#[0].value
	for thing in clubList:
		query = "INSERT OR IGNORE INTO Clubs (ClubID, ClubName) VALUES (?,?)"
		values = (thing['value'], thing.text)
		dbQuery(playerDB,query,values)

# Returns the list of clubIDs for clubs that a player has played for
def getClubList(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	clubList = dbQuery(playerDB, "SELECT * from Clubs")

	return clubList


# Fetches the list of all of the season a player has played for a club
def getSeasonList(playerID):#, clubID):

	seasonList = []

	clubList = getClubList(playerID)

	for club in clubList:

		clubID = club[0]

		soup = getSoup( "http://mycricket.cricket.com.au/cricket/reports/playercareerbatting.asp?save=0&playerid="+str(playerID)+"&eid="+str(clubID) )

		childList = soup.find_all('td', string="ALL GRADES")

		for child in childList:
			parent = child.find_parent("tr")['onclick']
			#print parent
			front = 10 + len( str(playerID) ) + len( str( clubID) )
			end = 15
			seasonID = parent[front:len(parent)-end]
			#print seasonID
			if seasonID not in seasonList:
				seasonList.append(seasonID)

	return seasonList

# Fetches the list of all matches a player has played, given a list of seasons
def getMatchList(playerID, clubID, seasonList):
# Replace this with SQL? populateDBFirstPast is already getting all the MatchIDs
# Just fetch them that way instead.

	matchList = []

	clubList = getClubList(playerID)

	# For each season in list, get list of matches, and add them to matchList
	for season in seasonList:

		soup = getSoup( "http://mycricket.cricket.com.au/common/pages/public/rv/cricket/viewplayer.aspx?save=0&playerID="+str(playerID)+"&eID="+str(clubID)+"&entityID="+str(clubID)+"&seasonID="+str(season) )

		matches = soup.select("tr.row")#find_all("tr", class_="row")
		for match in matches:
			matchOnclickText = match['onclick']
			#print matchOnclickText
			matchID = matchOnclickText[7:len(str(matchOnclickText))-2]
			#print matchID
			if matchID not in matchList:
				matchList.append(matchID)

		# Courtesy sleep, to reduce load on myCricket. Probs re-enable before release?
		#time.sleep(5)

	return matchList

# First pass at populating the player database. Fetches as much information as possible without opening individual scorecard views
def populateDatabaseFirstPass(playerID):

	seasonList = getSeasonList(playerID)

	playerDB = "Player Databases/" + str(playerID) + ".db"

	matchList = []

	battingInningsID = 1#select (count *) from Batting ? 

	clubList = getClubList(playerID)

	# For each season in list, get list of matches, and add them to matchList
	for season in seasonList:

		for club in clubList:

			clubID = str(club[0])

			soup = getSoup( "http://mycricket.cricket.com.au/common/pages/public/rv/cricket/viewplayer.aspx?save=0&playerID="+str(playerID)+"&eID="+str(clubID)+"&entityID="+str(clubID)+"&seasonID="+str(season) )
	
			seasonText = soup.select("select#rvsbSeason_lc > option[selected='selected']")[0].string
			#print seasonText
	
			matches = soup.select("tr.row")#find_all("tr", class_="row")
	
			prevMatchInfo = {}
			#if True:
			#	match = matches[2]
			for match in matches:
				matchOnclickText = match['onclick']
				#print matchOnclickText
				matchID = matchOnclickText[7:len(str(matchOnclickText))-2]
	
				innings = 0
	
				tds = match.select("td")
	
				superDebug = False
				if superDebug:
					print str(len(tds))
					i = 0
					for thing in tds:
						print str(i) + " : " + str(thing)
						i += 1
	
				# Fetch Match Specific Info
	
				grade = tds[0].string
	
				if grade == None:
					innings = 2
					if debug:
						print "Multi Innings Match - Fetching Previous Info"
					grade = prevMatchInfo['grade']
					Round = prevMatchInfo['Round']
					opponent = prevMatchInfo['opponent']
					ground = prevMatchInfo['ground']
					homeOrAway = prevMatchInfo['homeOrAway']
					winOrLoss = prevMatchInfo['winOrLoss']
					fullScorecardAvailable = prevMatchInfo['fullScorecardAvailable']
					captain = prevMatchInfo['captain']
	
	
				else:
					innings = 1
	
					Round = tds[1].string
	
					opponent = tds[3].select("span")[0].string.replace("'","")
	
					ground = unknown
	
					homeOrAway = unknown
					regex = re.findall( r'(red|green)', tds[4].select("img")[0]["src"] )[0]
					if regex == "green":
						homeOrAway = "Home"
					elif regex == "red":
						homeOrAway = "Away"
	
					winOrLoss = unknown
					
					fullScorecardAvailable = unknown
	
					captain = unknown
	
				# Fetch Batting Specific Info
	
				batting = match.select("td.batting")
	
				if batting[0].string.encode("ascii", "ignore") != '':
					battingRuns = int(batting[0].string)
					battingPos = int(batting[1].string)
					battingOut = batting[2].string
	
				# Fetch Bowling Specific Info
	
				bowling = match.select("td.bowling")
	
				if bowling[0].string.encode("ascii", "ignore") != '':
					
					bowlingovers = bowling[0].string
	
					temp = bowling[1].string
					if temp.encode("ascii", "ignore") != '':
						bowlingMaidens = int(temp)
					else:
						bowlingMaidens = 0
					
					temp = bowling[2].string
					if temp.encode("ascii", "ignore") != '':
						bowlingWickets = int(temp)
					else:
						bowlingWickets = 0
	
					temp = bowling[3].string
					if temp.encode("ascii", "ignore") != '':	
						bowlingRuns = int(temp)
					else:
						print "I dont think stats from this match should be included."
						bowlingRuns = 0
	
				# Fetch Fielding Specific Info
				# len fielding 5
				# Catches, CatchesWK, RunoutUnassisted, RunoutAssisted, Stumping
	
				fielding = match.select("td.fielding")
	
				### DB Inserts into various tables
				##
				# 
	
				#Matches
				if matchID not in matchList:
					# It wont be in DB so insert
					query = "INSERT OR IGNORE INTO Matches (MatchID, ClubID, Season, Round, Grade, Opponent, Ground, HomeOrAway, WinOrLoss, FullScorecardAvailable, Captain ) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
					values = (matchID, clubID, seasonText, Round, grade, opponent, ground, homeOrAway, winOrLoss, fullScorecardAvailable, captain)
					
					dbQuery(playerDB,query,values)
	
					matchList.append(matchID)
	
	
					# If Debug Print Match Info 
					if debug:
	
						#Match Info
						print "MatchID: " + str(matchID)
						print "ClubID: " + str(clubID)
						print "Season: " + seasonText
						print "Round: " + str(Round)
						print "Grade: " + str(grade)
						print "Innings: " + str(innings)# Not in Matches Table
						print "Opponent: " + opponent
						print "Ground: " + ground
						print "HomeOrAway: " + homeOrAway
						print "WinOrLoss: " + winOrLoss
						print "FullScorecardAvailable: " + fullScorecardAvailable
						print "Captain: " + captain
	
				#Batting
				if batting[0].string.encode("ascii", "ignore") != '':
	
					query = "INSERT OR IGNORE INTO Batting (BattingInningsID, MatchID, Innings, Runs, Position, HowDismissed, Fours, Sixes, TeamWicketsLost, TeamScore, TeamOversFaced) VALUES (?,?,?,?,?,?,null,null,null,null,null)"
					values = (battingInningsID, matchID, innings, battingRuns, battingPos, battingOut)#, unknown, unknown, unknown, unknown, unknown)
	
					dbQuery(playerDB,query,values)
	
					battingInningsID += 1
	
					# If Debug Print Batting/Innings Info
					if debug:
						print "Batting Figures:"
						print "\tRuns: " + str(battingRuns)
						print "\tPosition: " + str(battingPos)
						print "\tHow out: " + battingOut
	
	
				#Bowling
				if bowling[0].string.encode("ascii", "ignore") != '':
	
	
					# If Debug Print Bowling/Innings Info
					if debug:
						print "Bowling Figures:"
						print "\tOvers: " + bowlingovers
						print "\tMaidens: " + str(bowlingMaidens)
						print "\tWickets: " + str(bowlingWickets)
						print "\tRuns: " + str(bowlingRuns)
	
				#Fielding
				#if fielding[0].string.encode("ascii", "ignore") != '':
				#	print "Fielding Figures:"
	
	
	
	
				# Fetch High Level Batting, Bowling and Fielding stats
				# Insert into relevant tables.
	
	
				prevMatchInfo = {
					'matchID': matchID,
					'clubID': clubID,
					'seasonText': seasonText,
					'Round': Round,
					'grade': grade,
					'opponent': opponent,
					'ground': ground,
					'homeOrAway': homeOrAway,
					'winOrLoss': winOrLoss,
					'fullScorecardAvailable': fullScorecardAvailable,
					'captain': captain
				}
	
				#print ""
	
			# Courtesy sleep, to reduce load on myCricket. Probs re-enable before release?
			#time.sleep(5)

# Second pass at populating the player database. Goes through scorecards (if available) for all games in matchList
def populateDatabaseSecondPass(playerID):
	print "TODO"

# Third pass at populating the player database. Specifically concerning the TeamMates and TeamMatesMatches tables.
def populateDatabaseThirdPass(playerID):
	print "TODO"

### Phase 2 - Analyse data and present statistics

# Calculate and return batting stats for a list of innings
def getBattingStats(inningsList):
	headers = ("Innings", "High Score", "Not Outs", "Ducks", "25s", "50s", "100s", "Aggregate", "Average")

	# Initialise and zero all variables
	numInnings = highScore = notOuts = ducks = twentyFives = fifties = hundreds = aggregate = 0
	average = 0.0

	# Iterate over innings list
	for innings in inningsList:
		
		numInnings += 1

		if innings[3] > highScore:
			highScore = innings[3]

		if innings[5] == 'no':
			notOuts += 1

		if innings[3] == 0 and innings[5] != 'no':
			ducks += 1

		if innings[3] >= 25 and innings[3] < 50:
			twentyFives += 1

		if innings[3] >= 50 and innings[3] < 100:
			fifties += 1

		if innings[3] >= 100:
			hundreds += 1

		aggregate += innings[3]

	# Calculate Batting Average (rounded to 2 decimal places)
	try:
		rawAverage = aggregate / (numInnings - notOuts) 
	
		average = round(rawAverage, 2)
	except ZeroDivisionError:
		average = "N/A"


	# Compile stats into tuple
	stats = (numInnings, highScore, notOuts, ducks, twentyFives, fifties, hundreds, aggregate, average)

	return headers, stats

# Print function
def printStats(headers, stats):
	mode = "V"#"Horizontal"

	if mode == "H":#"Horizontal":
		if headers:
			print headers
		if stats:
			print stats

	elif mode == "V":#"Vertical":
		if headers and stats:
			for i in range(len(headers)):
				print headers[i] + ': ' + str( stats[i] )

	print ""

# Analyse all batting innings for player
def stats_Overall(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Overall Batting Summary"	

	allBattingInnings = dbQuery(playerDB,"SELECT * FROM Batting")

	# Get stats for all batting innings
	headers, stats = getBattingStats(allBattingInnings)

	# Print stats
	printStats(headers, stats)

# Batting stats by Season
def stats_Season(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Stats by Season\n"

	seasonList = dbQuery(playerDB, "SELECT DISTINCT Season FROM Matches")

	for season in seasonList:

		print season[0]

		matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Season='" + season[0] + "'")

		formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

		inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE MatchID IN " + formattedMatchList) 

		# Get stats for all batting innings for season
		headers, stats = getBattingStats(inningsList)

		# Print stats
		printStats(headers, stats)

# Batting stats by DismissalBreakdown
def stats_DismissalBreakdown(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Dismissal Breakdown\n"

	dismissalStats = dbQuery(playerDB, "SELECT HowDismissed, COUNT(*) as Count from Batting GROUP BY HowDismissed ORDER BY Count DESC")

	headers = [ str(i[0]) for i in dismissalStats ]

	stats = [ i[1] for i in dismissalStats ]

	# Replace this with better print
	# Include % of innings and % of dismissals
	printStats(headers, stats)

# Batting stats by Batting Position
def stats_Position(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Batting Position\n"

	print "Opening"
	inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE Position IN (1,2)") 
	headers, stats = getBattingStats(inningsList)
	printStats(headers, stats)

	for i in range(3,12):
		print "#" + str(i)
		inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE Position="+str(i)) 
		headers, stats = getBattingStats(inningsList)
		printStats(headers, stats)

# Batting stats by Opponent
def stats_Opponent(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Stats by Opponent\n"	

	opponentList = dbQuery(playerDB, "SELECT DISTINCT Opponent FROM Matches ORDER BY Opponent ASC")

	for opponent in opponentList:

		print opponent[0]

		matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Opponent='" + opponent[0] + "'")

		formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

		inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE MatchID IN " + formattedMatchList) 
		headers, stats = getBattingStats(inningsList)
		printStats(headers, stats)

# Batting stats by Grade
def stats_Grade(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Stats by Grade\n"	

	gradeList = dbQuery(playerDB, "SELECT DISTINCT Grade FROM Matches ORDER BY Grade ASC")

	for grade in gradeList:

		print grade[0]

		matchList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE Grade='" + grade[0] + "'")

		formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"

		inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE MatchID IN " + formattedMatchList) 
		headers, stats = getBattingStats(inningsList)
		printStats(headers, stats)

# Batting stats by HomeOrAway
def stats_HomeOrAway(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Stats by Home/Away\n"

	print "Home"
	matchList = seasonList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE HomeOrAway='Home'")
	formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"
	inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE MatchID IN " + formattedMatchList) 
	headers, stats = getBattingStats(inningsList)
	printStats(headers, stats)

	print "Away"
	matchList = seasonList = dbQuery(playerDB, "SELECT MatchID FROM Matches WHERE HomeOrAway='Away'")
	formattedMatchList = "(" + ','.join( [str( i[0] ) for i in matchList] ) + ")"
	inningsList = dbQuery(playerDB, "SELECT * FROM Batting WHERE MatchID IN " + formattedMatchList) 
	headers, stats = getBattingStats(inningsList)
	printStats(headers, stats)


# Batting stats by NohitBrohitLine
def stats_NohitBrohitLine(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Nohit/Brohit Line!\n"

	print median(dbQuery(playerDB, "SELECT Runs from Batting ORDER BY Runs ASC"))

# Batting stats by Bingo
def stats_Bingo(playerID):
	playerDB = "Player Databases/" + str(playerID) + ".db"

	print "Bingo!\n"

	bingoList = dbQuery(playerDB, "SELECT DISTINCT Runs from Batting ORDER BY Runs ASC")

	formattedBingoList = [ i[0] for i in bingoList ]

	missingNumbers = []

	for i in range( 0, formattedBingoList[-1]+1 ):
		if i not in formattedBingoList:
			missingNumbers.append(i)

	print "Hit"
	print formattedBingoList
	print "Miss"
	print missingNumbers
	print ""

	# Find next bingo number

## Need Fetch Pass 2

# Batting stats by Ground
def stats_Ground(playerID):
	print "TODO"

# Batting stats by PercentOfTeam
def stats_PercentOfTeam(playerID):
	print "TODO"

	# % of Team Runs for each game
	# Min, Max, Average

	# % of Team Overs faced for each game
	# Min, Max, Average
	# Hard/potentially impossible to calculate from MyCricket
	# FOW data doesn't have overs (when it is even there)

## Need Fetch Pass 3

# Batting stats by TeamMate
def stats_TeamMate(playerID, minGames):
	print "TODO"

## Need Additional Information

# Batting stats by Club
def stats_Club(playerID):
	print "TODO"

# Batting stats by Captain
def stats_Captain(playerID):
	print "TODO"





# Batting stats by THING
def stats_THING(playerID):
	print "TODO"
