#!/usr/bin/python
import urllib2
import urllib
import sys
import shelve
import pickle
import os
import re
import albumidentifyconfig

#url="http://musicbrainz.homeip.net/ws/1/track/"
url="http://musicbrainz.org/ws/1/track/"

albumidentifyconfig.readconfig()

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
	urllib2.install_opener(opener)

def clean_uuid(uuid):
	r=re.match("(?:.*/)?([a-zA-Z0-9-]{36})(?:.html)?",uuid)
	if not r:
		print "didn't match:",`uuid`
		return uuid
	return r.group(1)

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
		f = urllib2.urlopen(url,data)
		f.read()
	except urllib2.HTTPError, e:
		print e
		print e.read()
		raise
	# Flush these entries out of the track by puid cache
	try:
		sh=shelve.open(os.path.expanduser("~/.mbcache/delayed_get_tracks_by_puid"),"w")
		key=pickle.dumps(((unicode(puid),),{}))
		if key in sh:
			del sh[key]
		key=pickle.dumps(((str(puid),),{}))
		if key in sh:
			del sh[key]
	except Exception, e:
		print e

if __name__=="__main__":
	submit_puid(sys.argv[1],sys.argv[2])
