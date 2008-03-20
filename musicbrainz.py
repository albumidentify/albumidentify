#!/usr/bin/python
import pyPgSQL.PgSQL

db=pyPgSQL.PgSQL.connect(database='musicbrainz')

def get_album_info(artist,album):
	c=db.cursor()
	c.execute("""SELECT album.name as albumname,albumjoin.*,track.* 
		FROM album 
		JOIN albumjoin ON album.id = albumjoin.album
		JOIN artist ON album.artist = artist.id
		JOIN track ON albumjoin.track = track.id
		WHERE lower(artist.name) = lower(%s) and lower(album.name) = lower(%s)
		ORDER BY albumjoin.album,sequence
		""",(artist,album))

	oldalbum=None
	albums=[]
	for i in c.fetchall():
		if i["album"]!=oldalbum:
			oldalbum=i["album"]
			albums.append({
				"albumname": i['albumname'],
				"album" : i["album"],
				"tracks" : []
				})
			#print "%s(%d):" % (i["albumname"],i["album"])
		#print i["sequence"],i["length"]/1000.0,i["name"]
		albums[-1]["tracks"].append({
			"track" : i["sequence"],
			"duration" : i["length"],
			"name" : i["name"],
		})
	return albums

if __name__=="__main__":
	import sys
	for i in get_album_info(sys.argv[1],sys.argv[2]):
		print "%s(%d):" % (i["albumname"],i["album"])
		for j in i["tracks"]:
			print "",j["track"],j["duration"]/1000.0,j["name"]
