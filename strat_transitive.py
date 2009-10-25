#
# Strategy:
#  Look up PUID's -> Track -> PUID's transitively.
import sets
import lookups

def generate_track_puid_possibilities(tracks):
	"""Return all track ids with matching the tracks.

	Args:
		track: A list of tracks to match against.
	
	Yields:
		All releated track_ids. There is a n:n mapping of puid's to tracks.
		Therefore all puid's that match a track should be the same song.
		Thus if PUIDa maps to TrackA, which also has PUIDb
		and PUIDb maps to TrackB too, then PUIDa should map to
		TrackB too...
	"""
	tracks = tracks[:]
	done_track_ids = sets.Set()
	done_puids=sets.Set()

	# Don't return the tracks that were passed in.
	for track in tracks:
		done_track_ids.add(track.id)

	while tracks:
		t = tracks.pop()
		#print "Looking for any tracks related to %s" % t.title
		if not t.puids:
			track = lookups.get_track_by_id(t.id)
		for puid in track.puids:
			if puid in done_puids:
				continue
			done_puids.add(puid)
			tracks2 = lookups.get_tracks_by_puid(puid)
			for t2 in tracks2:
				if t2.id in done_track_ids:
					continue
				done_track_ids.add(t2.id)
				yield t2
				tracks.append(t2)
				#print " via %s considering track: %s" % (puid, t2.title)

