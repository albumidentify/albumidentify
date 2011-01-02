import subprocess
import serialisemp3
import parsemp3
import os
import re

supported_extensions = [".mp3", ".ogg", ".flac"]

# http://musicbrainz.org/doc/PicardQt/TagMapping
# http://xiph.org/vorbis/doc/v-comment.html
# http://wiki.hydrogenaudio.org/index.php?title=Foobar2000:ID3_Tag_Mapping
# http://www.jthink.net/jaudiotagger/tagmapping.html
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
ARTIST_SORT = "ARTISTSORT"
ALBUM_ARTIST_SORT = "ALBUMARTISTSORT"
COMPILATION = "COMPILATION"
ISRC = "ISRC"
MCN = "MCN"
TRACK_TOTAL = "TRACKTOTAL"
DISC_NUMBER = "DISC"
DISC_TOTAL_NUMBER = "DISCC"
RELEASE_TYPES = "MUSICBRAINZ_RELEASE_ATTRIBUTE"
DISC_NAME = "DISCNAME"
GENRE = "GENRE"
MOOD = "MOOD"
TAGS = "TAGS"
IMAGE = "IMAGE"
URL_OFFICIAL_RELEASE_SITE = "URL_OFFICIAL_RELEASE_SITE"
URL_DISCOGS_RELEASE_SITE = "URL_DISCOGS_RELEASE_SITE"
URL_WIKIPEDIA_RELEASE_SITE = "URL_WIKIPEDIA_RELEASE_SITE"
URL_IMDB_RELEASE_SITE = "URL_IMDB_RELEASE_SITE"
URL_MUSICMOZ_RELEASE_SITE = "URL_MUSICMOZ_RELEASE_SITE"

URL_OFFICIAL_ARTIST_SITE = "URL_OFFICIAL_ARTIST_SITE"
URL_DISCOGS_ARTIST_SITE = "URL_DISCOGS_ARTIST_SITE"
URL_WIKIPEDIA_ARTIST_SITE = "URL_WIKIPEDIA_ARTIST_SITE"
URL_IMDB_ARTIST_SITE = "URL_IMDB_ARTIST_SITE"


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
	# These sort tags are used by taglib-sharp, gstreamer,
	#  and musicbrainz
        ARTIST_SORT : "ARTISTSORT",
        ALBUM_ARTIST_SORT : "ALBUMARTISTSORT",
        COMPILATION : "COMPILATION",
        ISRC : "ISRC",
        MCN : "MCN",
        DISC_NAME : "DISCNAME"
}

class TagFailedException(Exception):
	def __init__(self, reason):
		self.reason = reason

	def __str__(self):
		return self.reason

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

        if tags.has_key(GENRE):
                genres = [x.strip().title() for x in tags[GENRE].split(',')]
                for g in genres:
                        flactags += "GENRE=" + g + "\n"

        return flactags

def __tag_flac(filename, tags, noact = False, image = None):
        flactags = __gen_flac_tags(tags)
        proclist = ["metaflac", "--import-tags-from=-"]

        if image:
                proclist.append("--import-picture-from=" + image)

        proclist.append(filename)

        if not noact:
		try:
	                p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
	                p.stdin.write(flactags.encode("utf8"))
	                p.stdin.close()
	                p.wait()
		except OSError, e:
			raise TagFailedException("Could not write flac tags. Try installing metaflac")

def __tag_ogg(filename, tags, noact=False, image=None):
        oggtags = __gen_flac_tags(tags)
        proclist = ["vorbiscomment", "-R", "-c", "-", "-w", filename]

        if not noact:
		try:
	                p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
	                (stdout, stderr) = p.communicate(oggtags.encode("utf8"))
	                p.wait()
		except OSError, e:
			raise TagFailedException("Could not write ogg tags. Try installing vorbiscomment")


def tag(filename, tags, noact=False, image=None):
        if filename.lower().endswith(".flac"):
                return __tag_flac(filename, tags, noact, image)
        elif filename.lower().endswith(".ogg"):
                return __tag_ogg(filename, tags, noact, image)
        elif filename.lower().endswith(".mp3"):
		#return __tag_mp3(filename, tags, noact, image)
		#Tags are written out earlier
		return

        raise TagFailedException("Don't know how to tag this file type!")

def __remove_tags_flac(filename, noact):
	proclist = ["metaflac", "--remove", "--block-type=VORBIS_COMMENT,PICTURE", filename]
	if not noact:
		try:
			return subprocess.call(proclist)
		except OSError, e:
			raise TagFailedException("Could not read flac tags. Try installing metaflac")



def remove_tags(filename, noact=False):
	if filename.lower().endswith(".flac"):
		return __remove_tags_flac(filename, noact)
	elif filename.lower().endswith(".ogg"):
		# Tagging Oggs uses -w (replace) so don't remove
		return
	elif filename.lower().endswith(".mp3"):
		# Don't bother doing anything with mp3 at the moment.
		return

	raise TagFailedException("Don't know how to remove tags for this file (%s)!" % filename)

def get_mp3_tags(tags):
	assert tags[DATE] is not None
        id3tags= {
                "TIT2" : tags[TITLE],
                "TPE1" : tags[ARTIST],
		"TPE2" : tags[ALBUM_ARTIST],
                "TALB" : tags[ALBUM],
                "TYER" : tags[YEAR],
                "TDAT" : tags[DATE],
                "TRCK" : "%s/%s" % (tags[TRACK_NUMBER], tags[TRACK_TOTAL]),
                "UFID" : ("http://musicbrainz.org",tags[TRACK_ID].encode("iso8859-1")),
                "TXXX" : [("MusicBrainz Artist Id", tags[ARTIST_ID]),
                          ("MusicBrainz Album Id", tags[ALBUM_ID]),
			 ],
                # TCOM -- Composer
                # TDLY -- Playlist delay (preample)
                # TSOA -- Album sort order
                # TSOT -- Title Sort
                # TIPL -- Involved People
                # TPOS -- Part of set
                # TSST -- Set subtitle
                "COMM" : [('Tags',tags[TAGS])],
                }
	if ARTIST_SORT in tags:
		id3tags["TSOP"] = tags[ARTIST_SORT]
	if ALBUM_ARTIST_SORT in tags:
		id3tags["TSO2"] = tags[ALBUM_ARTIST_SORT]
	if MOOD in tags:
		id3tags["TMOO"] = tags[MOOD]
	if GENRE in tags:
		id3tags["TCON"] = tags[GENRE].split(",")
	if URL_OFFICIAL_RELEASE_SITE in tags:
		id3tags["WOAR"] = tags[URL_OFFICIAL_RELEASE_SITE]
	id3tags["WXXX"] = []
	if URL_DISCOGS_RELEASE_SITE in tags:
		id3tags["WXXX"].append(
			("DISCOGS_RELEASE",tags[URL_DISCOGS_RELEASE_SITE]))
	if URL_WIKIPEDIA_RELEASE_SITE in tags:
		id3tags["WXXX"].append(
			("WIKIPEDIA_RELEASE",tags[URL_WIKIPEDIA_RELEASE_SITE]))
	if URL_MUSICMOZ_RELEASE_SITE in tags:
		id3tags["WXXX"].append(
			("MUSICMOZ_RELEASE",tags[URL_MUSICMOZ_RELEASE_SITE]))
	if URL_DISCOGS_ARTIST_SITE in tags:
		id3tags["WXXX"].append(
			("DISCOGS_ARTIST",tags[URL_DISCOGS_ARTIST_SITE]))
	if URL_WIKIPEDIA_ARTIST_SITE in tags:
		id3tags["WXXX"].append(
			("WIKIPEDIA_ARTIST",tags[URL_WIKIPEDIA_ARTIST_SITE]))
	return id3tags

def read_tags(filename):
	"Returns a hash of tags, indexed by constants in this file"
        if filename.lower().endswith(".flac"):
	        return __read_tags_flac(filename)
        elif filename.lower().endswith(".mp3"):
		return __read_tags_mp3(filename)
	elif filename.endswith(".ogg"):
	        return __read_tags_ogg(filename)
 
        raise TagFailedException("Don't know how to read tags for this file type!")

def __read_tags_flac(filename):
	args = ["metaflac", "--export-tags-to=-", filename]
	try:
		flactags = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
	except OSError, e:
		raise TagFailedException("Could not read flac tags. Try installing metaflac")

	inverse_flac_map = dict([(v, k) for k, v in flac_tag_map.iteritems()])
	tags = {}
	for line in flactags.split("\n"):
		if line == "": break
		k = line.split("=")[0]
		v = line.split("=")[1]
		if k in inverse_flac_map.keys():
			tags[inverse_flac_map[k]] = v
		elif k == "DISC":
			tags[DISC_NUMBER] = v
		elif k == "DISCC":
			tags[DISC_TOTAL_NUMBER] = v

	try:
		args = ["metaflac", "--block-type=PICTURE", "--list", filename]
		process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
		blockdata = process[0].split('METADATA block #')
		
		picblocks = []
		for block in blockdata:
			block = block.split('\n')
			blocknum = block[0]
			encoding = ""
			mime = ""
			desc = ""
			pictype = ""
			for i in block:
				match = re.match("  MIME type: (.*)", i)
				if match:
					mime = match.group(1)
				match = re.match("  description: (.*)", i)
				if match:
					desc = match.group(1)
				match = re.match("  type: ([0-9]*)", i)
				if match:
					pictype = int(match.group(1))
			picblocks.append({'blocknum':blocknum,'encoding':encoding,'mime':mime,'desc':desc,'pictype':pictype})

		images = []
		for block in picblocks:
			args = ["metaflac", "--block-number=%s" % block['blocknum'], "--export-picture-to=-", filename]
			process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
			image = process[0]
			err = process[1]
			# metaflac writes to stderr if there is no image
			if err == "":
				images.append({'encoding':block['encoding'], 'mime':block['mime'], 'pictype':block['pictype'], 'desc':block['desc'], 'imagedata':image})
		tags[IMAGE] = images
	except OSError, e:
		raise TagFailedException("Could not read flac tags. Try installing metaflac")

	return tags

def __read_tags_ogg(filename):
	args = ["vorbiscomment", "-l", filename]
	try:
		oggtags = subprocess.Popen(args, stdout=subprocess.PIPE).communicate()[0]
	except:
		raise TagFailedException("Could not read ogg tags. Try installing vorbiscomment")
	inverse_flac_map = dict([(v, k) for k, v in flac_tag_map.iteritems()])
	tags = {}
	for line in oggtags.split("\n"):
		if line == "": break
		k = line.split("=")[0]
		v = line.split("=")[1]
		if k in inverse_flac_map.keys():
			tags[inverse_flac_map[k]] = v
		elif k == "DISC":
			tags[DISC_NUMBER] = v
		elif k == "DISCC":
			tags[DISC_TOTAL_NUMBER] = v
	return tags

def __read_tag_mp3_anyver(mp3tags,tagname):
	if tagname in mp3tags["v2"]:
		return mp3tags["v2"][tagname]
	if tagname in mp3tags["v1"]:
		return mp3tags["v1"][tagname]
	return None

def __read_image_mp3(images):

	if type(images) is not list:
		images = [images]

	processed = []
	for image in images:
		i = image.find("\x00")
		encoding = image[0:i]	
		image = image[i+1:]
		
		i = image.find("\x00")
		mime = image[0:i]
		image = image[i+1:]
		
		i = image.find("\x00")
		pictype = ord(image[0:i])
		image = image[i+1:]
	
		i = image.find("\x00")
		desc = image[0:i]
		
		imagedata = image[i+1:]
		
		processed.append({'encoding':encoding, 'mime':mime, 'pictype':pictype, 'desc':desc, 'imagedata':imagedata})

	return processed

def __read_tags_mp3(filename):
	data = parsemp3.readid3(filename)
	tags = {}
	tags[TITLE] = __read_tag_mp3_anyver(data,"TIT2")
	tags[ARTIST] = __read_tag_mp3_anyver(data,"TPE1")
	tags[ALBUM] = __read_tag_mp3_anyver(data,"TALB")
	tags[YEAR] = __read_tag_mp3_anyver(data,"TYER")
	tags[DATE] = __read_tag_mp3_anyver(data,"TDAT")
	if "APIC" in data["v2"]:
		images = data["v2"]["APIC"]
		images = __read_image_mp3(images)
		if len(images) > 0:
			tags[IMAGE] = images

	tag = __read_tag_mp3_anyver(data,"TRCK")
	if tag:
		parts = tag.strip().strip("\x00").split("/")
		if len(parts) == 2:
                        if parts[0] and parts[1]:
                                tags[TRACK_NUMBER] = int(parts[0])
                                tags[TRACK_TOTAL] = int(parts[1])
		else:
			tags[TRACK_NUMBER] = tag.strip().strip("\x00")
	tag = __read_tag_mp3_anyver(data,"TPOS")
	if tag:
		parts = tag.strip().strip("\x00").split("/")
		if len(parts) == 2:
                        if parts[0] and parts[1]:
                                tags[DISC_NUMBER] = int(parts[0])
                                tags[DISC_TOTAL_NUMBER] = int(parts[1])
		else:
			tags[DISC_NUMBER] = tag.strip().strip("\x00")
	tag = __read_tag_mp3_anyver(data,"TXXX")
	if tag:
		if type(tag) == type([]):
			parts = tag
		else:
			parts = [tag]
		for i in parts:
			if len(i.split("\0")) == 2:
				(k,v) = tuple(i.split("\0"))
				if k == "MusicBrainz Artist Id":
					tags[ARTIST_ID] = v.encode("ascii", "ignore")
				elif k == "MusicBrainz Album Id":
					tags[ALBUM_ID] = v.encode("ascii", "ignore")
	tag = __read_tag_mp3_anyver(data,"UFID")
	if tag:
		if type(tag) == type([]):
			parts = tag
		else:
			parts = [tag]
		for i in parts:
			if len(i.split("\0")) == 2:
				(k,v) = tuple(i.split("\0"))
				if k == "http://musicbrainz.org":
					tags[TRACK_ID] = v.encode("ascii", "ignore")

	return tags
