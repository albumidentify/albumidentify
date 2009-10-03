# Strategy:
#  Check for musicbrainz id's
import lookups
import util

def generate_from_metadata(file):
	"""Return track id's by looking up the name on music brainz

	Args:
		musicfile: The file containing the track in question.
	
	Yields:
		A set of track_id, by querying based on metadata tags
	"""
	trackid=file.getMDTrackID()
	if trackid:
		yield trackid

