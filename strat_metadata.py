# Strategy:
#  Looking at id3 tags, try and guess a track_id
import lookups
import util

def flatten(x):
	for i in x:
		for j in i:
			yield j

def generate_from_metadata(file, num_tracks):
	"""Return track id's by looking up the name on music brainz

	Args:
		fname: The file containing the track in question.
	
	Yields:
		A set of track_id, by querying based on id3 tags
	"""
	album = file.getMDAlbumTitle()
	title = file.getMDTrackTitle()
	artist = file.getMDTrackArtist()
	if album is None or title is None or artist is None:
		return # Can't get metadata
	
	util.update_progress("Searching albums by text lookup: "+`album`+" "+`artist`)
	for i in flatten(util.combinations(lookups.get_releases_by_cdtext,album, artist, num_tracks)):
		release = lookups.get_release_by_releaseid(i.release.id)
		util.update_progress("Trying "+release.title+" by text lookup")
		for trackind in range(len(release.tracks)):
			rtrackname = release.tracks[trackind].title

			if util.comp_name(rtrackname,title):
				print "Using album based text comparison for",artist,album,"'s track",trackind+1,`rtrackname`
				yield lookups.get_track_by_id(release.tracks[trackind].id)

