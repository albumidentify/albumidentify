# Strategy:
#   check against all the possible releases for a track which matches the id3
#   tag name of this album
import lookups
import util

def generate_track_name_possibilities(file, fileid, possible_releases):
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
	ftrackname = file.getMDTrackTitle()
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

