import urllib2
import urllib
import urlparse
import xml.etree.ElementTree
import re
import lookups
import memocache
from htmlentitydefs import name2codepoint

key="65085e011105adbea86d1fdb8f3fe7a5"
secret="7c74c71eeac0045d153ab3cbfc828397"

def htmlentitydecode(s):
    os= re.sub('&(%s);' % '|'.join(name2codepoint), 
            lambda m: unichr(name2codepoint[m.group(1)]), s)
    return os

def clean_trackid(trackid):
	m=re.match(".*([a-fA-Z0-9]{8}-[a-fA-Z0-9]{4}-[a-fA-Z0-9]{4}-[a-fA-Z0-9]{4}-[a-fA-Z0-9]{12}).*",trackid)
	assert m
	mbid=m.group(1)
	return mbid

def _cleanname(x):
	if x is None:
		return ''
	return htmlentitydecode(x)

def _etree_to_dict(etree):
	result={}
	for i in etree:
		if i.tag not in result:
			result[i.tag]=[]
		if len(i):
			result[i.tag].append(_etree_to_dict(i))
		else:
			result[i.tag].append(_cleanname(i.text))
	return result

@memocache.memoify()
@lookups.timeout_retry("lastfm")
@lookups.delayed("lastfm")
def _do_raw_lastfm_query(url):
	f = urllib2.Request(url)
	f.add_header('User-Agent','AlbumIdentify v1.0')
	try:
		f = urllib2.urlopen(f)
	except urllib2.URLError, e:
		if (hasattr(e, 'reason')):
			print e.reason
		else:
			print str(e) + ' returned from ' + url
		raise

	tree = xml.etree.ElementTree.ElementTree(file=f)
	result=_etree_to_dict(tree.getroot()[0])
	return result

def _do_lastfm_query(method,**kwargs):
	args = { 
		"method" : method,
		"api_key" : key,
	 	}
	for k,v in kwargs.items():
		args[k] = v.encode("utf8")
	url=urlparse.urlunparse(('http',
		'ws.audioscrobbler.com',
		'/2.0/',
		'',
		urllib.urlencode(args),
		''))
	return _do_raw_lastfm_query(url)

def get_track_info(artistname, trackname):
	return _do_lastfm_query("track.getinfo",
		artist=artistname,
		track=trackname)

def get_track_toptags(artistname, trackname, mbtrackid=None):
	if mbtrackid is None:
		return _do_lastfm_query("track.gettoptags",
			artist=artistname,
			track=trackname)
	else:
		return _do_lastfm_query("track.gettoptags",
			artist=artistname,
			track=trackname,
			trackid=mbtrackid)

def get_artist_info(artistname):
	return _do_lastfm_query("artist.getinfo",
		artist=artistname)

def get_artist_by_mbid(mbid):
	return _do_lastfm_query("artist.getinfo",
		mbid=mbid)

def get_artist_toptags(artistname):
	return _do_lastfm_query("artist.gettoptags",
		artist=artistname)

def get_artist_toptracks(artistname):
	return _do_lastfm_query("artist.gettoptracks",
		artist=artistname)

if __name__=="__main__":
	import pprint
	pprint.pprint(get_track_info('Pearl Jam','Even Flow',))

# vim: set sw=8 tabstop=8 noexpandtab :
