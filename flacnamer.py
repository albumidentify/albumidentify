#!/usr/bin/python2.5
#
# Script to automatically look up albums in the musicbrainz database and
# rename/retag FLAC files.
# Also gets album art via amazon web services
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

import sys
import os
from datetime import timedelta
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
import musicdns
import lookups
import albumidentify
import operator
import tag

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
        print "  --no-force-order    Don't require source files to be in order."
        print "                      May cause false positives."

def get_release_by_fingerprints(disc):
        """ Do a fingerprint based search for a matching release.

        """
        dirinfo = albumidentify.get_dir_info(disc.dirname)
        data = albumidentify.guess_album(dirinfo)
        try:
                (directoryname, albumname, rid, events, asin, trackdata, albumartist, releaseid) = \
                        data.next()
        except StopIteration,si:
		return None

        release = lookups.get_release_by_releaseid(releaseid)
        print "Got result via audio fingerprinting!"

        if disc.tocfilename:
                print "Suggest submitting TOC and discID to musicbrainz:"
                print "Release URL: " + release.id + ".html"
                print "Submit URL : " + submit.musicbrainz_submission_url(disc)

        # When we id by fingerprints, the sorted original filenames may not
        # match the actual tracks (i.e. out of order, bad naming, etc). Here we
        # have identified the release, so we need to remember the actual
        # filename for each track for later.
        sorted(trackdata, key=operator.itemgetter(0)) # sort trackdata by tracknum
        disc.clear_tracks()
        for (tracknum,artist,sortartist,title,dur,origname,artistid,trkid) in trackdata:
                t = toc.Track(tracknum)
                t.filename = origname
                disc.tracks.append(t)

        return release

def get_musicbrainz_release(disc):
	""" Given a Disc object, try a bunch of methods to look up the release in
	musicbrainz.  If a releaseid is specified, use this, otherwise search by
	discid, then search by CD-TEXT and finally search by audio-fingerprinting.
	"""
	# If a release id has been specified, that takes precedence
	if disc.releaseid is not None:
		return lookups.get_release_by_releaseid(disc.releaseid)

	# Otherwise, lookup the releaseid using the discid as a key
        if disc.discid is not None:
                results = lookups.get_releases_by_discid(disc.discid)
                if len(results) > 1:
                        for result in results:
                                print result.release.id + ".html"
                        print "Ambiguous DiscID, trying fingerprint matching"
                        return get_release_by_fingerprints(disc)

                # DiscID lookup gave us an exact match. Use this!
                if len(results) == 1:
                        releaseid = results[0].release.id
                        return lookups.get_release_by_releaseid(results[0].release.id)

	# Otherwise, use CD-TEXT if present to guess the release
	if disc.performer is not None and disc.title is not None:
		print "Trying to look up release via CD-TEXT"
		print "Performer: " + disc.performer
		print "Title    : " + disc.title
		results = lookups.get_releases_by_cdtext(performer=disc.performer, 
                                        title=disc.title, num_tracks=len(disc.tracks))
		if len(results) == 1:
			print "Got result via CD-TEXT lookup!"
			print "Suggest submitting TOC and discID to musicbrainz:"
			print "Release URL: " + results[0].release.id + ".html"
			print "Submit URL : " + submit.musicbrainz_submission_url(disc)
			return lookups.get_release_by_releaseid(results[0].release.id)
		elif len(results) > 1:
			for result in results:
				print result.release.id + ".html"
			print "Ambiguous CD-TEXT"
		else:
			print "No results from CD-TEXT lookup."

        # Last resort, fingerprinting
        print "Trying fingerprint search"
        return get_release_by_fingerprints(disc)

def main():
	if len(sys.argv) < 2:
		print_usage()
		sys.exit(1)

	releaseid = None
	embedcovers = True
	asin = None
	year = None
	noact = False
	totaldiscs = None

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
		elif option.startswith("--total-discs"):
			totaldiscs = option.split("=",1)[1].strip()
                elif option.startswith("--no-force-order"):
                        albumidentify.FORCE_ORDER = False

	srcpath = os.path.abspath(sys.argv[1])

	if not os.path.exists(srcpath):
		print_usage()
		sys.exit(2)
	
	if noact:
		print "Performing dry-run"

	print "Source path: " + srcpath

	if os.path.exists(os.path.join(srcpath, "data.toc")):
                disc = toc.Disc(cdrdaotocfile = os.path.join(srcpath, "data.toc"))
	elif os.path.exists(os.path.join(srcpath, "TOC")):
                disc = toc.Disc(cdrecordtocfile = os.path.join(srcpath, "data.toc"))
        else:
                disc = toc.Disc()
                disc.dirname = srcpath

        if disc.tocfilename:
                disc.discid = discid.generate_musicbrainz_discid(
                                disc.get_first_track_num(),
                                disc.get_last_track_num(),
                                disc.get_track_offsets())
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

	disc.artist = release.artist.name
	disc.album = release.title
	if year is not None:
		disc.year = year
		disc.releasedate = year
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
		disc.asin = lookups.get_asin_from_release(release, prefer=".co.uk")
			
	# Set the compilation tag appropriately
	if musicbrainz2.model.Release.TYPE_COMPILATION in disc.releasetypes:
		disc.compilation = 1
	
	# Name the target folder differently for soundtracks
	if musicbrainz2.model.Release.TYPE_SOUNDTRACK in disc.releasetypes:
		newpath = "Soundtrack - %s - %s" % (disc.year, disc.album)
	else:
		newpath = "%s - %s - %s" % (mp3names.FixArtist(disc.artist), disc.year, disc.album)
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
		if not noact:
                        try:
                                (f,h) = urllib.urlretrieve(imageurl, \
                                        os.path.join(newpath, "folder.jpg"))
                                if h.getmaintype() != "image":
                                        print "WARNING: Failed to retrieve coverart (%s)" % imageurl
                                        embedcovers = False
                        except:
                                print "WARNING: Failed to retrieve coverart (%s)" % imageurl
                                embedcovers = False
	else:
		embedcovers = False

	# Deal with disc x of y numbering
	(albumname, discnumber, disctitle) = lookups.parse_album_name(disc.album)
	if discnumber is None:
		disc.number = 1
		disc.totalnumber = 1
	elif totaldiscs is not None:
		disc.totalnumber = totaldiscs
		disc.number = int(discnumber)
	else:
		disc.number = int(discnumber)
		discs = lookups.get_all_releases_in_set(release.id)
		disc.totalnumber = len(discs)

	print "disc " + str(disc.number) + " of " + str(disc.totalnumber)
	name_album(disc, release, srcpath, newpath, embedcovers, noact)


supported_extensions = [".flac"]

def get_file_list(disc):
        # If the tracks don't have filenames attached, just use the files in
        # the directory as if they are already in order
        files = []
        if (disc.tracks[0].filename is None):
                files = [ x for x in os.listdir(disc.dirname) if x[x.rfind("."):] in supported_extensions ]
                files.sort()
        else:
                files = [ x.filename for x in disc.tracks ]
        return files

def name_album(disc, release, srcpath, newpath, embedcovers=False, noact=False, move=False):
        files = get_file_list(disc)

        if len(files) != len(disc.tracks):
                print "Number of files to rename (%i) != number of tracks in release (%i)" % (len(files), len(disc.tracks))
                return

        tracknum = 0
	for file in files:
                (root,ext) = os.path.splitext(file)
                tracknum = tracknum + 1
		track = disc.tracks[tracknum - 1]
		mbtrack = track.mb_track

		if release.isSingleArtistRelease():
			track_artist = release.artist
		else:
			track_artist = lookups.get_track_artist_for_track(mbtrack)

		newfilename = "%s - %s - %s%s" % (tracknum, track_artist.name, mbtrack.title, ext)
		newfilename = mp3names.FixFilename(newfilename)

                if newfilename.startswith("_silence_"):
                        continue

		print os.path.join(srcpath, file) + " -> " + os.path.join(newpath, newfilename)
		if not noact:
			shutil.copyfile(os.path.join(srcpath, file), os.path.join(newpath, newfilename))

                # Set up the tag list so that we can pass it off to the
                # container-specific tagger function later.
                tags = {}
                tags[tag.TITLE] = mbtrack.title
                tags[tag.ARTIST] = track_artist.name
                tags[tag.ALBUM_ARTIST] = disc.artist
                tags[tag.TRACK_NUMBER] = str(tracknum)
                tags[tag.TRACK_TOTAL] = str(len(disc.tracks))
                tags[tag.ALBUM] = disc.album
                tags[tag.ALBUM_ID] = os.path.basename(release.id)
                tags[tag.ALBUM_ARTIST_ID] = os.path.basename(release.artist.id)
                tags[tag.ARTIST_ID] = os.path.basename(track_artist.id)
                tags[tag.TRACK_ID] = os.path.basename(mbtrack.id)
                tags[tag.DATE] = disc.releasedate
                tags[tag.YEAR] = disc.year
                tags[tag.SORT_ARTIST] = mp3names.FixArtist(track_artist.name)
                tags[tag.SORT_ALBUM_ARTIST] = mp3names.FixArtist(disc.artist)

                if disc.discid:
                        tags[tag.DISC_ID] = disc.discid
                if disc.compilation:
                        tags[tag.COMPILATION] = "1"
                if track.isrc is not None:
                        tags[tag.ISRC] = track.isrc
                if disc.mcn is not None:
                        tags[tag.MCN] = disc.mcn
                for rtype in disc.releasetypes:
                        types = tags.get(tag.RELEASE_TYPES, [])
                        types.append(musicbrainz2.utils.getReleaseTypeName(rtype))
                        tags[tag.RELEASE_TYPES] = types
                if disc.totalnumber > 1:
                        tags[tag.DISC_NUMBER] = str(disc.number)
                        tags[tag.DISC_TOTAL_NUMBER] = str(disc.totalnumber)

                image = None
                if embedcovers:
                        image = os.path.join(srcpath, "folder.jpg")

                tag.tag(os.path.join(newpath, newfilename), tags, noact, image)

        if disc.tocfilename:
                print os.path.join(srcpath, disc.tocfilename) + " -> " + os.path.join(newpath, "data.toc")
                if not noact:
                        shutil.copyfile(os.path.join(srcpath, disc.tocfilename), os.path.join(newpath, "data.toc"))
	#os.system("rm \"%s\" -rf" % srcpath)
	

if __name__ == "__main__":
	main()
	print "Success"
	sys.exit(0)
