# AASVO-scraper
Helper tool for the Penn State team to gather light curve data from AASVO on the star KIC 8462852 

To install, simply make sure you have python (tested with version 2.7) and then run

`pip install lxml`

On my system (fedora) I had to install these packages too: libxml2-devel, libxslt-devel, python-devel.

Now you can just run

`python scrape.py`

and you'll find two new files:
- `MASTER2015-11-12_12:00.csv` : the latest contents of AASVO's database
- `ADDED2015-11-12_12:00.csv` : the additions since last run

Content is a CSV with values: julianDate, calendarDate, magnitude, error, filter, observer
