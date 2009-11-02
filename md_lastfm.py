import lastfm
import tag
import urllib2

def get_tags(tags, mbalbum, mbtrack, artistname):
	try:
		artist_tags = lastfm.get_artist_toptags(artistname)
	except urllib2.HTTPError, e:
		artist_tags = {}
	try:
		track_tags =  lastfm.get_track_toptags(artistname,mbtrack.title,mbtrack.id)
	except urllib2.HTTPError, e:
		track_tags = {}
	taglist = [
		i["name"][0]
		for i in 
		artist_tags.get('tag',[]) + track_tags.get('tag',[])
		if int(i["count"][0])>1
		]
	tags[tag.TAGS] = ",".join(taglist)

