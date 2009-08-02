
import subprocess
import parsemp3
import sys
try:
	import eyeD3
except ImportError:
	print "Cannot find eyeD3.  Please install python-eyed3 or similar"
	sys.exit(1)

supported_extensions = [".mp3", ".ogg", ".flac"]

TITLE = "TITLE"
ARTIST = "ARTIST"
ALBUM_ARTIST = "ALBUM_ARTIST"
TRACK_NUMBER = "TRACKNUMBER"
ALBUM = "ALBUM"
ALBUM_ID = "MUSICBRAINZ_ALBUMID"
ALBUM_ARTIST_ID = "MUSICBRAINZ_ALBUMARTISTID"
ARTIST_ID = "MUSICBRAINZ_ARTISTID"
TRACK_ID = "MUSICBRAINZ_TRACKID"
DISC_ID = "MUSICBRAINZ_DISCID"
YEAR = "YEAR"
DATE = "DATE"
SORT_ARTIST = "SORTARTIST"
SORT_ALBUM_ARTIST = "SORTALBUMARTIST"
COMPILATION = "COMPILATION"
ISRC = "ISRC"
MCN = "MCN"
TRACK_TOTAL = "TRACKTOTAL"
DISC_NUMBER = "DISC"
DISC_TOTAL_NUMBER = "DISCC"
RELEASE_TYPES = "MUSICBRAINZ_RELEASE_ATTRIBUTE"

flac_tag_map = {
        TITLE : "TITLE",
        ARTIST : "ARTIST",
        ALBUM_ARTIST : "ALBUM_ARTIST",
        TRACK_NUMBER : "TRACKNUMBER",
        ALBUM : "ALBUM",
        ALBUM_ID : "MUSICBRAINZ_ALBUMID",
        ALBUM_ARTIST_ID : "MUSICBRAINZ_ALBUMARTISTID",
        ARTIST_ID : "MUSICBRAINZ_ARTISTID",
        TRACK_ID : "MUSICBRAINZ_TRACKID",
        DISC_ID : "MUSICBRAINZ_DISCID",
        YEAR : "YEAR",
        DATE : "DATE",
        SORT_ARTIST : "SORTARTIST",
        SORT_ALBUM_ARTIST : "SORTALBUMARTIST",
        COMPILATION : "COMPILATION",
        ISRC : "ISRC",
        MCN : "MCN",
}

def __gen_flac_tags(tags):
        flactags = u""
        # Simple tags
        for k in flac_tag_map.keys():
                if tags.has_key(k):
                        flactags += flac_tag_map[k] + "=" + tags[k] + "\n"
        # More interesting tags
        if (tags.has_key(TRACK_TOTAL)):
                flactags += "TRACKTOTAL=" + tags[TRACK_TOTAL] + "\n"
                flactags += "TOTALTRACKS=" + tags[TRACK_TOTAL] + "\n"

        if tags.has_key(DISC_NUMBER):
                flactags += "DISC=" + tags[DISC_NUMBER] + "\n"
                flactags += "DISCNUMBER=" + tags[DISC_NUMBER] + "\n"
        if tags.has_key(DISC_TOTAL_NUMBER):
                flactags += "DISCC=" + tags[DISC_TOTAL_NUMBER] + "\n"
                flactags += "DISCTOTAL=" + tags[DISC_TOTAL_NUMBER] + "\n"

        if tags.has_key(RELEASE_TYPES):
                for t in tags[RELEASE_TYPES]:
			flactags += "MUSICBRAINZ_RELEASE_ATTRIBUTE=%s\n" % t
        return flactags

def __tag_flac(filename, tags, noact = False, image = None):
        flactags = __gen_flac_tags(tags)
        proclist = ["metaflac", "--import-tags-from=-"]

        if image:
                proclist.append("--import-picture-from=" + image)

        proclist.append(filename)

        if not noact:
                p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
                p.stdin.write(flactags.encode("utf8"))
                p.stdin.close()
                p.wait

def __tag_ogg(filename, tags, noact=False, image=None):
        oggtags = __gen_flac_tags(tags)
        proclist = ["vorbiscomment", "-R", "-c", "-", "-w", filename]

        if not noact:
                p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
                (stdout, stderr) = p.communicate(oggtags.encode("utf8"))
                p.wait()

def __tag_mp3(filename, tags, noact=False, image=None):
	tag = eyeD3.Tag()
	# Don't write tagging time
	tag.do_tdtg = False
	tag.link(filename)
	tag.header.setVersion(eyeD3.ID3_V2_3)
	tag.setTextEncoding(eyeD3.frames.UTF_16_ENCODING)
	tag.setArtist(tags[ARTIST])
	tag.setAlbum(tags[ALBUM])
	tag.setTitle(tags[TITLE])
	date = tags[DATE].split("-")
	if len(date) == 3:
		tag.setDate(date[0], date[1], date[2])
	elif len(date) == 2:
		tag.setDate(date[0], date[1])
	elif len(date) == 1:
		tag.setDate(date[0])
	else:
		tag.setDate(tags[YEAR])
	tag.setTrackNum((tags[TRACK_NUMBER],tags[TRACK_TOTAL]))
	if tags.has_key(DISC_NUMBER) and tags.has_key(DISC_TOTAL_NUMBER):
		tag.setDiscNum((tags[DISC_NUMBER], tags[DISC_TOTAL_NUMBER]))
	tag.addUserTextFrame("MusicBrainz Artist Id", tags[ARTIST_ID])
	tag.addUserTextFrame("MusicBrainz Album Id", tags[ALBUM_ID])
	tag.addUniqueFileID("http://musicbrainz.org", tags[TRACK_ID].encode("iso8859-1"))
	if image:
		tag.addImage(0x03, image)

	if not noact:
		# Write 2.3
		tag.update()
		# Write 1.1
		# eyed3 won't ignore encoding errors by default, so we'll re-encode them
		#  here, and ignore any errors.
		tag.header.setVersion(eyeD3.ID3_V1_1)
		tag.setTextEncoding(eyeD3.frames.LATIN1_ENCODING)
		# ouch
		old_encoding = eyeD3.LOCAL_ENCODING
		eyeD3.LOCAL_ENCODING="latin1"
		tag.setArtist(tags[ARTIST].encode("latin1", "replace"))
		tag.setAlbum(tags[ALBUM].encode("latin1", "replace"))
		tag.setTitle(tags[TITLE].encode("latin1", "replace"))
		tag.update()
		eyeD3.LOCAL_ENCODING=old_encoding

def tag(filename, tags, noact=False, image=None):
        if filename.lower().endswith(".flac"):
                return __tag_flac(filename, tags, noact, image)
        elif filename.lower().endswith(".ogg"):
                return __tag_ogg(filename, tags, noact, image)
        elif filename.lower().endswith(".mp3"):
		return __tag_mp3(filename, tags, noact, image)

        raise Exception("Don't know how to tag this file type!")

def __remove_tags_flac(filename, noact):
	proclist = ["metaflac", "--remove", "--block-type=VORBIS_COMMENT,PICTURE", filename]
	if not noact:
		ret = subprocess.call(proclist)

def __remove_tags_mp3(filename, noact):
	if not noact:
		tag = eyeD3.Tag()
		tag.link(filename)
		tag.remove()
		tag.update()

def remove_tags(filename, noact=False):
	if filename.lower().endswith(".flac"):
		return __remove_tags_flac(filename, noact)
	elif filename.lower().endswith(".ogg"):
		# Tagging Oggs uses -w (replace) so don't remove
		return
	elif filename.lower().endswith(".mp3"):
		return __remove_tags_mp3(filename, noact)

	raise Exception("Don't know how to remove tags for this file (%s)!" % filename)

def read_tags(filename):
        if filename.lower().endswith(".flac"):
	        return __read_tags_flac(filename)
        elif filename.lower().endswith(".mp3"):
		return __read_tags_mp3(filename)
	elif filename.endswith(".ogg"):
	        return __read_tags_ogg(filename)
 
        raise Exception("Don't know how to read tags for this file type!")

def __read_tags_flac(filename):
	args = ["metaflac", "--export-tags-to=-", filename]
	flactags = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
	inverse_flac_map = dict([(v, k) for k, v in flac_tag_map.iteritems()])
	tags = {}
	for line in flactags.split("\n"):
		if line == "": break
		k = line.split("=")[0]
		v = line.split("=")[1]
		if k in inverse_flac_map.keys():
			tags[inverse_flac_map[k]] = v
	return tags

def __read_tags_ogg(filename):
	args = ["vorbiscomment", "-l", filename]
	oggtags = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
	inverse_flac_map = dict([(v, k) for k, v in flac_tag_map.iteritems()])
	tags = {}
	for line in oggtags.split("\n"):
		if line == "": break
		k = line.split("=")[0]
		v = line.split("=")[1]
		if k in inverse_flac_map.keys():
			tags[inverse_flac_map[k]] = v
	return tags


def __read_tags_mp3(filename):
	data = parsemp3.parsemp3(filename)
	mp3tags = data["v2"]
	tags = {}
	if "TIT2" in mp3tags:
		tags[TITLE] = mp3tags["TIT2"]
	if "TPE1" in mp3tags:
		tags[ARTIST] = mp3tags["TPE1"]
	if "TALB" in mp3tags:
		tags[ALBUM] = mp3tags["TALB"]
	if "TYER" in mp3tags:
		tags[YEAR] = mp3tags["TYER"]
	if "TDAT" in mp3tags:
		tags[DATE] = mp3tags["TDAT"]
	if "TXXX" in mp3tags:
		if type(mp3tags["TXXX"]) == type([]):
			parts = mp3tags["TXXX"]
		else:
			parts = [mp3tags["TXXX"]]
		for i in parts:
			if len(i.split("\0")) == 2:
				(k,v) = tuple(i.split("\0"))
				if k == "MusicBrainz Artist Id":
					tags[ARTIST_ID] = v
				elif k == "MusicBrainz Album Id":
					tags[ALBUM_ID] = v
	if "UFID" in mp3tags:
		if type(mp3tags["UFID"]) == type([]):
			parts = mp3tags["UFID"]
		else:
			parts = [mp3tags["UFID"]]
		for i in parts:
			if len(i.split("\0")) == 2:
				(k,v) = tuple(i.split("\0"))
				if k == "http://musicbrainz.org":
					tags[TRACK_ID] = v

	return tags
