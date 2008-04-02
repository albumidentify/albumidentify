#
# toc.py
# Functions to deal with parsing CD TOCs
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

class Track:
	def __init__(self, tracknum):
		self.track_num = tracknum
		self.track_start = 0
		self.track_length = 0
		self.track_offset = 0

	def __repr__(self):
		return ("<track %i, start %i, length %i, offset %i, end %i>" % (self.tracknum, self.track_start,
												self.track_length, self.track_offset, self.track_start + self.track_length))

def timestamp_to_sectors(ts):
	""" Takes a TOC timestamp of the form "MM:SS:ss" where MM == minutes,
	    SS == seconds and ss == sectors, and converts to sectors.
	"""
	if ts == "0":
		return 0
	parts = ts.split(":")
	minutes = int(parts[0])
	seconds = int(parts[1])
	sectors = int(parts[2])
	return (((minutes * 60) + seconds) * 75) + sectors

def parse_text_toc(filename):
	""" Parse a cdrdao-style TOC and return a list of Track objects """
	f = open(filename, 'r')

	type = f.readline()
	if not type.startswith("CD_DA"):
		raise Exception("Unsupported disc type: " + type)

	tracks = []
	curtrack = None
	for line in f.readlines():
		parts = line.split()
		if line.startswith("// Track"):
			if curtrack is not None:
				tracks.append(curtrack)
			curtrack = Track(int(parts[2]))
		elif line.startswith("FILE"):
			curtrack.track_start = timestamp_to_sectors(parts[2]) + 150
			curtrack.track_length = timestamp_to_sectors(parts[3])
		elif line.startswith("START"):
			curtrack.track_offset = timestamp_to_sectors(parts[1])

	f.close()
	tracks.append(curtrack)
	return tracks

def tracks_to_offsets(tracks):
	""" Take a list of Track objects and return a tuple of the form:
			(first_track_num, last_track_num, offsets)
		Where offsets is a list of track offsets. The first item of the list
		if the offset of the leadout track.
	"""
	offsets = []
	last_track = tracks[len(tracks)-1]

	first_track_num = tracks[0].track_num
	last_track_num = last_track.track_num

	offsets.append(last_track.track_start + last_track.track_length)
	for track in tracks:
		offsets.append(track.track_start + track.track_offset)

	return (first_track_num, last_track_num, offsets)


####################
# cdrecord-style tocs. This code isn't really needed anymore.
#   the parse_cdrecord_toc() function doesn't quite work the same as the
#   parse_text_toc() function in that it directly returns the tuple, rather
#   than returning a list of Track objects.

def __parse_cdrecord_toc_track_line(line):
	l = {}
	parts = line.split()
	if parts[0] == "lout":
		l['track'] = "lout"
	else:
		l['track'] = int(parts[0])
	l['start_sector'] = int(parts[2])
	l['start_time'] = parts[5]
	l['control'] = int(parts[9])
	l['mode'] = int(parts[11])
	if l['mode'] != -1 and l['mode'] != 0:
		raise Exception("Unsupported disc type")
	return l

def parse_cdrecord_toc(tocfilename):
	""" Opens a cdrecord toc file and parses out the track numbers and
		track offsets, adjusting for the pre-gap of track 1.
		Returns a tuple consisting of (first_track_num, last_track_num, offsets)
	"""
	f = open(tocfilename, 'r')
	first_track_num = 0
	last_track_num = 0
	offsets = []
	tracks = {}
	for line in f.readlines():
		if line.startswith("first"):
			parts = line.split(' ')
			first_track_num = int(parts[1])
			last_track_num = int(parts[3])
		elif line.startswith("track"):
			l = __parse_cdrecord_toc_track_line(line[6:])
			l['start_sector'] = l['start_sector'] + 150
			tracks[l['track']] = l
	f.close()
	offsets.append(tracks['lout']['start_sector'])
	for i in range(first_track_num, last_track_num + 1):
		offsets.append(tracks[i]['start_sector'])

	return (first_track_num, last_track_num, offsets)


