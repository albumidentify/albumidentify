#!/usr/bin/env python

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
	f = urllib2.urlopen(f)

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

def lookup_track(args):
	r = get_track_info(args.artist, args.trackname)

	print "Results for %s - %s" % (args.artist, args.trackname)
	print r['name'][0]
	del r['name']

	print_output(r, args.filter)

def lookup_artist(args):
	r = get_artist_info(args.artist)

	print "Results for %s" % (args.artist)

	print_output(r, args.filter)

def print_output(text, filter):
	if filter == 'ALL':
		import pprint
		pprint.pprint(text)
	elif filter != '':
		space = 0;
		for i in filter.split('/'):
			for a in xrange(space):
				print "",
			try:
				i = int(i)
				text = text[i]
				print "-> fetching item %d from list" % i
			except:
				text = text[i]
				print "-> %s" % i
			if type(text) == list and len(text) == 1:
				text = text[0]
			space += 1
	if type(text) == dict:
		print text.keys()
	elif type(text) == list:
		for i in text:
			print i
	else:
		print text

def help(args):
	print """Filters

A filter is the fields you are after separated by forward slashes. Here's an 
example: ./lastfm.py artist "Avril Lavigne" 'tags/tag/0/name'
As you can see the filter has 4 parts. First we want tags. Next we want the
tag field. Next we want item 0 from the list. Finally we want the text from the
name field. To find out what the next set of filter items are simply omit the
term you are looking for and you will be presented with all the possibilities.
If the results are a list, each item of the list will be printed one per line.
To disable filtering use the keyword 'ALL' as the filter.
"""

if __name__=="__main__":
	import argparse,sys

	mode_parser = argparse.ArgumentParser()
	subparsers = mode_parser.add_subparsers(title='actions',dest='action')
	mode_parser.add_argument('--filter-help',action='store_true',help='Explanation of output filters')

	track_parser = subparsers.add_parser('track', help='Get lastfm info for a Track')
	track_parser.add_argument('artist',help='The name of the Artist')
	track_parser.add_argument('trackname',help='The Title of the Track')
	track_parser.add_argument('filter',help='Output filter (see %s help)' % sys.argv[0],default="",nargs='?')
	track_parser.set_defaults(func=lookup_track)

	artist_parser = subparsers.add_parser('artist', help='Get lastfm info for an Artist')
	artist_parser.add_argument('artist',help='The name of the Artist')
	artist_parser.add_argument('filter',help='Output filter (see %s help)' % sys.argv[0],default="",nargs='?')
	artist_parser.set_defaults(func=lookup_artist)

	help_parser = subparsers.add_parser('help', help='Help with filters')
	help_parser.set_defaults(func=help)

	args = mode_parser.parse_args()
	args.func(args)

# vim: set sw=8 tabstop=8 noexpandtab :
