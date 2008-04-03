#!/usr/bin/python
#
# Script to automatically look up albums in the musicbrainz database and
# rename/retag FLAC files.
# Also gets album art via amazon web services
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#
# TODO:
#  - Disc x of y tags - this may require looking at the musicbrainz
#    relationships system.
#  - Set the COMPILATION tag appropriately - is a greatest hits release a
#    compilation, or is a compilation just a release with various artists?
#  - Set synonymous tags for things like TOTALTRACKS, etc.
#  - Abstract out the musicbrainz access to make it easier to switch between
#    using the webservice and a local copy of the database
#  - In main(), switch from iterating over the files to iterating over the
#    tracks
#  - Deal with multi-mode discs

import sys
import os
from datetime import timedelta
import musicbrainz2.webservice as ws
import musicbrainz2.utils as u
import musicbrainz2.model
import amazon4
import toc
import discid
import shutil
import urllib
import mp3names
import subprocess

AMAZON_LICENSE_KEY='1WQQTEA14HEA9AERDMG2'

def print_usage():
	print "usage: " + sys.argv[0] + " <srcpath>"

def get_album_art_url_for_asin(asin):
	print "Doing an Amazon Web Services lookup for ASIN " + asin
	item = amazon4.search_by_asin(asin, license_key=AMAZON_LICENSE_KEY, response_group="Images")
	return item.LargeImage.URL


def get_track_artist_for_track(track):
	""" Returns the musicbrainz Artist object for the given track. This may
		require a webservice lookup
	"""
	if track.artist is not None:
		return track.artist

	q = ws.Query()
	includes = ws.TrackIncludes(artist = True)
	t = q.getTrackById(track.id, includes)

	if t is not None:
		return t.artist

	return None

def get_musicbrainz_release_for_discid(discid):
	q = ws.Query()
	filter = ws.ReleaseFilter(discId=discid)
	results = q.getReleases(filter=filter)

	if len(results) > 1:
		raise Exception("Ambiguous DiscID. More than one release matches")

	if len(results) == 0:
		raise Exception("No result for DiscID " + discid)

	includes = ws.ReleaseIncludes(artist=True, tracks=True, releaseEvents=True)
	return q.getReleaseById(id_ = results[0].release.id, include=includes)

def main():
	if len(sys.argv) != 2:
		print_usage()
		sys.exit(1)

	srcpath = os.path.abspath(sys.argv[1])

	if not os.path.exists(srcpath):
		print_usage()
		sys.exit(2)

	print "Source path: " + srcpath

	tocfilename = ""
	if os.path.exists(os.path.join(srcpath, "data.toc")):
		tocfilename = "data.toc"
	elif os.path.exists(os.path.join(srcpath, "TOC")):
		tocfilename = "TOC"
	else:
		print "No TOC in source path!"
		sys.exit(4)

	disc = toc.Disc(cdrdaotocfile=os.path.join(srcpath, tocfilename))
	mb_discid = discid.generate_musicbrainz_discid(
		disc.get_first_track_num(),
		disc.get_last_track_num(),
		disc.get_track_offsets())

	print "Looking up musicbrainz discid " + mb_discid 
	release = get_musicbrainz_release_for_discid(mb_discid)

	releasetypes = release.getTypes()

	disc.set_musicbrainz_tracks(release.getTracks())
	disc.releasedate = release.getEarliestReleaseDate()

	disc.artist = mp3names.FixArtist(release.artist.name)
	disc.album = release.title
	disc.year = disc.releasedate[0:4]
	disc.asin = release.asin
	
	if musicbrainz2.model.Release.TYPE_SOUNDTRACK in releasetypes:
		newpath = "Soundtrack - %s - %s" % (disc.year, disc.album)
	else:
		newpath = "%s - %s - %s" % (disc.artist, disc.year, disc.album)
	newpath = mp3names.FixFilename(newpath)
	newpath = os.path.join(srcpath, "../%s/" % newpath)
	newpath = os.path.normpath(newpath)

	print "Destination path: " + newpath

	if (os.path.exists(newpath)):
		print "Destination path already exists, skipping" 
		sys.exit(3)

	os.mkdir(newpath)

	# Get album art
	imageurl = get_album_art_url_for_asin(disc.asin)
	print imageurl
	if imageurl is not None:
		urllib.urlretrieve(imageurl, os.path.join(newpath, "folder.jpg"))

	# Warning: This code doesn't actually check if the number of tracks in the
	# current directory matches the number of tracks in the release. It's
	# assumed that seeing as the TOC describes this directory and the discId is
	# unique, then things should all work out for the best.  A safer assumption
	# would be to iterate over the track list rather than the file list. Meh
	# for now.
	for file in os.listdir(srcpath):
		if not file.endswith(".flac"):
			continue
		if not file.startswith("track"):
			continue

		tracknum = file[5:7]
		track = disc.tracks[int(tracknum) -1]
		mbtrack = track.mb_track

		if release.isSingleArtistRelease():
			track_artist = release.artist
		else:
			track_artist = get_track_artist_for_track(mbtrack)

		track_artist_name = mp3names.FixArtist(track_artist.name)

		newfilename = "%s - %s - %s.flac" % (tracknum, track_artist_name,
													mbtrack.title)
		newfilename = mp3names.FixFilename(newfilename)

		print os.path.join(srcpath, file) + " -> " + os.path.join(newpath, newfilename)
		shutil.copyfile(os.path.join(srcpath, file), os.path.join(newpath, newfilename))

		flactags = '''TITLE=%s
ARTIST=%s
ALBUMARTIST=%s
TRACKNUMBER=%s
TRACKTOTAL=%s
ALBUM=%s
MUSICBRAINZ_ALBUMID=%s
MUSICBRAINZ_ALBUMARTISTID=%s
MUSICBRAINZ_ARTISTID=%s
MUSICBRAINZ_TRACKID=%s
MUSICBRAINZ_DISCID=%s
DATE=%s
''' % (mbtrack.title, track_artist_name, disc.artist, str(tracknum), str(len(disc.tracks)), 
			disc.album, os.path.basename(release.id), os.path.basename(release.artist.id),
			os.path.basename(track_artist.id), os.path.basename(mbtrack.id), mb_discid, disc.releasedate)
		
		if track.isrc is not None:
			flactags += "ISRC=%s\n" % track.isrc
		if disc.mcn is not None:
			flactags += "MCN=%s\n" % disc.mcn

		for type in releasetypes:
			flactags += "MUSICBRAINZ_RELEASE_ATTRIBUTE=%s\n" % musicbrainz2.utils.getReleaseTypeName(type)

		p = subprocess.Popen(["metaflac", "--import-tags-from=-", os.path.join(newpath, newfilename)],
							stdin=subprocess.PIPE)
		p.stdin.write(flactags.encode("utf8"))
		p.stdin.close()
		p.wait()

	print os.path.join(srcpath, tocfilename) + " -> " + os.path.join(newpath, "data.toc")
	shutil.copyfile(os.path.join(srcpath, tocfilename), os.path.join(newpath, "data.toc"))
	#os.system("rm \"%s\" -rf" % srcpath)
	

if __name__ == "__main__":
	main()
	sys.exit(0)
