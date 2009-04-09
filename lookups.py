import musicbrainz2.webservice as ws
import musicbrainz2.model as model
import time
import amazon4
import re
import pickle
import os
import atexit
import shelve

AMAZON_LICENSE_KEY='1WQQTEA14HEA9AERDMG2'

startup = time.time()
lastwsquery = {}

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

def remove_from_cache(funcname,*args,**kwargs):
	key=pickle.dumps((args,kwargs))
	if key in memocache[funcname]:
		del memocache[funcname][key]

def cleanup_memos():
	while memocache!={}:
		i=memocache.keys()[0]
		memocache[i].close()
		del memocache[i]

atexit.register(cleanup_memos)

MAXDELAY=1.5

def delayed(webservice="default"):
	"Decorator to make sure a function isn't called more often than once every 2 seconds. used to space webservice calls"
	def delayed2(func):
		def delay(*args,**kwargs):
			global lastwsquery
			if webservice not in lastwsquery:
				lastwsquery[webservice]=startup
				
			if time.time()-lastwsquery[webservice]<MAXDELAY:
				wait=MAXDELAY-(time.time()-lastwsquery[webservice])
				time.sleep(wait)
			ret=func(*args,**kwargs)
			lastwsquery[webservice]=time.time()
			return ret
		delay.__name__="delayed_"+func.__name__
		return delay
	return delayed2
	
@memoify
@delayed()
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
@delayed()
def get_track_by_id(id):
	q = ws.Query()
	results = []
	includes = ws.TrackIncludes(artist=True, releases=True, puids=True)
	t = q.getTrackById(id_ = id, include = includes)
	return t

@memoify
@delayed()
def get_release_by_releaseid(releaseid):
	""" Given a musicbrainz release-id, fetch the release from musicbrainz. """
	q = ws.Query()
	includes = ws.ReleaseIncludes(artist=True, counts=True, tracks=True, releaseEvents=True, urlRelations=True, releaseRelations=True)
	return q.getReleaseById(id_ = releaseid, include=includes)

@memoify
@delayed()
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
@delayed()
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
@delayed()
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

def __get_prev_and_next_releases(release):
        prev = None
        next = None
        relations = release.getRelations()
        for r in relations:
                if r.getType().find("#PartOfSet") != -1:
                        if r.getDirection() == model.Relation.DIR_BACKWARD:
                                prev = str(r.getTargetId()[-36:])
                        else:
                                next = str(r.getTargetId()[-36:])
                        continue
        return (prev,next)

def get_all_releases_in_set(releaseid):
        """ Return all of the release ids that belong to the same multi-disc set
            as the provided id.

            The original id will be passed back in the set, so the length of the 
            returned list indicates the number of discs in the set. The list should be
            ordered.
        """
        releases = [releaseid]
        r = get_release_by_releaseid(releaseid)
        (prev, next) = __get_prev_and_next_releases(r)
        # Search back to the beginning of the set...
        while prev is not None:
                releases = [prev] + releases
                (prev, n) = __get_prev_and_next_releases(get_release_by_releaseid(prev))
        # Search forward to the end of the set...
        while next is not None:
                releases = releases + [next]
                (p, next) = __get_prev_and_next_releases(get_release_by_releaseid(next))

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
def get_asin_from_release(release, prefer=None):
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

        if prefer is not None:
                for asin in asins:
                        if asin.find(prefer) != -1:
                                print "WARNING: Mulitple ASINs exist, but we are forcing " + prefer
                                return asin
	
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


