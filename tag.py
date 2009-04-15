
import subprocess
import parsemp3

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
        flactags = ""
        # Simple tags
        for k in flac_tag_map.keys():
                if tags.has_key(k):
                        flactags += str(flac_tag_map[k]) + "=" + str(tags[k]) + "\n"
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

def tag(filename, tags, noact=False, image=None):
        if filename.endswith(".flac"):
                return __tag_flac(filename, tags, noact, image)
        elif filename.endswith(".ogg"):
                return __tag_ogg(filename, tags, noact, image)
        elif filename.endswith(".mp3"):
                # Don't bother doing anything with mp3 at the moment.
                return

        raise Exception("Don't know how to tag this file type!")

def get_mp3_tags(tags):
        return {
                "TIT2" : tags[TITLE],
                "TPE1" : tags[ARTIST],
                "TALB" : tags[ALBUM],
                "TYER" : tags[YEAR],
                "TDAT" : tags[DATE],
                "TRCK" : "%s/%s" % (tags[TRACK_NUMBER], tags[TRACK_TOTAL]),
                "UFID" : ("http://musicbrainz.org",tags[TRACK_ID].encode("iso8859-1")),
                "TXXX" : [("MusicBrainz Artist Id", tags[ARTIST_ID]),
                          ("MusicBrainz Album Id", tags[ALBUM_ID])],
                # TCOM -- Composer
                # TDLY -- Playlist delay (preample)
                # TSOA -- Album sort order
                # TSOP -- Performer sort
                # TSOT -- Title Sort
                # TIPL -- Involved People
                # TPOS -- Part of set
                # TSST -- Set subtitle
                "COMM" : ""
                }

def read_tags(filename):
        #if filename.endswith(".flac"):
	#        return __read_tags_flac(filename)
	#elif filename.endswith(".ogg"):
	#        return __read_tags_ogg(filename)
        if filename.endswith(".mp3"):
		return __read_tags_mp3(filename)

        raise Exception("Don't know how to read tags for this file type!")

def __read_tags_mp3(filename):
	data = parsemp3.parsemp3(filename)
	mp3tags = data["v2"]
	tags = {
		TITLE: mp3tags["TIT2"],
		ARTIST: mp3tags["TPE1"],
		ALBUM: mp3tags["TALB"],
		YEAR: mp3tags["TYER"]
		}
	if "TDAT" in mp3tags:
		tags[DATE] = mp3tags["TDAT"]
	if "TXXX" in mp3tags:
		if type(mp3tags["TXXX"]) == type([]):
			parts = mp3tags["TXXX"]
		else:
			parts = [mp3tags["TXXX"]]
		for i in parts:
			(k,v) = tuple(i.split("\0"))
			if k == "MusicBrainz Artist Id":
				tags[ARTIST_ID] = v
			elif k == "MusicBrainz Album Id":
				tags[ALBUM_ID] = v
	print tags
	return tags
