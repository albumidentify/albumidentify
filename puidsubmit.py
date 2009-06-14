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
from ConfigParser import NoOptionError

#host="musicbrainz.homeip.net"
host="musicbrainz.org"
clientId = 'albumrenamer-1'

class SubmitFailed(Exception):
	def __init__(self, reason):
		self.reason = reason
		
	def __str__(self):
		return "Failed to submit to Musicbrainz: %s" % self.reason

@lookups.delayed()
def submit_puids_mb(track2puid):
	try:
		username=albumidentifyconfig.config.get("musicbrainz","username")
		password=albumidentifyconfig.config.get("musicbrainz","password")
	except NoOptionError, e:
		raise SubmitFailed("No username or password set")
	
	service = ws.WebService(host=host, username=username, password=password)
	q = ws.Query(service, clientId=clientId)
	submititems = track2puid.items()
	while len(submititems) > 0:
		q.submitPuids(dict(submititems[:20]))
		submititems=submititems[20:]

	for (track,puid) in track2puid.iteritems():
		lookups.remove_from_cache("delayed_get_tracks_by_puid",puid)
		lookups.remove_from_cache("delayed_get_track_by_id",track)

@lookups.delayed()
def submit_isrcs_mb(track2isrc):
	try:
		username=albumidentifyconfig.config.get("musicbrainz","username")
		password=albumidentifyconfig.config.get("musicbrainz","password")
	except NoOptionError, e:
		raise SubmitFailed("No username or password set")
	
	service = ws.WebService(host=host, username=username, password=password)
	q = ws.Query(service)
	submititems = track2isrc.items()
	while len(submititems) > 0:
		q.submitISRCs(dict(submititems[:20]))
		submititems=submititems[20:]

	for (track,isrc) in track2isrc.iteritems():
		lookups.remove_from_cache("delayed_get_track_by_id",track)
