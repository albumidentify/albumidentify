# Strategy:
#  Looking at id3 tags, try and guess a track_id
import parsemp3
import lookups
import util

def generate_from_metadata(fname, num_tracks):
	"""Return track id's by looking up the name on music brainz

	Args:
		fname: The file containing the track in question.
	
	Yields:
		A set of track_id, by querying based on id3 tags
	"""
	if fname.endswith(".mp3"):
		md = parsemp3.parsemp3(fname)
		if "TALB" in md["v2"]:
			album = md["v2"]["TALB"]
		else:
			return # Give up
		if "TIT2" in md["v2"]:
			title = md["v2"]["TIT2"]
		else:
			return # Give up
		if "TPE1" in md["v2"]:
			artist = md["v2"]["TPE1"]
		else:
			return # Give up
	else:
		return # Can't get the title/artist
	
	util.update_progress("Searching by text lookup: "+`album`+" "+`artist`)
	for i in util.combinations(lookups.get_releases_by_cdtext,album, artist, num_tracks):
		release = lookups.get_release_by_releaseid(i.release.id)
		util.update_progress("Trying "+release.title+" by text lookup")
		for trackind in range(len(release.tracks)):
			rtrackname = release.tracks[trackind].title

			if util.comp_name(rtrackname,title):
				print "Using album based text comparison for",artist,album,"'s track",trackind+1,`rtrackname`
				yield lookups.get_track_by_id(release.tracks[trackind].id)

