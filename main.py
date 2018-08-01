###############################################################################
# myCricket.py - A scraper and a stats analyzer for myCricket 
# jamesj223

###############################################################################
# Imports

import os, requests, bs4, re, sqlite3, time

###############################################################################
# User Input

debug = True

# Get Player ID
playerID = int(input("Enter PlayerID: "))
clubID = int(input("Enter ClubID: "))

playerDB = "Player Databases/" + str(playerID) + ".db"

###############################################################################
# DB Schemas

playerInfoTable = "PlayerInfo (PlayerID INTEGER PRIMARY KEY, FirstName TEXT, LastName TEXT, NumMatches INTEGER)"

matchesTable = "Matches (MatchID INTEGER PRIMARY KEY, Season TEXT, Round INTEGER, Grade TEXT, Opponent TEXT, Ground TEXT, HomeOrAway TEXT, WinOrLoss TEXT, FullScorecardAvailable TEXT)"#, TeamMates)"

battingTable = "Batting (BattingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Innings INTEGER, Runs INTEGER, Position INTEGER, HowDismissed TEXT, Fours INTEGER, Sixes INTEGER, TeamWicketsLost INTEGER, TeamScore INTEGER, TeamOversFaced TEXT, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

bowlingTable = "Bowling (BowlingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Innings INTEGER, Overs TEXT, Wickets INTEGER, Runs INTEGER, Maidens INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

fieldingTable = "Fielding (FieldingInningsID INTEGER PRIMARY KEY, MatchID INTEGER, Catches INTEGER, RunOuts INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID))"

teamMatesTable = "TeamMates (PlayerID INTEGER PRIMARY KEY, FirstName TEXT, LastName Text)"

teamMatesMatchesTable = "TeamMatesMatches (MatchID INTEGER, PlayerID INTEGER, FOREIGN KEY (MatchID) REFERENCES Matches(MatchID), FOREIGN KEY (PlayerID) REFERENCES TeamMates(PlayerID))"

unknown = "Unknown"

###############################################################################
# Functions

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
	
	# If Database doesnt exist, create one.
	if not os.path.exists(playerDB):
		open(playerDB, 'a').close()

	conn = sqlite3.connect(playerDB)

	c = conn.cursor()

	if wipe:
		c.execute("DROP TABLE IF EXISTS PlayerInfo;")
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
def fetchPlayerInfo(playerID, clubID):

	soup = getSoup( "http://mycricket.cricket.com.au/common/pages/public/rv/cricket/viewplayer.aspx?save=0&clubid="+str(clubID)+"&entityid="+str(clubID)+"&playerid="+str(playerID) )

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
	conn = sqlite3.connect(playerDB)
	c = conn.cursor()
	c.execute("INSERT OR IGNORE INTO PlayerInfo (PlayerID, FirstName, LastName, NumMatches) values (?,?,?,?)", (playerID, firstName, lastName, numMatches) )
	c.execute("UPDATE PlayerInfo SET NumMatches=? WHERE PlayerID = ?", (numMatches, playerID) ) 
	conn.commit()

	if debug:
		print "PlayerInfo Database Updated."

	conn.close()

# Fetches the list of all of the season a player has played for a club
def getSeasonList(playerID, clubID):

	soup = getSoup( "http://mycricket.cricket.com.au/cricket/reports/playercareerbatting.asp?save=0&playerid="+str(playerID)+"&eid="+str(clubID) )

	childList = soup.find_all('td', string="ALL GRADES")

	seasonList = []

	for child in childList:
		parent = child.find_parent("tr")['onclick']
		#print parent
		front = 10 + len( str(playerID) ) + len( str( clubID) )
		end = 15
		seasonID = parent[front:len(parent)-end]
		#print seasonID
		seasonList.append(seasonID)

	return seasonList

# Fetches the list of all matches a player has played, given a list of seasons 
def getMatchList(playerID,clubID, seasonList):

	matchList = []

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
		time.sleep(5)

	return matchList

# First pass at populating the player database. Fetches as much information as possible without opening individual scorecard views
def populateDatabaseFirstPass(playerID, clubID, seasonList):

	matchList = []

	battingInningsID = 1#select (count *) from Batting ? 

	print ""

	# For each season in list, get list of matches, and add them to matchList
	for season in seasonList:

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


			else:
				innings = 1

				Round = tds[1].string

				opponent = tds[3].select("span")[0].string

				ground = unknown

				homeOrAway = unknown
				regex = re.findall( r'(red|green)', tds[4].select("img")[0]["src"] )[0]
				if regex == "green":
					homeOrAway = "Home"
				elif regex == "red":
					homeOrAway = "Away"

				winOrLoss = unknown
				
				fullScorecardAvailable = unknown

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
				query = "INSERT INTO Matches (MatchID, Season, Round, Grade, Opponent, Ground, HomeOrAway, WinOrLoss, FullScorecardAvailable ) VALUES (?,?,?,?,?,?,?,null,null)"#?,?)"
				values = (matchID, seasonText, Round, grade, opponent, ground, homeOrAway)#, winOrLoss, fullScorecardAvailable)
				
				dbQuery(playerDB,query,values)

				matchList.append(matchID)


				# If Debug Print Match Info 
				if debug:

					#Match Info
					print "MatchID: " + str(matchID)
					print "Season: " + seasonText
					print "Round: " + str(Round)
					print "Grade: " + str(grade)
					print "Innings: " + str(innings)# Not in Matches Table
					print "Opponent: " + opponent
					print "Ground: " + ground
					print "HomeOrAway: " + homeOrAway
					print "WinOrLoss: " + winOrLoss
					print "FullScorecardAvailable: " + fullScorecardAvailable

			#Batting
			if batting[0].string.encode("ascii", "ignore") != '':

				query = "INSERT INTO Batting (BattingInningsID, MatchID, Innings, Runs, Position, HowDismissed, Fours, Sixes, TeamWicketsLost, TeamScore, TeamOversFaced) VALUES (?,?,?,?,?,?,null,null,null,null,null)"
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
				'seasonText': seasonText,
				'Round': Round,
				'grade': grade,
				'opponent': opponent,
				'ground': ground,
				'homeOrAway': homeOrAway,
				'winOrLoss': winOrLoss,
				'fullScorecardAvailable': fullScorecardAvailable
			}

			print ""

		time.sleep(5)

# Second pass at populating the player database. Goes through scorecards (if available) for all games in matchList
def populateDatabaseSecondPass(playerID, clubID, matchList):
	print "TODO"

# Third pass at populating the player database. Specifically concerning the TeamMates and TeamMatesMatches tables.
def populateDatabaseThirdPass(playerID, clubID, matchList):
	print "TODO"



###############################################################################
# Main

wipe = False # TODO Determine whether to wipe based on schema change or not
fetch = True # TODO Determine whether to fetch based on whether numMatches on myCricket == numMatches in PlayerInfo
analysis = True

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

	#printHighLevelBattingSummary(playerID)

	matchesDBFetch = dbQuery(playerDB,"select * from Matches")

	print "Num Matches in DB: " + str( len( matchesDBFetch ) )

	print "Printing Matches table:"
	for thing in matchesDBFetch:
		print thing

	battingDBFetch = dbQuery(playerDB,"select * from Batting")

	print "Num Batting Innings in DB: " + str( len( battingDBFetch ) )

	print "Printing Batting table:"
	for thing in battingDBFetch:
		print thing
