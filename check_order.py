#!/usr/bin/python

import sys
import os
import math
import time
sys.path.insert(0, os.path.expanduser("~/Projects/python-musicbrainz2-svn/src"))
import tag
import albumidentify
import sort
import lookups
import musicdns
from musicbrainz2.webservice import WebServiceError

class Logger:
	def __init__(self, releaseid):
		self.fp = open(os.path.expanduser("~/musicproblems"), "a")
		self.releaseid = releaseid
		self.written = False

	def write(self, msg):
		if not self.written:
			print "%s.html" % self.releaseid
			self.fp.write("\n\n%s.html\n" % self.releaseid)
			self.written = True
		print msg
		if not msg.endswith("\n"):
			msg+= "\n"
		self.fp.write(msg)

	def close(self):
		self.fp.close()


def test(release, file, track, tracknum, l):
	#print "file",file
	fp, dur = albumidentify.populate_fingerprint_cache(file)
	(trackname, artist, puid) = musicdns.lookup_fingerprint(fp, dur, albumidentify.key)
	#print "puid",puid,"trackname",trackname,"dur",(dur/1000)
	track = lookups.get_track_by_id(track.id)
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
	if release not in releaseToTrack:
		l.write("puid http://musicbrainz.org/show/puid/?puid=%s is not on track %s.html Might just have not been submitted" % (puid, track.id))
	elif len(releaseToTrack[release]) > 1:
		l.write("Track %d (%s.html)" % (tracknum, track.id))
		l.write("Puid http://musicbrainz.org/show/puid/?puid=%s" % puid)
		l.write("    This puid links to more than 1 track on the same release")
	
	if track.duration is not None and math.fabs(dur/1000-track.duration/1000) > 3:
		l.write("    Track duration and puid duration differ by >3s (track %d, puid %d)" % (track.duration/1000, dur/1000))
		l.write("    http://musicbrainz.org/show/puid/?puid=%s" % puid)
		l.write("    you may want to remove track %d" % tracknum)

def process(dirname):
	print "dir",dirname
	files = sort.sorted_dir(dirname)

	tags = tag.read_tags(os.path.join(dirname,files[0]))
	releaseid = tags[tag.ALBUM_ID]
	r = u"http://musicbrainz.org/release/"+releaseid
	l = Logger(dirname + " " + r)

	release = lookups.get_release_by_releaseid(releaseid[0:])
	for i in range(len(release.tracks)):
		track = release.tracks[i]
		file = os.path.join(dirname, files[i])
		test(r, file, track, i+1, l)
	l.close()

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "usage:",sys.argv[0],"<dirs>"
		sys.exit(1)
	
	for i in sys.argv[1:]:
		try:
			process(i)
		except WebServiceError, e:
			time.sleep(10)
			process(i)
