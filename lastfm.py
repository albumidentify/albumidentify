import urllib2
import urllib
import urlparse
import xml.etree.ElementTree
key="65085e011105adbea86d1fdb8f3fe7a5"
secret="7c74c71eeac0045d153ab3cbfc828397"

def _etree_to_dict(etree):
	result={}
	for i in etree:
		if i.tag not in result:
			result[i.tag]=[]
		if len(i):
			result[i.tag].append(_etree_to_dict(i))
		else:
			result[i.tag].append(i.text)
	return result

def get_track_info(mbid,artist,track):
	url=urlparse.urlunparse(('http',
		'ws.audioscrobbler.com',
		'/2.0/',
		'',
		urllib.urlencode({
			"method":"track.getinfo",
			"api_key" : key,
			"artist" : artist,
			"track" : track,
			"mbid" : mbid,
			}),
			''))
	f = urllib2.Request(url)
	f.add_header('User-Agent','AlbumIdentify v1.0')
	try:
		f = urllib2.urlopen(f)
	except Exception, e:
		print e.msg
		print e.fp.read()
		raise

	tree = xml.etree.ElementTree.ElementTree(file=f)
	result=_etree_to_dict(tree.getroot()[0])
	return result
	
if __name__=="__main__":
	import pprint
	pprint.pprint(get_track_info('33e1d8ed-40e1-401c-962f-0170573cbc00','Pearl Jam','Even Flow',))
