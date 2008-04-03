#!/usr/bin/python
import pyPgSQL.PgSQL

db=pyPgSQL.PgSQL.connect(database='musicbrainz')

def get_album_info(artist,album):
	c=db.cursor()
	c.execute("""SELECT album.name as albumname,
		trackartist.name as trackartist, albumartist.name as albumartist,
		min(release.releasedate) as releasedate,
		albumjoin.album, track.length,
		albumjoin.sequence as sequence,
		track.name as trackname
		FROM album 
		JOIN albumjoin ON album.id = albumjoin.album
		JOIN track ON albumjoin.track = track.id
		JOIN artist AS trackartist ON track.artist = trackartist.id
		JOIN artist AS albumartist ON album.artist = albumartist.id
		JOIN release ON release.album = album.id
		JOIN artistalias AS albumartistalias ON albumartistalias.ref = albumartist.id
		WHERE (lower(albumartist.name) = lower(%s) 
			OR lower(albumartistalias.name) = lower(%s)
			OR lower(albumartist.sortname) = lower(%s))
		AND lower(album.name) = lower(%s) 
		GROUP BY albumjoin.album, albumjoin.sequence, albumname,
			trackartist, albumartist, track.length, trackname
		ORDER BY albumjoin.album,sequence
		""",(artist,artist,artist,album))

	oldalbum=None
	albums=[]
	for i in c.fetchall():
		if i["album"]!=oldalbum:
			oldalbum=i["album"]
			print i.items()
			albums.append({
				"albumname": i['albumname'],
				"album" : i["album"],
				"tracks" : [],
				"artist" : i["albumartist"],
				"year" : i["releasedate"].split("-")[0],
				"releasedate" : i["releasedate"],
				})
			#print "%s(%d):" % (i["albumname"],i["album"])
		#print i["sequence"],i["length"]/1000.0,i["name"]
		albums[-1]["tracks"].append({
			"track" : i["sequence"],
			"duration" : i["length"],
			"name" : i["trackname"],
			"artist" : i["trackartist"],
		})
	return albums

if __name__=="__main__":
	import sys
	for i in get_album_info(sys.argv[1],sys.argv[2]):
		print "%s(%d):" % (i["albumname"],i["album"])
		for j in i["tracks"]:
			print "",j["track"],j["duration"]/1000.0,j["name"]
