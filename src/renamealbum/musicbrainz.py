#!/usr/bin/python
import pyPgSQL.PgSQL
import re

db=pyPgSQL.PgSQL.connect(database='musicbrainz')

def _do_query(artist,album):
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
		LEFT JOIN release ON release.album = album.id
		LEFT JOIN artistalias AS albumartistalias ON albumartistalias.ref = albumartist.id
		WHERE (lower(albumartist.name) = lower(%(albumartist)s) 
			OR lower(albumartistalias.name) = lower(%(albumartist)s)
			OR lower(albumartist.sortname) = lower(%(albumartist)s))
		AND (lower(album.name) = lower(%(albumname)s) 
			OR lower(album.name) like lower(%(albumname)s))
		GROUP BY albumjoin.album, albumjoin.sequence, albumname,
			trackartist, albumartist, track.length, trackname
		ORDER BY albumjoin.album,sequence
		""",{"albumname" : album, "albumartist" : artist})
	return c.fetchall()

fixups = (
	(r'\((.*), (CD.*)\)',r'(\1) (\2)'),
	(r'\(CD *([0-9]+)\)',r'(disc \1%)'),
	(r'(.*), The','The $1'),
	(r'[^A-Za-z0-9() ]','%'),
	(r'(The(ir)? )?Greatest Hits','%'),
	(r'\(%\)',r'%'),
	(r' *%',r'%'),
	(r'$',r'%'),
	(r'%*%$',r'%'),
	)

morefixups = (
	(r'\(disc',r'%(disc'),
	)
	

def get_album_info(artist,album):
	data = _do_query(artist,album)
	if data==[]:
		for s,r in fixups:
			album=re.sub(s,r,album)
		print "Trying fuzzy match %s:" % `album`
		data = _do_query(artist,album)
	if data==[]:
		for s,r in morefixups:
			album=re.sub(s,r,album)
		print "Trying fuzzier match %s:" % `album`
		data = _do_query(artist,album)

	oldalbum=None
	albums=[]
	for i in data:
		if i["album"]!=oldalbum:
			oldalbum=i["album"]
			print i.items()
			albums.append({
				"albumname": i['albumname'],
				"album" : i["album"],
				"tracks" : [],
				"artist" : i["albumartist"],
				"releasedate" : i["releasedate"],
				})
			if i["releasedate"]:
				albums[-1]["year"]=i["releasedate"].split("-")[0]

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
	data=get_album_info(sys.argv[1],sys.argv[2])
	for i in data:
		print "%s %s(%d):" % (i["releasedate"],i["albumname"],i["album"])
		for j in i["tracks"]:
			print "",j["track"],j["duration"]/1000.0,j["name"]
	if not data:
		print "No matches"

