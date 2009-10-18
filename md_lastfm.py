import lastfm
import tag

def get_tags(tags, mbtrack, artistname):
	print "Looking up lastfm"
	artist_tags = lastfm.get_artist_toptags(artistname)
	track_tags =  lastfm.get_track_toptags(artistname,mbtrack.title)
	taglist = [
		i["name"][0]
		for i in 
		artist_tags.get('tag',[]) + track_tags.get('tag',[])
		if int(i["count"][0])>1
		]
	tags[tag.TAGS] = ",".join(taglist)

