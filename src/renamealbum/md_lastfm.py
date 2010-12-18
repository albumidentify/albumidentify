import lastfm
import tag
import urllib2
import string

def get_tags(tags, mbalbum, mbtrack, artistname):
	try:
		artist_tags = lastfm.get_artist_toptags(artistname)
	except urllib2.HTTPError, e:
		artist_tags = {}
	try:
		track_tags =  lastfm.get_track_toptags(artistname,mbtrack.title,mbtrack.id)
	except urllib2.HTTPError, e:
		track_tags = {}
	taglist = []
	for i in artist_tags.get('tag',[]) + track_tags.get('tag',[]):
		if int(i["count"][0])>1:
			name = i["name"][0]
			name = string.capwords(name)
			if name not in taglist:
				taglist.append(name)
	#return tags separated by a comma
	tags[tag.TAGS] = ",".join(taglist)

