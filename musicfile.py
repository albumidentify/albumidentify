import subprocess
import lookups
import tag
import fingerprint
import musicdns
import albumidentifyconfig

# Used for reading.
musicdns_key = 'a7f6063296c0f1c9b75c7f511861b89b'

class MusicFile:
	def __init__(self,fname):
		self.fname = fname
		self.tracks = None
		self.fetchedpuid = False
		self.puid = None
		self.metadata = None

	def _fetchPUID(self):
		if self.fetchedpuid:
			return
		self.fetchedpuid = True
		try:
			self.fingerprint, self.dur \
				= fingerprint.populate_fingerprint_cache(self.fname)
			self.trackname, self.artist, self.puid \
				= musicdns.lookup_fingerprint(
					self.fingerprint, 
					self.dur, 
					musicdns_key)
		except:
			self.dur = None
			self.fingerprint = None
			raise
			return 
		if self.puid != None:
			return 
		# Submit the PUID if it's unknown
                genpuid_cmd = albumidentifyconfig.config.get("albumidentify","genpuid_command")
                musicdnskey = albumidentifyconfig.config.get("albumidentify","musicdnskey")
                if not genpuid_cmd:
			print "No genpuid command specified, can't submit fingerprint for %s" % self.fname
			return
                elif not musicdnskey:
                        print "No musicdnskey specified, can't submit fingerprint for %s" % self.fname
			return
		fingerprint.upload_fingerprint_any(
				self.fname, 
				genpuid_cmd,
				musicdnskey)
		memocache.remove_from_cache("delayed_lookup_fingerprint",
				self.fp,
				self.dur,
				musicdns_key)
		return None
		

	def _fetchmetadata(self):
		if self.metadata is None:
			self.metadata = tag.read_tags(self.fname)

	def getPUID(self):
		self._fetchPUID()
		return self.puid

	def getMDAlbumTitle(self):
		"Return the album title, or None if not known"
		self._fetchmetadata()
		return self.metadata.get(tag.ALBUM,None)

	def getMDTrackArtist(self):
		"Return the track artist, or None if not known"
		self._fetchmetadata()
		return self.metadata.get(tag.ARTIST,None)

	def getMDTrackTitle(self):
		"Return the track title, or None if not known"
		self._fetchmetadata()
		return self.metadata.get(tag.TITLE,None)

	def getDuration(self):
		"Return the duration, or None if not known"
		self._fetchPUID()
		return self.dur

	def getTracks(self):
		"Return the tracks"
		if self.tracks is None:
			if self.getPUID() is None:
				return []
			self.tracks = lookups.get_tracks_by_puid(self.getPUID())
		return self.tracks

	def getFilename(self):
		"Return the filename"
		self._fetchmetadata()
		return self.fname

