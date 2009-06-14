#!/usr/bin/python
import urllib2
import urllib
import sys
import shelve
import pickle
import os
import re
import albumidentifyconfig
import lookups
import musicbrainz2.webservice as ws
import musicbrainz2.model as model

#url="http://musicbrainz.homeip.net/ws/1/track/"
url="http://musicbrainz.org/ws/1/track/"

opener = None

def build_opener():
	global opener
	if opener is not None:
		return

	authinfo = urllib2.HTTPDigestAuthHandler()
	authinfo.add_password(realm="musicbrainz.org",
			uri=url,
			user=albumidentifyconfig.config.get("musicbrainz","username"),
			passwd=albumidentifyconfig.config.get("musicbrainz","password"))

	opener = urllib2.build_opener(authinfo)

def clean_uuid(uuid):
	r=re.match("(?:.*/)?([a-zA-Z0-9-]{36})(?:.html)?",uuid)
	if not r:
		print "didn't match:",`uuid`
		return uuid
	return r.group(1)

@lookups.delayed()
def submit_puid(trackid,puid):
	build_opener()
	trackid = clean_uuid(trackid)
	puid = clean_uuid(puid)
	assert len(trackid)==36
	assert len(puid)==36
	data= urllib.urlencode([
			("client" , "albumrenamer-1"),
			("puid" , "%s %s" % (trackid,puid)),
			],True)

	try:
		f = opener.open(url,data)
		f.read()
	except urllib2.HTTPError, e:
		print e
		print e.read()
		raise
	# Flush these entries out of the cache, so they'll be found next time
	try:
		lookups.remove_from_cache("delayed_get_tracks_by_puid",puid)
		lookups.remote_from_cache("delayed_get_track_by_id",trackid)
	except Exception, e:
		print e

@lookups.delayed()
def _submit_puids(puid2track):
	build_opener()
	data= urllib.urlencode([
			("client" , "albumrenamer-1"),
			]+[ 
				("puid" , "%s %s" % (clean_uuid(trackid),
					clean_uuid(puid)))
				for (puid,trackid) in puid2track.items()
			],True)

	try:
		f = opener.open(url,data)
		f.read()
	except urllib2.HTTPError, e:
		print e
		print e.read()
		raise
	# Flush these entries out of the track by puid cache
	try:
		sh=shelve.open(os.path.expanduser("~/.mbcache/delayed_get_tracks_by_puid"),"c")
		key=pickle.dumps(((unicode(puid),),{}))
		if key in sh:
			del sh[key]
		key=pickle.dumps(((str(puid),),{}))
		if key in sh:
			del sh[key]
	except Exception, e:
		print e

def submit_puids(puid2trackid):
	"Bulk submit puids"
	puid2trackid = puid2trackid.items()
	while len(puid2trackid)>0:
		_submit_puids(dict(puid2trackid[:20]))
		puid2trackid=puid2trackid[20:]

@lookups.delayed()
def submit_puids_mb(track2puid):
	service = ws.WebService(
		username=albumidentifyconfig.config.get("musicbrainz","username"),
		password=albumidentifyconfig.config.get("musicbrainz","password"))
	q = ws.Query(service, clientId='albumrenamer-1')
	try:
		q.submitPuids(track2puid)
	except Exception, e:
		print e
		raise e
	for (track,puid) in track2puid.iteritems():
		lookups.remove_from_cache("delayed_get_tracks_by_puid",puid)
		lookups.remove_from_cache("delayed_get_track_by_id",track)

@lookups.delayed()
def submit_isrcs_mb(track2isrc):
	service = ws.WebService(
		username=albumidentifyconfig.config.get("musicbrainz","username"),
		password=albumidentifyconfig.config.get("musicbrainz","password"))
	q = ws.Query(service, clientId='albumrenamer-1')
	try:
		q.submitISRCs(track2isrc)
	except Exception, e:
		print e
		raise e
	for (track,isrc) in track2isrc.iteritems():
		lookups.remove_from_cache("delayed_get_track_by_id",track)

if __name__=="__main__":
	puid2track={}
	for i in range(len(sys.argv[1:])/2):
		puid2track[sys.argv[2+i*2]]=sys.argv[1+i*2]
	submit_puids(puid2track)
