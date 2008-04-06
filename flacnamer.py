#!/usr/bin/python
#
# Script to automatically look up albums in the musicbrainz database and
# rename/retag FLAC files.
# Also gets album art via amazon web services
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#
# TODO:
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
import re

AMAZON_LICENSE_KEY='1WQQTEA14HEA9AERDMG2'

def print_usage():
	print "usage: " + sys.argv[0] + " <srcpath> [OPTIONS]"
	print "  srcpath     A path containing flacs and a TOC to tag"
	print " OPTIONS:"
	print "  --release-id=ID     The Musicbrainz release id for this disc. Use this to"
	print "                      specify the release when discid lookup fails."
	print "  --no-embed-coverart Don't embed the cover-art in each flac file"
	print "  --release-asin=ASIN Manually specify the Amazon ASIN number for discs that"
	print "                      have more than one ASIN (useful to force the correct"
	print "                      coverart image)."

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

def get_musicbrainz_release(discid = None, releaseid = None):
	if discid is None and releaseid is None:
		raise Exception("Specify at least one of discid or releaseid")

	q = ws.Query()

	# If a discid has been specified we need to look that up first to get the
	# releaseid.
	if discid is not None:
		filter = ws.ReleaseFilter(discId=discid)
		results = q.getReleases(filter=filter)
		if len(results) > 1:
			raise Exception("Ambiguous DiscID. More than one release matches")

		if len(results) == 0:
			raise Exception("No result for DiscID " + discid)
		releaseid = results[0].release.id

	includes = ws.ReleaseIncludes(artist=True, tracks=True, releaseEvents=True,
									urlRelations=True)
	return q.getReleaseById(id_ = releaseid, include=includes)

def parse_album_name(albumname):
	""" Pull apart an album name of the form 
			"Stadium Arcadium (disc 1: Mars)"
		and return a tuple of the form
			(albumtitle, discnumber, disctitle)
		so for the above, we would return
			("Stadium Arcadium", "1", "Mars")
		discnumber or disctitle will be set to None if they are unavailable
	"""
	# Note that we use a pretty ugly pattern here so that it's easy to separate
	# out into groups.
	pattern = r"^(.*?)( \(disc (\d+)(: (.*))?\))?$"
	m = re.compile(pattern).search(albumname)
	if m is None:
		raise Exception("Malformed album name: %s" % albumname)

	g = m.groups()
	return (g[0].strip(), g[2], g[4])

def get_all_discs_in_album(disc, albumname = None): 
	""" Given a disc, talk to musicbrainz to see how many discs are in the
	release.  Return a list of releases which correspond to all of the discs in
	this release. Note that there is an easier way to accomplish this using a
	newer version of python-musicbrainz2 which allows for Lucene searching in
	the Filter objects, so we can search directly by ASIN, which would be
	perfect.  For now though we need to do fuzzy matching on release title and
	album artist and then count how many resulting releases share the asin with
	the disc we have been given.  """

	releases = []

	if albumname is None:
		(albumname, discnumber, disctitle) = parse_album_name(disc.album)
	filter = ws.ReleaseFilter(title=albumname, artistName=disc.artist)
	q = ws.Query()
	rels = q.getReleases(filter)

	for rel in rels:
		r = rel.getRelease()
		# Releases can have multiple ASINs, so we need to get the entire list
		# and check them all. Pain.
		includes = ws.ReleaseIncludes(artist=True, urlRelations = True)
		release = q.getReleaseById(r.id, includes)
		for relation in release.getRelations():
			if relation.getType().find("AmazonAsin") != -1:
				asin = relation.getTargetId().split("/")[-1].strip()
				if asin == disc.asin:
					releases.append(release)
	return releases
	
def main():
	if len(sys.argv) < 2:
		print_usage()
		sys.exit(1)

	releaseid = None
	embedcovers = True
	asin = None

	for option in sys.argv[2:]:
		if option.startswith("--release-id="):
			releaseid = option.split("=")[1].strip()
		elif option.startswith("--no-embed-coverart"):
			embedcovers = False
		elif option.startswith("--release-asin="):
			asin = option.split("=",1)[1].strip()
			# Allow the user to specify an ASIN as a URI or just the number
			if asin.find("/") != -1:
				asin = asin.split("/")[-1]

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

	if releaseid is None:
		print "Looking up musicbrainz discid " + mb_discid 
		release = get_musicbrainz_release(discid = mb_discid)
	else:
		print "Looking up musicbrainz releaseid " + releaseid
		release = get_musicbrainz_release(releaseid = releaseid)

	releasetypes = release.getTypes()

	disc.set_musicbrainz_tracks(release.getTracks())
	disc.releasedate = release.getEarliestReleaseDate()

	disc.artist = mp3names.FixArtist(release.artist.name)
	disc.album = release.title
	disc.year = disc.releasedate[0:4]
	disc.compilation = 0
	disc.number = 0
	disc.totalnumber = 0
	if asin is not None:
		disc.asin = asin
	else:
		# The ASIN specified in release.asin isn't necessarily the only ASIN
		# for the release. Sigh. So, we need to look at the release's relations
		# to see if there are multiple ASINs, report this to the user, and
		# bail. The user can then choose which ASIN they want to use and
		# specify it on the command line next time.
		asincount = 0
		for relation in release.getRelations():
			if relation.getType().find("AmazonAsin") != -1:
				asincount += 1
				print "Amazon ASIN: " + relation.getTargetId()
		if asincount == 1 or asincount == 0:
			disc.asin = release.asin
		else:
			raise Exception("Ambiguous ASIN. Select an ASIN and specify it using --release-asin")
			
	# Set the compilation tag appropriately
	if musicbrainz2.model.Release.TYPE_COMPILATION in releasetypes:
		disc.compilation = 1
	
	# Name the target folder differently for soundtracks
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

	# Deal with disc x of y numbering
	(albumname, discnumber, disctitle) = parse_album_name(disc.album)
	if discnumber is None:
		disc.number = 1
		disc.totalnumber = 1
	else:
		disc.number = int(discnumber)
		discs = get_all_discs_in_album(disc, albumname)
		disc.totalnumber = len(discs)

	print "disc " + str(disc.number) + " of " + str(disc.totalnumber)
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
TOTALTRACKS=%s
ALBUM=%s
MUSICBRAINZ_ALBUMID=%s
MUSICBRAINZ_ALBUMARTISTID=%s
MUSICBRAINZ_ARTISTID=%s
MUSICBRAINZ_TRACKID=%s
MUSICBRAINZ_DISCID=%s
DATE=%s
YEAR=%s
COMPILATION=%s
DISC=%s
DISCC=%s
DISCNUMBER=%s
DISCTOTAL=%s
''' % (mbtrack.title, track_artist_name, disc.artist, str(tracknum), str(len(disc.tracks)), str(len(disc.tracks)), 
			disc.album, os.path.basename(release.id), os.path.basename(release.artist.id),
			os.path.basename(track_artist.id), os.path.basename(mbtrack.id), mb_discid, disc.releasedate, disc.year,
			str(disc.compilation), str(disc.number), str(disc.totalnumber), str(disc.number), str(disc.totalnumber))
		
		if track.isrc is not None:
			flactags += "ISRC=%s\n" % track.isrc
		if disc.mcn is not None:
			flactags += "MCN=%s\n" % disc.mcn

		for type in releasetypes:
			flactags += "MUSICBRAINZ_RELEASE_ATTRIBUTE=%s\n" % musicbrainz2.utils.getReleaseTypeName(type)

		proclist = ["metaflac", "--import-tags-from=-"]

		if embedcovers:
			proclist.append("--import-picture-from=" + os.path.join(newpath, "folder.jpg"))

		proclist.append(os.path.join(newpath, newfilename))


		p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
		p.stdin.write(flactags.encode("utf8"))
		p.stdin.close()
		p.wait()

	print os.path.join(srcpath, tocfilename) + " -> " + os.path.join(newpath, "data.toc")
	shutil.copyfile(os.path.join(srcpath, tocfilename), os.path.join(newpath, "data.toc"))
	#os.system("rm \"%s\" -rf" % srcpath)
	

if __name__ == "__main__":
	main()
	sys.exit(0)
