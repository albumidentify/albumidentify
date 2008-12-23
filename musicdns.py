#
# musicdns.py
# An interface to the MusicDNS web-service
#
# Mostly stolen^Hborrowed from pyofa
#

import urllib
from xml.etree import ElementTree
import re
import lookups

musicdns_host = 'ofa.musicdns.org'
musicdns_port = 80

@lookups.memoify
@lookups.delayed
def lookup_fingerprint(fingerprint, duration, musicdns_key):
	""" Given a fingerprint and duration, lookup the track using the 
	MusicDNS web-service and return the PUID, if found.
	"""
	req = '/ofa/1/track'
	url = 'http://%s:%d%s' % (musicdns_host, musicdns_port, req)
	postargs = dict(
		cid=musicdns_key,
		cvr="flacnamer 0.1",
		fpt=fingerprint,
		art='',
		ttl='track',
		alb='',
		tnm='',
		gnr='',
		yrr='',
		brt='',
		fmt='',
		dur=str(duration),
		rmd='1' # Return metadata, 
	)
	
	data = urllib.urlencode(postargs)

	f = urllib.urlopen(url, data)
	tree = ElementTree.parse(f)
	sanitize_tree(tree)
	el = tree.find('//title')
	title = el.text if el is not None else None

	el = tree.find('//artist/name')
	artist = el.text if el is not None else None

	el = tree.find('//puid')
	puid = el.attrib['id'] if el is not None else None

	return (title, artist, puid)

def sanitize_tree(tree):
	for el in tree.getiterator():
		el.tag = re.sub('{.*}', '', el.tag) 
