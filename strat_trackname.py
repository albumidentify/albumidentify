# Strategy:
#   check against all the possible releases for a track which matches the id3
#   tag name of this album
import parsemp3
import lookups
import util

def generate_track_name_possibilities(fname, fileid, possible_releases):
	"""Return all track ids matching the tracks.

	Args:
		fname: The file containing the track in question.
		track: A list of tracks to match against.
		possible_releases: Dictionary containing releases under consideration.
	
	Yields:
		All releated track_ids. Looks at all track names in the releases under
		consideration and case insensitively compares the tracks, returning any
		matches.
	"""
	if fname.lower().endswith(".flac"):
		return
	elif fname.lower().endswith(".ogg"):
		return
	try:
		mp3data = parsemp3.parsemp3(fname)
	except:
		# Parsing MP3s is a source of bugs... be robust here.
		print "Failed to parse mp3: %s" % fname
		return

	if "TIT2" not in mp3data["v2"]:
		return
	ftrackname = mp3data["v2"]["TIT2"]
	for (rid,v) in possible_releases.items():
		release = lookups.get_release_by_releaseid(rid)
		for trackind in range(len(release.tracks)):
			rtrackname = release.tracks[trackind].title

			# Don't bother if we've already found this track!
			if trackind+1 in v:
				continue

			if util.combinations(util.comp_name, rtrackname, ftrackname):
				print "Using text based comparison for track",trackind+1,`rtrackname`
				yield lookups.get_track_by_id(release.tracks[trackind].id)

