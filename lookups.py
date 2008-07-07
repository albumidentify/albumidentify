import musicbrainz2.webservice as ws
import time

lastwsquery = time.time()

def waitforws(cb):
	global lastwsquery
	if time.time()-lastwsquery<2:
		wait=2-(time.time()-lastwsquery)
		time.sleep(wait)
	ret=cb()
	lastwsquery=time.time()
	return ret


def get_tracks_by_puid(puid):
	""" Lookup a list of musicbrainz tracks by PUID. Returns a list of Track
	objects. """ 
	q = ws.Query()
	filter = ws.TrackFilter(puid=puid)
	results = []
	rs = waitforws(lambda :q.getTracks(filter=filter))
	for r in rs:
		results.append(r.getTrack())
	return results

def get_track_by_id(id):
	q = flacnamer.ws.Query()
	results = []
	includes = flacnamer.waitforws(lambda :flacnamer.ws.TrackIncludes(artist=True, releases=True, puids=True))
	t = q.getTrackById(id_ = id, include = includes)
	return t

release_by_releaseid_cache={}
def get_release_by_releaseid(releaseid):
	""" Given a musicbrainz release-id, fetch the release from musicbrainz. """
	global release_by_releaseid_cache
	if releaseid not in release_by_releaseid_cache:
		q = ws.Query()
		includes = waitforws(lambda :ws.ReleaseIncludes(artist=True, counts=True, tracks=True, releaseEvents=True,
										urlRelations=True))
		release_by_releaseid_cache[releaseid]=q.getReleaseById(id_ = releaseid, include=includes)
	return release_by_releaseid_cache[releaseid]

def track_number(tracks, trackname):
	""" Lookup trackname in a list of tracks and return the track number
	(indexed starting at 1) """
	tracknum = 1
	for t in tracks:
		if t.title == trackname:
			return tracknum
		tracknum += 1
	return -1

def get_track_artist_for_track(track):
	""" Returns the musicbrainz Artist object for the given track. This may
		require a webservice lookup
	"""
	if track.artist is not None:
		return track.artist

	q = ws.Query()
	includes = ws.TrackIncludes(artist = True)
	t = lookups.waitforws(lambda :q.getTrackById(track.id, includes))

	if t is not None:
		return t.artist

def get_all_discs_in_album(disc, albumname = None): 
	""" Given a disc, talk to musicbrainz to see how many discs are in the
	release.  Return a list of releases which correspond to all of the discs in
	this release. Note that there is an easier way to accomplish this using a
	newer version of python-musicbrainz2 which allows for Lucene searching in
	the Filter objects, so we can search directly by ASIN, which would be
	perfect.  For now though we need to do fuzzy matching on release title and
	album artist and then count how many resulting releases share the asin with
	the disc we have been given.  """

	releases = []

	if albumname is None:
		(albumname, discnumber, disctitle) = parse_album_name(disc.album)
	filter = ws.ReleaseFilter(title=albumname, artistName=disc.artist)
	q = ws.Query()
	rels = lookups.waitforws(lambda :q.getReleases(filter))

	for rel in rels:
		r = rel.getRelease()
		# Releases can have multiple ASINs, so we need to get the entire list
		# and check them all. Pain.
		includes = ws.ReleaseIncludes(artist=True, urlRelations = True)
		release = q.getReleaseById(r.id, includes)
		time.sleep(1)
		for relation in release.getRelations():
			if relation.getType().find("AmazonAsin") != -1:
				asin = relation.getTargetId().split("/")[-1].strip()
				if asin == disc.asin:
					releases.append(release)
	return releases

	return None

