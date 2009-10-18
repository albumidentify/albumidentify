import lastfm
import tag

def get_tags(tags, mbrelease, mbtrack, artistname):
	if tag.TAGS in tags:
		taglist = tags[tag.TAGS].split(",")

	taglist  = tags[tag.TAGS].split(",")
	taglist += [x.getValue() for x in mbtrack.getTags()]
	taglist += [x.getValue() for x in mbrelease.getTags()]

	taglist = list(set(taglist))

	tags[tag.TAGS] = ",".join(taglist)

