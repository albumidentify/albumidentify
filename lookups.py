import musicbrainz2.webservice as ws
import time
import amazon4
import re
import pickle
import os
import atexit
import shelve

AMAZON_LICENSE_KEY='1WQQTEA14HEA9AERDMG2'

lastwsquery = time.time()

memocache={}

# Make sure we write it out every so often

def memoify(func):
	def memoify(*args,**kwargs):
		if func.__name__ not in memocache:
                        if not os.path.isdir(os.path.expanduser("~/.mbcache/")):
                                os.mkdir(os.path.expanduser("~/.mbcache/"))
			memocache[func.__name__]=shelve.open(os.path.expanduser("~/.mbcache/"+func.__name__),"c")
		key=pickle.dumps((args,kwargs))
		if key not in memocache[func.__name__]:
			memocache[func.__name__][key]=func(*args,**kwargs)
			memocache[func.__name__].sync()

		return memocache[func.__name__][key]
	return memoify

def delayed(func):
	"Decorator to make sure a function isn't called more often than once every 2 seconds. used to space webservice calls"
	def delay(*args,**kwargs):
		global lastwsquery
		if time.time()-lastwsquery<2:
			wait=2-(time.time()-lastwsquery)
			time.sleep(wait)
		ret=func(*args,**kwargs)
		lastwsquery=time.time()
		return ret
	return delay
		
	

@memoify
@delayed
def get_tracks_by_puid(puid):
	""" Lookup a list of musicbrainz tracks by PUID. Returns a list of Track
	objects. """ 
	q = ws.Query()
	filter = ws.TrackFilter(puid=puid)
	results = []
	rs = q.getTracks(filter=filter)
	for r in rs:
		results.append(r.getTrack())
	return results

@memoify
@delayed
def get_track_by_id(id):
	q = ws.Query()
	results = []
	includes = ws.TrackIncludes(artist=True, releases=True, puids=True)
	t = q.getTrackById(id_ = id, include = includes)
	return t

@memoify
@delayed
def get_release_by_releaseid(releaseid):
	""" Given a musicbrainz release-id, fetch the release from musicbrainz. """
	q = ws.Query()
	includes = ws.ReleaseIncludes(artist=True, counts=True, tracks=True, releaseEvents=True, urlRelations=True)
	return q.getReleaseById(id_ = releaseid, include=includes)

@memoify
@delayed
def get_releases_by_cdtext(title, performer, num_tracks):
	""" Given the performer, title and number of tracks on a disc,
	lookup the release in musicbrainz. This method returns a list of possible
	results, or the empty list if there were no matches. """

	q = ws.Query()
	filter = ws.ReleaseFilter(title=title, artistName=performer)
	rels = q.getReleases(filter=filter)
	
	# Filter out of the list releases with a different number of tracks to the
	# Disc.
        return [r for r in rels if len(get_release_by_releaseid(r.release.id).getTracks()) == num_tracks]

@memoify
@delayed
def get_releases_by_discid(discid):
        """ Given a musicbrainz disc-id, fetch a list of possible releases. """
        q = ws.Query()
        filter = ws.ReleaseFilter(discId=discid)
        return q.getReleases(filter=filter)

def track_number(tracks, track):
	""" Lookup trackname in a list of tracks and return the track number
	(indexed starting at 1) """
	tracknum = 1
	for t in tracks:
		if t.id == track.id:
			return tracknum
		tracknum += 1
	return -1

@memoify
@delayed
def get_track_artist_for_track(track):
	""" Returns the musicbrainz Artist object for the given track. This may
		require a webservice lookup
	"""
	if track.artist is not None:
		return track.artist

	q = ws.Query()
	includes = ws.TrackIncludes(artist = True)
	t = q.getTrackById(track.id, includes)

	if t is not None:
		return t.artist

	return None

@memoify
@delayed
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
	rels = q.getReleases(filter)

	for rel in rels:
		r = rel.getRelease()
		# Releases can have multiple ASINs, so we need to get the entire list
		# and check them all. Pain.
		includes = ws.ReleaseIncludes(artist=True, urlRelations = True)
		release = q.getReleaseById(r.id, includes)
		for relation in release.getRelations():
			if relation.getType().find("AmazonAsin") != -1:
				asin = relation.getTargetId().split("/")[-1].strip()
				if asin == disc.asin:
					releases.append(release)
	return releases


@memoify
def get_album_art_url_for_asin(asin):
	if asin is None:
		return None
	print "Doing an Amazon Web Services lookup for ASIN " + asin
	try:
		item = amazon4.search_by_asin(asin, license_key=AMAZON_LICENSE_KEY, response_group="Images")
	except Exception,e:
		print e
		return None
	if hasattr(item,"LargeImage"):
		return item.LargeImage.URL
	return None

@memoify
def get_asin_from_release(release):
	# The ASIN specified in release.asin isn't necessarily the only ASIN
	# for the release. Sigh. So, we need to look at the release's relations
	# to see if there are multiple ASINs, report this to the user, and
	# bail. The user can then choose which ASIN they want to use and
	# specify it on the command line next time.
	asins = []
	for relation in release.getRelations():
		if relation.getType().find("AmazonAsin") != -1:
			asinurl = relation.getTargetId()
			asins.append(asinurl)
			print "Amazon ASIN: " + asinurl
	if len(asins) == 1:
		return asins[0]
	elif len(asins) == 0:
		print "WARNING: No ASIN for this release"
		return None
	else:
		print "WARNING: Ambiguous ASIN. Select an ASIN and specify it using --release-asin"
		return None

def parse_album_name(albumname):
	""" Pull apart an album name of the form 
			"Stadium Arcadium (disc 1: Mars)"
		and return a tuple of the form
			(albumtitle, discnumber, disctitle)
		so for the above, we would return
			("Stadium Arcadium", "1", "Mars")
		discnumber or disctitle will be set to None if they are unavailable
	"""
	# Note that we use a pretty ugly pattern here so that it's easy to separate
	# out into groups.
	pattern = r"^(.*?)( \(disc (\d+)(: (.*))?\))?$"
	m = re.compile(pattern).search(albumname)
	if m is None:
		raise Exception("Malformed album name: %s" % albumname)

	g = m.groups()
	return (g[0].strip(), g[2], g[4])


