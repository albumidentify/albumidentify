#!/usr/bin/python2.5
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
import time
import submit #musicbrainz_submission_url()
import fingerprint
import musicdns

AMAZON_LICENSE_KEY='1WQQTEA14HEA9AERDMG2'
MUSICDNS_KEY='a7f6063296c0f1c9b75c7f511861b89b'
lastwsquery = time.time()

def waitforws(cb):
	global lastwsquery
	if time.time()-lastwsquery<2:
		wait=2-(time.time()-lastwsquery)
		time.sleep(wait)
	ret=cb()
	lastwsquery=time.time()
	return ret

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
	print "  --year=YEAR         Overwrite the album release year.  Use to force a"
	print "                      re-issue to the date of the original release or to"
	print "                      provide a date where one is missing"
	print "  -n                  Don't actually tag and rename files"

def get_album_art_url_for_asin(asin):
	if asin is None:
		return None
	print "Doing an Amazon Web Services lookup for ASIN " + asin
	item = amazon4.search_by_asin(asin, license_key=AMAZON_LICENSE_KEY, response_group="Images")
	if hasattr(item,"LargeImage"):
		return item.LargeImage.URL
	return None

def get_track_artist_for_track(track):
	""" Returns the musicbrainz Artist object for the given track. This may
		require a webservice lookup
	"""
	if track.artist is not None:
		return track.artist

	q = ws.Query()
	includes = ws.TrackIncludes(artist = True)
	t = waitforws(lambda :q.getTrackById(track.id, includes))

	if t is not None:
		return t.artist

	return None

def get_releases_by_metadata(disc):
	""" Given a Disc object, use the performer, title and number of tracks to
	lookup the release in musicbrainz. This method returns a list of possible
	results, or the empty list if there were no matches. """

	releases = []

	q = ws.Query()
	filter = ws.ReleaseFilter(title=disc.title, artistName=disc.performer)
	rels = waitforws(lambda :q.getReleases(filter))
	
	# Filter out of the list releases with a different number of tracks to the
	# Disc.
	for rel in rels:
		release =rel.release  #get_release_by_releaseid(rel.id)
		if len(release.getTracks()) == len(disc.tracks):
			releases.append(rel)

	return releases


def get_tracks_by_puid(puid):
	""" Lookup a list of musicbrainz tracks by PUID. Returns a list of Track
	objects. """ 
	q = ws.Query()
	filter = ws.TrackFilter(puid=puid)
	results = []
	rs = waitforws(lambda :q.getTracks(filter=filter))
	for r in rs:
		results.append(r.getTrack())
	return results

def get_release_by_releaseid(releaseid):
	""" Given a musicbrainz release-id, fetch the release from musicbrainz. """
	q = ws.Query()
	includes = waitforws(lambda :ws.ReleaseIncludes(artist=True, counts=True, tracks=True, releaseEvents=True,
									urlRelations=True))
	return q.getReleaseById(id_ = releaseid, include=includes)

def track_number(tracks, trackname):
	""" Lookup trackname in a list of tracks and return the track number
	(indexed starting at 1) """
	tracknum = 1
	for t in tracks:
		if t.title == trackname:
			return tracknum
		tracknum += 1
	return -1

def get_release_by_fingerprints(disc):
	""" Try to determine the release of a disc based on audio fingerprinting each track. 
	"""
	possible_releases = {}
	tracknum = 0
	for t in disc.tracks:
		tracknum += 1

		tmp = os.tmpnam() + ".wav"
		if os.system("flac -d --totally-silent -o " +  tmp +  " " + t.filename)!=0:
			raise Exception("flac %s failed!" % t.filanem )

		(fp, duration) = fingerprint.fingerprint(tmp)
		(artist, trackname, puid) = musicdns.lookup_fingerprint(fp, duration, MUSICDNS_KEY)
		os.unlink(tmp)
		if puid is None:
			print "Fingerprinting for " + t.filename + " failed."
			continue
		print "Fingerprinting for " + t.filename + " succeeded."
		print " PUID: " + puid

		tracks = get_tracks_by_puid(puid)
		for track in tracks:
			print "  Could be " + track.id + " (%s)" % track.title
			releases = track.getReleases()
			for r in releases:
				print "     Which is on " + r.id + " (%s)" % r.title
				release = get_release_by_releaseid(r.id)

				# Filter releases with the wrong number of tracks
				if len(release.getTracks()) != len(disc.tracks):
					print "      Which has " + str(len(release.getTracks())) + " tracks instead of " + str(len(disc.tracks))
					continue
				
				# Filter releases where this track is not in the correct
				# position.
				if track_number(release.getTracks(), track.title) != tracknum:
					print "      Incorrect track number"
					continue

				if possible_releases.has_key(release.id):
					possible_releases[release.id] += 1
				else:
					possible_releases[release.id] = 1
	print "Found " + str(len(possible_releases.keys())) + " possible releases"
	for r in possible_releases.keys():
		print r + " (" + str(possible_releases[r]) + ")"
	return possible_releases.keys()

def get_musicbrainz_release(disc):
	""" Given a Disc object, try a bunch of methods to look up the release in
	musicbrainz.  If a releaseid is specified, use this, otherwise search by
	discid, then search by CD-TEXT and finally search by audio-fingerprinting.
	"""
	if disc.discid is None and disc.releaseid is None:
		raise Exception("Specify at least one of discid or releaseid")

	q = ws.Query()

	# If a release id has been specified, that takes precedence
	if disc.releaseid is not None:
		return get_release_by_releaseid(disc.releaseid)

	# Otherwise, lookup the releaseid using the discid as a key
	filter = ws.ReleaseFilter(discId=disc.discid)
	results = waitforws(lambda :q.getReleases(filter=filter))
	if len(results) > 1:
		for result in results:
			print result.release.id
		raise Exception("Ambiguous DiscID. More than one release matches")

	# We have an exact match, use this.
	if len(results) == 1:
		releaseid = results[0].release.id
		return get_release_by_releaseid(results[0].release.id)

	# Otherwise, use CD-TEXT if present to guess the release
	if disc.performer is not None and disc.title is not None:
		print "Trying to look up release via CD-TEXT"
		print "Performer: " + disc.performer
		print "Title    : " + disc.title
		results = get_releases_by_metadata(disc)
		if len(results) == 1:
			print "Got result via CD-TEXT lookup!"
			print "Suggest submitting TOC and discID to musicbrainz:"
			print "Release URL: " + results[0].id + ".html"
			print "Submit URL : " + submit.musicbrainz_submission_url(disc)
			return results[0]
		elif len(results) > 1:
			for release in results:
				print release.id
			raise Exception("Ambiguous CD-TEXT. Select a release with --release-id")
		else:
			print "No results from CD-TEXT lookup."

	# Last resort, use audio finger-printing to guess the release
	releases = get_release_by_fingerprints(disc)
	if len(releases) == 1:
		release = get_release_by_releaseid(releases[0])
		print "Got result via audio fingerprinting!"
		print "Suggest submitting TOC and discID to musicbrainz:"
		print "Release URL: " + release.id + ".html"
		print "Submit URL : " + submit.musicbrainz_submission_url(disc)
		return release
	elif len(releases) > 1:
		raise Exception("Ambiguous PUID matches. Select a release with --release-id")
	else:
		print "No results from fingerprinting."
	return None

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
	rels = waitforws(lambda :q.getReleases(filter))

	for rel in rels:
		r = rel.getRelease()
		# Releases can have multiple ASINs, so we need to get the entire list
		# and check them all. Pain.
		includes = ws.ReleaseIncludes(artist=True, urlRelations = True)
		release = q.getReleaseById(r.id, includes)
		time.sleep(1)
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
	year = None
	noact = False

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
		elif option.startswith("--year="):
			year = option.split("=")[1].strip()
		elif option.startswith("-n"):
			noact = True

	srcpath = os.path.abspath(sys.argv[1])

	if not os.path.exists(srcpath):
		print_usage()
		sys.exit(2)
	
	if not noact:
		print "Performing dry-run"

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

	disc.tocfilename = tocfilename
	disc.discid = discid.generate_musicbrainz_discid(
			disc.get_first_track_num(),
			disc.get_last_track_num(),
			disc.get_track_offsets())

	for i in range(len(disc.tracks)):
		disc.tracks[i].filename = os.path.join(srcpath,  "track" + str(i + 1).zfill(2) + ".flac")
		if not os.path.exists(disc.tracks[i].filename):
			disc.tracks[i].filename = os.path.join(srcpath,  "track" + str(i + 1).zfill(2) + ".cdda.flac")

	print "discID: " + disc.discid

	if releaseid:
		disc.releaseid = releaseid
	
	release = get_musicbrainz_release(disc)

	if release is None:
		raise Exception("Couldn't find a matching release. Sorry, I tried.")

	print "release id: %s.html" % (release.id)

	disc.releasetypes = release.getTypes()

	disc.set_musicbrainz_tracks(release.getTracks())
	disc.releasedate = release.getEarliestReleaseDate()

	disc.artist = mp3names.FixArtist(release.artist.name)
	disc.album = release.title
	if year is not None:
		disc.year = year
	elif disc.releasedate is not None:
		disc.year = disc.releasedate[0:4]
	else:
		raise Exception("Unknown year: %s %s " % (`disc.artist`,`disc.album`))

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
		if asincount == 1:
			disc.asin = release.asin
		elif asincount == 0:
			print "WARNING: No ASIN for this release"
			disc.asin = None
		else:
			print "WARNING: Ambiguous ASIN. Select an ASIN and specify it using --release-asin"
			disc.asin = None
			
	# Set the compilation tag appropriately
	if musicbrainz2.model.Release.TYPE_COMPILATION in disc.releasetypes:
		disc.compilation = 1
	
	# Name the target folder differently for soundtracks
	if musicbrainz2.model.Release.TYPE_SOUNDTRACK in disc.releasetypes:
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

	if not noact:
		os.mkdir(newpath)

	# Get album art
	imageurl = get_album_art_url_for_asin(disc.asin)
	if imageurl is not None:
		print imageurl
		if not noact:
			urllib.urlretrieve(imageurl, os.path.join(newpath, "folder.jpg"))
	else:
		embedcovers = False

	# Deal with disc x of y numbering
	(albumname, discnumber, disctitle) = parse_album_name(disc.album)
	if discnumber is None:
		disc.number = 1
		disc.totalnumber = 1
	else:
		if disc.asin is None:
			raise Exception("This disc is part of a multi-disc set, but we have no ASIN!")

		disc.number = int(discnumber)
		discs = get_all_discs_in_album(disc, albumname)
		disc.totalnumber = len(discs)

	print "disc " + str(disc.number) + " of " + str(disc.totalnumber)
	flacname(disc, release, srcpath, newpath, embedcovers, noact)

def flacname(disc, release, srcpath, newpath, embedcovers=False, noact=False, move=False):
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
		if not noact:
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
			os.path.basename(track_artist.id), os.path.basename(mbtrack.id), disc.discid, disc.releasedate, disc.year,
			str(disc.compilation), str(disc.number), str(disc.totalnumber), str(disc.number), str(disc.totalnumber))
		
		if track.isrc is not None:
			flactags += "ISRC=%s\n" % track.isrc
		if disc.mcn is not None:
			flactags += "MCN=%s\n" % disc.mcn

		for rtype in disc.releasetypes:
			flactags += "MUSICBRAINZ_RELEASE_ATTRIBUTE=%s\n" % musicbrainz2.utils.getReleaseTypeName(rtype)

		proclist = ["metaflac", "--import-tags-from=-"]

		if embedcovers:
			proclist.append("--import-picture-from=" + os.path.join(newpath, "folder.jpg"))

		proclist.append(os.path.join(newpath, newfilename))

		if not noact:
			p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
			p.stdin.write(flactags.encode("utf8"))
			p.stdin.close()
			p.wait()

	print os.path.join(srcpath, disc.tocfilename) + " -> " + os.path.join(newpath, "data.toc")
	if not noact:
		shutil.copyfile(os.path.join(srcpath, disc.tocfilename), os.path.join(newpath, "data.toc"))
	#os.system("rm \"%s\" -rf" % srcpath)
	

if __name__ == "__main__":
	main()
	print "Success"
	sys.exit(0)
