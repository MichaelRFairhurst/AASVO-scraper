from lxml import html
import requests
import datetime
import glob

class Observation:
	"""This holds the basic data that we are going to use in an observation"""

	def __init__(self, julianDate, calendarDate, magnitude, error, filter, observer):
		if error == u'\u2014': # - represents...none? unknown?
			error = 0

		self.julianDate = float(julianDate)
		self.calendarDate = str(calendarDate).strip()
		self.magnitude = float(magnitude)
		self.error = float(error)
		self.filter = str(filter).strip()
		self.observer = str(observer).strip()

	def cmp(self, other):
		"""Sort by date DESC and observer ASC"""

		if self.julianDate < other.julianDate:
			return 1
		if self.julianDate > other.julianDate:
			return -1
		if self.observer < other.observer:
			return -1
		if self.observer > other.observer:
			return 1
		return 0

	def toString(self):
		return "%f,%s,%f,%f,%s,%s" % (self.julianDate, self.calendarDate, self.magnitude, self.error, self.filter, self.observer);

	def equals(self, other):
		return self.julianDate == other.julianDate and self.observer == other.observer

def collectCurrentObservations():
	"""Scrape directly from AASVO to get their observations into a sorted array"""
	hasNext = True
	arr = []

	pageNum = 1

	while hasNext:
		print 'fetching page %d' % pageNum
		page = requests.get('https://www.aavso.org/apps/webobs/results/?star=KIC+8462852&page=%d' % pageNum)
		tree = html.fromstring(page.content)

		julianDates = tree.xpath('//tr[contains(@class,"obs")]/td[3]/text()')
		calendarDates = tree.xpath('//tr[contains(@class,"obs")]/td[4]/text()')
		magnitudes = tree.xpath('//tr[contains(@class,"obs")]/td[5]/a/text()')
		errors = tree.xpath('//tr[contains(@class,"obs")]/td[6]/text()')
		filters = tree.xpath('//tr[contains(@class,"obs")]/td[7]/text()')
		observers = tree.xpath('//tr[contains(@class,"obs")]/td[8]/text()')

		for i in range(0, len(julianDates)):
			arr.append(Observation(julianDates[i], calendarDates[i], magnitudes[i], errors[i], filters[i], observers[i]))

		hasNext = tree.xpath('//text() = \'Next\'')

		pageNum += 1

	# Its possible that items were added as we paged, introducing duplicates
	return removeDuplicateObservations(arr)

def sortObservations(arr):
	arr.sort(lambda a, b: a.cmp(b))

def removeDuplicateObservations(arr):
	"""Take the first item as the 'standard,' and compare it to subsequent items, saving unique items while making them the new 'standard'"""
	if len(arr) == 0:
		return arr

	# sort to find duplicates without O(n^2) complexity
	sortObservations(arr)

	# the first one is always unique. And we know by now that we have one
	b = 0
	standard = arr[b]
	unique = [standard]

	# now which others are unique? Start at index 1, compare to the stardard
	for i in range(1, len(arr)):
		if not arr[i].equals(standard):
			# Its unique! Lets save it and note it our new standard
			standard = arr[i]
			unique.append(standard)

	return unique

def writeObservationsByFilename(fname, arr):
	"""Given a filename, write out an array of observations in CSV format"""
	with open(fname, 'w') as f:
		for obs in arr:
			f.write("%s\n" % obs.toString())

def listMasters():
	"""List the files representing a complete latest copy of what AASVO hosted at a moment in time. We can diff these to find additions later"""
	fnames = sorted(glob.glob('./MASTER*.csv'))
	fnames.reverse()
	return fnames

def getLatestMasterCopy():
	"""Find and read out the newest master copy of AASVO, parsing the CSV insto Observation objects"""
	fnames = listMasters()
	if len(fnames) > 0:
		with open(fnames[0]) as f:
			return readObservationsFromFile(f)

	return []

def readObservationsFromFile(f):
	"""Read a CSV file into an array of Observations"""
	arr = []

	for line in f.readlines():
		vals = line.split(',');
		arr.append(Observation(vals[0], vals[1], vals[2], vals[3], vals[4], vals[5]))

	return arr

def writeObservations(prefix, now, arr):
	"""Create a file named after the specified prefix and date, then write out an observation to it as a CSV"""
	writeObservationsByFilename(prefix + now.strftime('%Y-%m-%d_%H:%M') + '.csv', arr)

def findNewObservations(previous, next):
	"""Perform a sort of merge sort on the previous and new master copies of AASVO, finding the differences, and returning them in order"""
	b = 0
	new = []

	for i in range(0, len(next)):
		if b >= len(previous):
			print "Found new record at the end - " + next[i].toString()
			new.append(next[i])
			continue

		if previous[b].julianDate < next[i].julianDate or (previous[b].julianDate == next[i].julianDate and previous[b].observer != next[i].observer):
			print "Found new record - " + next[i].toString()
			# This record is newer and/or from the same time but a new observer
			new.append(next[i])
		else:
			# This new record is that previous record. We won't see that previous record again in
			# our new set, so increment this.
			b += 1

	return new

##
# Now we actually do it all.
##

print 'Getting the previous "Master Copy" of AASVO\'s records'
previousMaster = getLatestMasterCopy()
print 'Getting the current "Master Copy" of AASVO\'s records'
nextMaster = collectCurrentObservations()
print 'Finding the ones that were added since last check'
additions = findNewObservations(previousMaster, nextMaster)

now = datetime.datetime.now()
print 'Saving the new master'
writeObservations("MASTER", now, nextMaster)
print 'Saving the additions'
writeObservations("ADDED", now, additions)
print 'Done!'
