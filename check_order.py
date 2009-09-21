#!/usr/bin/python

import sys
import os
import math
import time
import codecs
sys.path.insert(0, os.path.expanduser("~/Projects/python-musicbrainz2/src"))
import tag
import albumidentify
import sort
import lookups
import musicdns
from musicbrainz2.webservice import WebServiceError

class Logger:
	def __init__(self, dirname, releaseid):
		self.fp = codecs.open(os.path.expanduser("~/musicproblems"), "a", "utf-8")
		self.dirname = dirname
		self.releaseid = releaseid
		self.written = False

	def write(self, msg):
		if not self.written:
			print "%s %s.html" % (self.dirname, self.releaseid)
			self.fp.write("\n\n%s %s.html\n" % (self.dirname, self.releaseid))
			self.written = True
		print msg
		if not msg.endswith("\n"):
			msg+= "\n"
			self.fp.write(msg)

	def close(self):
		self.fp.close()


class Check:
	def __init__(self, dirname):
		self.dirname = unicode(dirname, "utf-8")
		self.fileTags = []

	def process(self):
		print "dir",self.dirname
		self.files = sort.sorted_dir(self.dirname)

		i = 1
		for file in self.files:
			tags = tag.read_tags(os.path.join(self.dirname,file))
			self.fileTags.append(tags)
			trck = tags[tag.TRACK_NUMBER]
			if "/" in trck:
				trck = trck.split("/")[0]
			trck = int(trck)
			if trck != i:
				print "%s Missing an expected track. Expected %d but got %d" % (dir, i, trck)
				fp = open(os.path.expanduser("~/musicproblems"), "a")
				fp.write("%s Missing an expected track. Expected %d but got %d" % (dir, i, trck))
				fp.close()
				return
			releaseid = u"http://musicbrainz.org/release/"+tags[tag.ALBUM_ID]
			i+=1
	
		self.l = Logger(self.dirname, releaseid)

		self.release = lookups.get_release_by_releaseid(releaseid)
		if len(self.files) != len(self.release.tracks):
			self.l.write("Fewer files than the release says (release: %d files %d)" % (len(self.release.tracks), len(self.files)))
			self.l.close()
			return
		
		i=0
		for file in self.files:
			self.test(i, os.path.join(self.dirname, file))
			i+=1

		self.l.close()

	def test(self, tracknum, file):
		#print "file",file
		(trackname, artist, puid) = self.calcpuid(file)
		if puid is None:
			return
		self.puid = puid
		#print "puid",puid,"trackname",trackname,"dur",(dur/1000)
		track = lookups.get_track_by_id(self.release.tracks[tracknum].id)
		#print "track len",(track.duration/1000)
		#print "puids",track.puids

		puidtracks = lookups.get_tracks_by_puid(puid)
		releaseToTrack = {}
		for pt in puidtracks:
			relId = pt.releases[0].id
			if relId not in releaseToTrack:
				releaseToTrack[relId] = [pt.id]
			else:
				releaseToTrack[relId].append(pt.id)
		if self.release.id not in releaseToTrack:
			self.l.write("puid http://musicbrainz.org/show/puid/?puid=%s is not on track %s.html Might just have not been submitted" % (puid, track.id))
		elif len(releaseToTrack[self.release.id]) > 1:
			self.l.write("Track %d (%s.html)" % (tracknum+1, track.id))
			self.l.write("Puid http://musicbrainz.org/show/puid/?puid=%s" % puid)
			self.l.write("    This puid links to more than 1 track on the same release")
			for t in releaseToTrack[self.release.id]:
				if t != track.id:
					self.crossref(t)
		elif len(releaseToTrack[self.release.id]) == 1:
			relTrack = os.path.basename(releaseToTrack[self.release.id][0])
			tagTrack = self.fileTags[tracknum][tag.TRACK_ID]
			if relTrack != tagTrack:
				self.l.write("Track %d (%s.html)" % (tracknum+1, track.id))
				self.l.write("    Based on the puid, this should be track %s, but it's %s" % (relTrack, tagTrack))

	def crossref(self, trackid):
		i=0
		for track in self.release.tracks:
			if trackid == track.id:
				self.l.write("    * also on track %d (%s)" % (i+1, track.title))
				(trackname, artist, thispuid) = self.calcpuid(os.path.join(self.dirname, self.files[i]))
				if self.puid != thispuid:
					self.l.write("      - but I don't think the puid is correct - remove this track")
					thistrack = lookups.get_track_by_id(trackid)
					if thispuid in thistrack.puids:
						self.l.write("        (I'm doubly sure, because the puid of this file is also in mb for the correct track)")
			i+=1

	def calcpuid(self, file):
		fp, dur = albumidentify.populate_fingerprint_cache(file)
		return musicdns.lookup_fingerprint(fp, dur, albumidentify.key)
	
if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "usage:",sys.argv[0],"<dirs>"
		sys.exit(1)
	
	for dir in sys.argv[1:]:
		Check(dir).process()
