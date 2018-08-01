# myCricket.py
A scraper and a stats analyzer for MyCricket 

2 parts:
  1) Fetch data from MyCricket
  2) Analyse data.

The eventual goal being to put in a MyCricket player ID, and have it spit out a bunch of interesting/useful statistics.

More advanced batting stats than MyCricket provides itself, such as:
  by Opposition
  by Ground
  by batting position
  Average % of team score
 
  and more! Maybe...
 
 And fun stats such as:
  nohit/brohit line
  score bingo
  Batting average when playing with certain teammates
  
Currently, it fetches as much data as it can from the season view, without clicking in to individual match scorecards.

Quite a bit still to do, including:
  Fetch more detailed data from individual scorecards
  
Also want to clean up/restructure the code a bit, and potentially rewrite the scraping stuff to use Scrapy library.

and argparse and logging.
