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
import lookups

MUSICDNS_KEY='a7f6063296c0f1c9b75c7f511861b89b'

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


def get_releases_by_metadata(disc):
	""" Given a Disc object, use the performer, title and number of tracks to
	lookup the release in musicbrainz. This method returns a list of possible
	results, or the empty list if there were no matches. """

	releases = []

	q = ws.Query()
	filter = ws.ReleaseFilter(title=disc.title, artistName=disc.performer)
	rels = lookups.waitforws(lambda :q.getReleases(filter))
	
	# Filter out of the list releases with a different number of tracks to the
	# Disc.
	for rel in rels:
		release =rel.release  #get_release_by_releaseid(rel.id)
		if len(release.getTracks()) == len(disc.tracks):
			releases.append(rel)

	return releases

def get_release_by_fingerprints(disc):
	""" Try to determine the release of a disc based on audio fingerprinting each track. 
	"""
	possible_releases = {}
	tracknum = 0
	for t in disc.tracks:
		tracknum += 1

		tmp = os.tmpnam() + ".wav"
		if os.system("flac -d --totally-silent -o " +  tmp +  " " + t.filename)!=0:
			raise Exception("flac %s failed!" % t.filename )

		(fp, duration) = fingerprint.fingerprint(tmp)
		(artist, trackname, puid) = musicdns.lookup_fingerprint(fp, duration, MUSICDNS_KEY)
		os.unlink(tmp)
		if puid is None:
			print "Fingerprinting for " + t.filename + " failed."
			continue
		print "Fingerprinting for " + t.filename + " succeeded."
		print " PUID: " + puid

		tracks = lookups.get_tracks_by_puid(puid)
		for track in tracks:
			print "  Could be " + track.id + " (%s)" % track.title
			releases = track.getReleases()
			for r in releases:
				print "     Which is on " + r.id + " (%s)" % r.title
				release = lookups.get_release_by_releaseid(r.id)

				# Filter releases with the wrong number of tracks
				if len(release.getTracks()) != len(disc.tracks):
					print "      Which has " + str(len(release.getTracks())) + " tracks instead of " + str(len(disc.tracks))
					continue
				
				# Filter releases where this track is not in the correct
				# position.
				if lookups.track_number(release.getTracks(), track.title) != tracknum:
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
		return lookups.get_release_by_releaseid(disc.releaseid)

	# Otherwise, lookup the releaseid using the discid as a key
	filter = ws.ReleaseFilter(discId=disc.discid)
	results = lookups.waitforws(lambda :q.getReleases(filter=filter))
	if len(results) > 1:
		for result in results:
			print result.release.id
		raise Exception("Ambiguous DiscID. More than one release matches")

	# We have an exact match, use this.
	if len(results) == 1:
		releaseid = results[0].release.id
		return lookups.get_release_by_releaseid(results[0].release.id)

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
		release = lookups.get_release_by_releaseid(releases[0])
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
		elif option.startswith("--year="):
			year = option.split("=")[1].strip()
		elif option.startswith("-n"):
			noact = True

	srcpath = os.path.abspath(sys.argv[1])

	if not os.path.exists(srcpath):
		print_usage()
		sys.exit(2)
	
	if noact:
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
		disc.asin = lookups.get_asin_from_release(release)
			
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
	imageurl = lookups.get_album_art_url_for_asin(disc.asin)
	# Check for manual image
	if os.path.exists(os.path.join(srcpath, "folder.jpg")):
		print "Using existing image"
		if not noact:
			shutil.copyfile(os.path.join(srcpath, "folder.jpg"), os.path.join(newpath, "folder.jpg"))
	elif imageurl is not None:
		print imageurl
		if not noact:
			urllib.urlretrieve(imageurl, os.path.join(newpath, "folder.jpg"))
	else:
		embedcovers = False

	# Deal with disc x of y numbering
	(albumname, discnumber, disctitle) = lookups.parse_album_name(disc.album)
	if discnumber is None:
		disc.number = 1
		disc.totalnumber = 1
	else:
		if disc.asin is None:
			raise Exception("This disc is part of a multi-disc set, but we have no ASIN!")

		disc.number = int(discnumber)
		discs = lookups.get_all_discs_in_album(disc, albumname)
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
			track_artist = lookups.get_track_artist_for_track(mbtrack)

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
