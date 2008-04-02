#
# discid.py
# Functions to generate discid's
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

import base64
import sha

def discid_base64_encode(binarystring):
	""" Encodes the binarystring into base64 (discid style).
	After encoding to base64, we substitute '/', '+' and '=' with '_',
	'.' and '-' in order for the string to be suitable for use in a
	URL.  
	"""
	e = base64.b64encode(binarystring)
	e = e.replace('/', '_')
	e = e.replace('+', '.')
	return e.replace('=', '-')

def to_hex(i, width=2):
	return hex(i)[2:].upper().zfill(width)

def generate_musicbrainz_discid(first_track_num, last_track_num, track_offsets):
	""" Returns a musicbrainz discId from TOC data.
		@param first_track_num The first track number
		@param last_track_num The last track number
		@param track_offsets Up to 100 track offsets. The first item of
		the list should be the offset of the leadout.
	"""
	s = sha.new()
	s.update(to_hex(first_track_num))
	s.update(to_hex(last_track_num))
	for o in track_offsets:
		s.update(to_hex(o, 8))
	for i in range(0, 100-len(track_offsets)):
		s.update("00000000")
	return discid_base64_encode(s.digest())


