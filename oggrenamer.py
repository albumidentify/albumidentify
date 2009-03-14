#!/usr/bin/python

import sys
import os
import lookups
import albumidentify
import musicbrainz2
import mp3names
import shutil
import subprocess

def print_usage():
	print "usage: " + sys.argv[0] + " <srcpath> <destpath> [OPTIONS]"
	print "  srcpath     A path containing oggs to rename"
	print "  srcpath     The path to rename the oggs to"
	print " OPTIONS:"
	print "  -n		  Don't actually tag and rename files"

def get_musicbrainz_release(dirname):
	""" Do a fingerprint based search for a matching release.
	"""

def main():
	if len(sys.argv) < 2:
		print_usage()
		sys.exit(1)

	noact = False

	for option in sys.argv[2:]:
		if option.startswith("-n"):
			noact = True
	
	srcpath = os.path.abspath(sys.argv[1])

	if not os.path.exists(srcpath):
		print_usage()
		sys.exit(2)

	if noact:
		print "Performing dry-run"

	print "Source path: " + srcpath

	dirinfo = albumidentify.get_dir_info(srcpath)
	data = albumidentify.guess_album(dirinfo)
	try:
		(directoryname, albumname, rid, events, asin, trackdata, albumartist, releaseid) = \
			data.next()
	except StopIteration,si:
		return None

	release = lookups.get_release_by_releaseid(releaseid)

	if release is None:
		raise Exception("Couldn't find a matching release. Sorry, I tried.")

	print "release id: %s.html" % (release.id)

	releasetypes = release.getTypes()

	release_tacks = release.getTracks()
	releasedate = release.getEarliestReleaseDate()

	release_artist = release.artist.name
	release_album = release.title
	if releasedate is not None:
		year = releasedate[0:4]
	else:
		raise Exception("Unknown year: %s %s " % (`release_artist`,`release_album`))

	dates = (year, releasedate)

	disc_compilation = 0
	disc_number = 0
	disc_totalnumber = 0
	disc_asin = lookups.get_asin_from_release(release, prefer=".co.uk")

	# Set the compilation tag appropriately
	if musicbrainz2.model.Release.TYPE_COMPILATION in releasetypes:
		disc_compilation = 1

	# Name the target folder differently for soundtracks
	if musicbrainz2.model.Release.TYPE_SOUNDTRACK in releasetypes:
		newpath = "Soundtrack - %s - %s" % (year, release_album)
	else:
		newpath = "%s - %s - %s" % (mp3names.FixArtist(release_artist), year, release_album)
	newpath = mp3names.FixFilename(newpath)

	destpath = os.path.abspath(sys.argv[2])
	newpath = os.path.join(destpath, "%s" % newpath)
	newpath = os.path.normpath(newpath)

	print "Destination path: " + newpath
	if (os.path.exists(newpath)):
		print "Destination path already exists, skipping"
		sys.exit(3)

	if not noact:
		os.mkdir(newpath)

	# Get album art
	imageurl = lookups.get_album_art_url_for_asin(disc_asin)
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
	(albumname, discnumber, disctitle) = lookups.parse_album_name(release_album)
	if discnumber is None:
		disc_number = 1
		disc_totalnumber = 1
	elif totaldiscs is not None:
		disc_totalnumber = totaldiscs
		disc_number = int(discnumber)
	else:
		disc_number = int(discnumber)
		discs = lookups.get_all_releases_in_set(release.id)
		disc_totalnumber = len(discs)
	
	disc_data = (disc_number, disc_totalnumber)

	print "disc " + str(disc_number) + " of " + str(disc_totalnumber)
	oggname(release, srcpath, trackdata, disc_data, dates, newpath, noact)

def oggname(release, srcpath, trackdata, disc_data, dates, newpath, noact=False, move=False):
	(disc_number, disc_totalnumber) = disc_data
	(year, releasedate) = dates
	release_artist = mp3names.FixArtist(release.artist.name)
	release_album = release.title
	for track in trackdata:
		tracknum = track[0]
		fname = track[5]

		track = release.getTracks()[tracknum-1]

		if release.isSingleArtistRelease():
			track_artist = release.artist
		else:
			track_artist = lookups.get_track_artist_for_track(track)

		newfilename = "%02d - %s - %s.ogg" % (tracknum, track_artist.name, track.title)
		newfilename = mp3names.FixFilename(newfilename)
		
		print fname + " -> " + os.path.join(newpath, newfilename)
		if not noact:
			shutil.copyfile(fname, os.path.join(newpath, newfilename))

		oggtags = '''TITLE=%s
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
DATE=%s
YEAR=%s
SORTARTIST=%s
SORTALBUMARTIST=%s
''' % (track.title, track.artist.name, release.artist.name, str(tracknum), str(len(release.tracks)), str(len(release.tracks)),
			release.title, os.path.basename(release.id), os.path.basename(release.artist.id),
			os.path.basename(track.artist.id), os.path.basename(track.id), releasedate, year,
			mp3names.FixArtist(track.artist.name), mp3names.FixArtist(release.artist.name))

#		if track.isrc is not None:
#			oggtags += "ISRC=%s\n" % track.isrc
#		if disc.mcn is not None:
#			oggtags += "MCN=%s\n" % disc.mcn
		if disc_totalnumber > 1:
			# only add total number of discs if it's a collection
			oggtags += "DISC=%s\nDISCC=%s\nDISCNUMBER=%s\nDISCTOTAL=%s\n" % \
					(str(disc_number), str(disc_totalnumber), str(disc_number), str(disc_totalnumber))

#		for rtype in disc.releasetypes:
#			oggtags += "MUSICBRAINZ_RELEASE_ATTRIBUTE=%s\n" % musicbrainz2.utils.getReleaseTypeName(rtype)

		proclist = ["vorbiscomment", "-R", "-c", "-", "-w"]
		proclist.append(os.path.join(newpath, newfilename))

		if not noact:
			try:
				p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
#				p.stdin.write(oggtags.encode("utf8"))
				(stdout, stderr) = p.communicate(oggtags.encode("utf8"))
				p.wait()
			except:
				print "exception"

if __name__ == '__main__':
	main()
	print "Success"
	sys.exit(0)
