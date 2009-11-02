import musicbrainz2.model as mbmodel
import lastfm
import tag

# Release - Release
COVERS_AND_VERSIONS="http://musicbrainz.org/ns/rel-1.0#CoversAndVersions"
REMIXES="http://musicbrainz.org/ns/rel-1.0#Remixes"
COMPILATIONS="http://musicbrainz.org/ns/rel-1.0#Compilations"
LIVE_PERFORMANCE="http://musicbrainz.org/ns/rel-1.0#LivePerformance"
DJ_MIX="?"
REMASTER="http://musicbrainz.org/ns/rel-1.0#Remaster"
COVER="http://musicbrainz.org/ns/rel-1.0#Cover"
REMIX="http://musicbrainz.org/ns/rel-1.0#Remix"
REVIEW="http://musicbrainz.org/ns/rel-1.0#Review"
MASHESUP="http://musicbrainz.org/ns/rel-1.0#MashesUp"

FIRST_ALBUM_RELEASE="http://musicbrainz.org/ns/rel-1.0#FirstAlbumRelease"
PART_OF_SET="http://musicbrainz.org/ns/rel-1.0#PartOfSet"

# Release - URL
ASIN="http://musicbrainz.org/ns/rel-1.0#AmazonAsin"
WIKIPEDIA="http://musicbrainz.org/ns/rel-1.0#Wikipedia"
DISCOGS="http://musicbrainz.org/ns/rel-1.0#Discogs"
MUSICMOZ="http://musicbrainz.org/ns/rel-1.0#Musicmoz"
IMDB="http://musicbrainz.org/ns/rel-1.0#IMDb"
REVIEW="http://musicbrainz.org/ns/rel-1.0#Review"


def _add_track_relationship(tags, relationship):
	if relationship.getTargetType() == mbmodel.Relation.TO_URL:
		print "URL"
		print " dir=",relationship.getDirection()
		print " target=",relationship.getTarget()
		print " targetid=",relationship.getTargetId()
		print " targettype=",relationship.getTargetType()
		print " type=",relationship.getType()
	elif relationship.getTargetType() == mbmodel.Relation.TO_RELEASE:
		print "RELEASE"
		print " dir=",relationship.getDirection()
		print " target=",relationship.getTarget()
		print " targetid=",relationship.getTargetId()
		print " targettype=",relationship.getTargetType()
		print " type=",relationship.getType()
	else:
		print "Unknown type:",relationship.getTargetType()
	
def _add_album_relationship(tags, relationship):
	if relationship.getType() == ASIN:
		#print " ASIN:",relationship.getTargetId()
		pass
	elif relationship.getType() == WIKIPEDIA:
		#print " Wikipedia:",relationship.getTargetId()
		tags[tag.URL_WIKIPEDIA_RELEASE_SITE] = relationship.getTargetId()
	elif relationship.getType() == DISCOGS:
		#print " Discogs:",relationship.getTargetId()
		tags[tag.URL_DISCOGS_RELEASE_SITE] = relationship.getTargetId()
	elif relationship.getType() == MUSICMOZ:
		#print " Discogs:",relationship.getTargetId()
		tags[tag.URL_MUSICMOZ_RELEASE_SITE] = relationship.getTargetId()
	elif relationship.getType() == IMDB:
		#print " Discogs:",relationship.getTargetId()
		tags[tag.URL_IMDB_RELEASE_SITE] = relationship.getTargetId()
	elif relationship.getType() == REMASTER:
		print " Remaster of", relationship.getTargetId()
	elif relationship.getType() == PART_OF_SET:
		print " Part of set:", relationship.getTargetId()
	elif relationship.getType() == FIRST_ALBUM_RELEASE:
		print " First album release:", relationship.getTargetId()
	elif relationship.getType() == REMIX:
		print " Remix of:", relationship.getTargetId()
	elif relationship.getType() == REMIX:
		print " Review:", relationship.getTargetId()
	elif relationship.getTargetType() == mbmodel.Relation.TO_URL:
		print "URL"
		print " dir=",relationship.getDirection()
		print " target=",relationship.getTarget()
		print " targetid=",relationship.getTargetId()
		print " targettype=",relationship.getTargetType()
		print " type=",relationship.getType()
	elif relationship.getTargetType() == mbmodel.Relation.TO_RELEASE:
		print "RELEASE"
		print " dir=",relationship.getDirection()
		print " target=",relationship.getTarget()
		print " targetid=",relationship.getTargetId()
		print " targettype=",relationship.getTargetType()
		print " type=",relationship.getType()
	else:
		print "Unknown type:",relationship.getTargetType()

def get_tags(tags, mbrelease, mbtrack, artistname):
	# Fetch tags
	if tag.TAGS in tags:
		taglist = tags[tag.TAGS].split(",")

	taglist  = tags[tag.TAGS].split(",")
	taglist += [x.getValue() for x in mbtrack.getTags()]
	taglist += [x.getValue() for x in mbrelease.getTags()]

	taglist = list(set(taglist))

	tags[tag.TAGS] = ",".join(taglist)

	release_md = {}

	# Find relationships
	for i in mbrelease.getRelations():
		_add_album_relationship(tags, i)
	for i in mbtrack.getRelations():
		_add_track_relationship(tags, i)
