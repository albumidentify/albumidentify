#!/usr/bin/python2.5
import sys
import fingerprint
import musicdns
import os
import lookups
import parsemp3
import musicbrainz2
import itertools
import pickle
import md5
import random
import shelve
import puidsubmit
import albumidentifyconfig

def output_list(l):
	l.sort()
	ret=[]
	start=l[0]
	end=l[0]
	for i in l[1:]:
		if end+1==i:
			end=i
			continue
		if start!=end:
			ret.append("%d-%d" % (start,end))
		else:
			ret.append("%d" % start)
		start=i
		end=i
	if start!=end:
		ret.append("%d-%d" % (start,end))
	else:
		ret.append("%d" % start)
	return "[%s]" % (",".join(ret))
		

key = 'a7f6063296c0f1c9b75c7f511861b89b'

def decode(frommp3name, towavname):
        if frommp3name.lower().endswith(".mp3"):
                os.spawnlp(os.P_WAIT,"mpg123","mpg123","--quiet","--wav",
                        towavname,frommp3name)
        elif frommp3name.lower().endswith(".flac"):
                os.spawnlp(os.P_WAIT,"flac","flac","-d", "--totally-silent", "-o", towavname,
                        frommp3name)

fileinfocache=shelve.open(os.path.expanduser("~/.albumidentifycachedb"),"c")

class FingerprintFailed(Exception):
	def __init__(self,fname):
		self.fname = fname

	def __str__(self):
		return "Failed to fingerprint track %s" % repr(self.fname)


def get_file_info(fname):
	print "identifying",fname
	#sys.stdout.write("identifying "+os.path.basename(fname)+"\r\x1B[K")
	#sys.stdout.flush()
	fhash = md5.md5(open(fname,"r").read()).hexdigest()
	if fhash in fileinfocache:
		return fileinfocache[fhash]
	# While testing this uses a fixed name in /tmp
	# and checks if it exists, and doesn't decode if it does.
	# This is for speed while debugging, should be changed with
	# tmpname later
	toname=os.path.join("/tmp/fingerprint.wav")
	if not os.path.exists(toname):
		sys.stdout.write("decoding"+os.path.basename(fname)+"\r\x1B[K")
		sys.stdout.flush()
		decode(fname,toname)
	sys.stdout.write("Generating fingerprint\r")
	sys.stdout.flush()
	(fp, dur) = fingerprint.fingerprint(toname)
	os.unlink(toname)

	sys.stdout.write("Fetching fingerprint info\r")
	sys.stdout.flush()
	(trackname, artist, puid) = musicdns.lookup_fingerprint(fp, dur, key)
	print "***",`artist`,`trackname`,puid
	if puid is None:
		raise FingerprintFailed(fname)
	sys.stdout.write("Looking up PUID\r")
	sys.stdout.flush()
	tracks = lookups.get_tracks_by_puid(puid)
	data=(fname,artist,trackname,dur,tracks,puid)
	if tracks!=[]:
		fileinfocache[fhash]=data
	else:
		print "Musicbrainz doesn't know about this track, not caching"
	return data

def get_dir_info(dirname):
	files=os.listdir(dirname)
	files.sort()
	tracknum=0
	trackinfo={}
	for i in files:
		if not (i.lower().endswith(".mp3") or i.lower().endswith(".flac")):
			print "Skipping non mp3/flac file",`i`
			continue
		tracknum=tracknum+1
		fname=os.path.join(dirname,i)
		trackinfo[tracknum]=get_file_info(fname)
	return trackinfo

def find_more_tracks(tracks):
	# There is a n:n mapping of puid's to tracks.
	# All puid's that match a track should be the same song.
	# Thus if PUIDa maps to TrackA, which also has PUIDb
	# and PUIDb maps to TrackB too, then PUIDa should map to
	# TrackB too...
	tracks=tracks[:]
	donetracks=[]
	donepuids=[]
	donetrackids=[]

	while tracks!=[]:
		t=tracks.pop()
		donetracks.append(t)
		yield t
		newt = lookups.get_track_by_id(t.id)
		for p in newt.puids:
			if p in donepuids:
				continue
			donepuids.append(p)
			ts = lookups.get_tracks_by_puid(p)
			for u in ts:
				if u.id in donetrackids:
					continue
				tracks.append(u)
				donetrackids.append(u.id)
					
def find_even_more_tracks(fname,tracknum,possible_releases):
	gotone = False
        if fname.lower().endswith(".flac"):
                return
	mp3data = parsemp3.parsemp3(fname)
	if "TIT2" not in mp3data["v2"]:
		return
	ftrackname = mp3data["v2"]["TIT2"]
	for (rid,v) in possible_releases.items():
		release = lookups.get_release_by_releaseid(rid)
		rtrackname = release.tracks[tracknum-1].title
		if rtrackname.lower() == ftrackname.lower():
			yield release.tracks[tracknum-1]


# We need to choose a track to expand out.
# We want to choose a track that's more likely to give us a result.  For
# For example, if we have a track that appears in several nearly complete
# albums, we probably don't need to expand it that frequently (but we still
# should occasionally).
def choose_track(possible_releases, track_generator, trackinfo):
	total=0
	track_prob={}
	for tracknum in range(len(trackinfo)):
		tracknum=tracknum+1
		if tracknum not in track_generator:
			continue
		track_prob[tracknum]=1
		total=total+1
		for release in possible_releases:
			if tracknum not in possible_releases[release]:
				track_prob[tracknum]+=len(possible_releases[release])**2
				total+=track_prob[tracknum]
	r=random.random()*total
	tot=0
	for tracknum in track_prob:
		if tracknum not in track_generator:
			continue
		tot+=track_prob[tracknum]
		if tot>=r:
			return tracknum
	return tracknum

def submit_shortcut_puids(releaseid,trackinfo):
	if not albumidentifyconfig.config.getboolean("albumidentify",
		"push_shortcut_puids"):
		print "Not submiting shortcut puids: not enabled in config"
		return
	print "Submitting shortcut puids to musicbrainz"
	for (tracknum,(fname,artist,trackname,dur,trackids,puid)) \
			in trackinfo.items():
		release = lookups.get_release_by_releaseid(releaseid)
		trackid=release.tracks[tracknum-1].id
		puidsubmit.submit_puid(trackid,puid)


def guess_album2(trackinfo):
	# trackinfo is
	#  <tracknum> => (fname,artist,trackname,dur,[mbtrackids])
	#
	# returns a list of possible release id's
	#
	# This version works by trying a breadth first search of releases to try
	# and avoid wasting a lot of time finding releases which are going to
	# be ignored.
	#
	# This function returns a list of release id's
	possible_releases={}
	failed_releases={}
	impossible_releases=[]
	track_generator={}
	completed_releases=[]
	for (tracknum,(fname,artist,trackname,dur,trackids,puid)) in trackinfo.iteritems():
		track_generator[tracknum]=itertools.chain(
					(track
						for track in trackids),
					find_more_tracks([
						track for track in trackids]),
					find_even_more_tracks(fname,
							tracknum,
							possible_releases)
					)

	track_counts={}
	track_prob={}
	for i in range(len(trackinfo)):
		track_counts[i+1]=0
		track_prob[i+1]=0
	old_possible_releases=None
	total=0
	if track_generator=={}:
		print "No tracks to identify?"
		return
	while track_generator!={}:
		tracknum = choose_track(possible_releases, track_generator, trackinfo)
		try:
			track = track_generator[tracknum].next()
		except StopIteration, si:
			# If there are no more tracks for this
			# skip it and try more.
			del track_generator[tracknum]
			print
			print "All possibilities for track",tracknum,"exhausted"
			print "puid:",trackinfo[tracknum][5]#[0].puids
			print "filename",trackinfo[tracknum][0]
			removed_releases={}
			for i in possible_releases.keys():
				# Ignore any release that doesn't have this
				# track, since we can no longer find it.
				if tracknum not in possible_releases[i]:
					removed_releases[i]=possible_releases[i]
					del possible_releases[i]
			if possible_releases=={}:
				print "No possible releases left"
				if removed_releases:
					print "Possible releases:"
					for releaseid in removed_releases:
						release = lookups.get_release_by_releaseid(releaseid)
						print release.artist.name,"-",release.title
						print "",release.tracks[tracknum-1].title
						print "",release.tracks[tracknum-1].id
						print "",output_list(removed_releases[releaseid])
				return
			#return
			continue

		for releaseid in (x.id for x in track.releases):
			#releaseid = track.releases[0].id

			if releaseid in impossible_releases:
				continue

			release = lookups.get_release_by_releaseid(releaseid)

			if len(release.tracks) != len(trackinfo):
				# Ignore release -- wrong number of tracks
				sys.stdout.write(release.title.encode("ascii","ignore")[:40]+": wrong number of tracks (%d not %d)\x1B[K\r" % (len(release.tracks),len(trackinfo)))
				sys.stdout.flush()
				impossible_releases.append(releaseid)
				continue

			found_tracknumber=lookups.track_number(release.tracks, track)
			if found_tracknumber != tracknum:
				#impossible_releases.append(releaseid)
				# Ignore release -- Wrong track position
				if releaseid in failed_releases:
					failed_releases[releaseid]= \
						failed_releases[releaseid]+1
				else:
					failed_releases[releaseid]=1
				if releaseid in possible_releases:
					#print "No longer considering",release.title,": doesn't have track at the right position (",tracknum,"expected at",found_tracknumber,")"
					#for i in possible_releases[releaseid]:
					#	track_counts[i]=track_counts[i]-1
					#del possible_releases[releaseid]
					pass
				else:
					sys.stdout.write(release.title.encode("ascii","ignore")[:40]+" (track at wrong position)\x1b[K\r")
					sys.stdout.flush()
				continue

			if releaseid in possible_releases:
				if tracknum not in possible_releases[releaseid]:
					possible_releases[releaseid].append(tracknum)
					track_counts[tracknum]=track_counts[tracknum]+1
					print "Found track",tracknum,"on",release.title,"(tracks found: %s)\x1b[K" % (output_list(possible_releases[releaseid]))
			else:
				possible_releases[releaseid]=[tracknum]
				track_counts[tracknum]=track_counts[tracknum]+1
				print "Considering",release.title,"\x1b[K"
				if possible_releases!={}:
					print "Currently Considering:"
					for i in possible_releases:
						print "",lookups.get_release_by_releaseid(i).title,"(tracks found: %s)" % (output_list(possible_releases[i])),failed_releases.get(i,0)
					print

			if len(possible_releases[releaseid])==len(trackinfo) and releaseid not in completed_releases:
				print release.title,"seems ok\x1b[K"
				submit_shortcut_puids(releaseid,trackinfo)
				yield releaseid
				completed_releases.append(releaseid)
			
def guess_album(trackinfo):
	releasedata={}
	for rid in guess_album2(trackinfo):
		release = lookups.get_release_by_releaseid(rid)
		albumartist=release.artist
		if musicbrainz2.model.Release.TYPE_SOUNDTRACK in release.types:
			directoryname = "Soundtrack"
		else:
			directoryname = albumartist.name
		#print albumartist.name,":",release.title+" ("+rid+".html)"
		releaseevents=release.getReleaseEvents()
		#print "Release dates:"
		#for ev in releaseevents:
		#	print " ",ev.date
		#print "Track:"
		tracks=release.getTracks()
		trackdata=[]
		for tracknum in range(len(tracks)):
			trk=tracks[tracknum]
			(fname,artist,trackname,dur,trackprints,puid) = trackinfo[tracknum+1]
			if trk.artist is None:
				artist=albumartist.name
				sortartist=albumartist.sortName
				artistid=albumartist.id
			else:
				artist=trk.artist.name
				sortartist=trk.artist.sortName
				artistid=trk.artist.id
			#print " ",tracknum+1,"-",artist,"-",trk.title,"%2d:%06.3f" % (int(dur/60000),(dur%6000)/1000),`fname`
			trackdata.append((tracknum+1,artist,sortartist,trk.title,dur,fname,artistid,trk.id))
		asin = lookups.get_asin_from_release(release)
		albuminfo = (
			directoryname,
			release.title,
			rid+".html",
			[x.date for x in releaseevents],
			asin,
			trackdata,
			albumartist,
			release.id,
		)
		yield albuminfo

if __name__=="__main__":
	trackinfo=get_dir_info(sys.argv[1])
	for (albumartist,release,rid,releases,asin,trackdata,albumartistid,releaseid) in guess_album(trackinfo):
		print albumartist,"-",release
		print "ASIN:",asin
		print "Release Dates:",
		for i in releases:
			print "",i
		for (tracknum,artist,sortartist,title,dur,fname,artistid,trkid) in trackdata:
			print "",tracknum,"-",artist,"-",title,"%2d:%06.3f" % (int(dur/60000),(dur % 60000)/1000)
			print " ",fname

