#!/usr/bin/env python
#
# Test out the various components of audio-fingerprinting
#

import fingerprint
import musicdns
import flacnamer
import sys

key = 'a7f6063296c0f1c9b75c7f511861b89b'

filename = sys.argv[1]

print "Fingerprinting..."
(fp, dur) = fingerprint.fingerprint(filename)
print "Duration: " + str(dur) + "ms"
print "Fingerprint: " + fp

print
print "MusicDNS lookup..."
(artist, trackname, puid) = musicdns.lookup_fingerprint(fp, dur, key)
print "Artist: " + artist
print "Title: " + trackname
print "PUID: " + puid

print 
print "Musicbrainz lookup by PUID..."

tracks = flacnamer.get_tracks_by_puid(puid)
for track in tracks:
	print "TrackID: " + track.id

