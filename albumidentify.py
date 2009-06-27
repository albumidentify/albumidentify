#!/usr/bin/python2.5
import sys
import fingerprint
import musicdns
import os
import subprocess
import lookups
import parsemp3
import musicbrainz2
import itertools
import pickle
import hashlib
import random
import shelve
import albumidentifyconfig
import re
import sets
import time
import tempfile
import sort

# If set to True, this will force tracks to be found in order
# if set to False, tracks can be found in any order (has false positives)
FORCE_ORDER=True

# trackind's are 0 based
# tracknum's are 1 based

def update_progress(msg):
	if type(msg) == type(''):
		msg = msg.decode('utf8','ignore')
	sys.stdout.write(time.strftime("%H:%M:%S ")+msg.encode("ascii","ignore")+"\x1b[K\r\n")
	sys.stdout.flush()

def output_list(l):
	if not l:
		return "[]"
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
		
def list_difference(src,remove):
	res=src[:]
	for i in remove:
		if i in res:
			res.remove(i)
	return res

key = 'a7f6063296c0f1c9b75c7f511861b89b'

class FingerprintFailed(Exception):
	def __init__(self,fname):
		self.fname = fname

	def __str__(self):
		return "Failed to fingerprint track %s" % repr(self.fname)

class DecodeFailed(FingerprintFailed):
	def __init__(self,fname,reason):
		self.fname = fname
		self.reason = reason

	def __str__(self):
		return "Failed to decode file %s (%s)" % (repr(self.fname),self.reason)


def decode(fromname, towavname):
        if fromname.lower().endswith(".mp3"):
		args = ["mpg123","--quiet","--wav",towavname,fromname]
        elif fromname.lower().endswith(".flac"):
		args = ["flac","-d", "--totally-silent", "-f", "-o", towavname,fromname]
	elif fromname.lower().endswith(".ogg"):
		args = ["oggdec","--quiet","-o",towavname,fromname]
	else:
		raise DecodeFailed(fromname, "Don't know how to decode filename")
	
	try:
		ret = subprocess.call(args)
	except OSError,e:
		raise DecodeFailed(fromname, "Cannot find decoder %s" % args[0])
	if ret != 0:
		raise DecodeFailed(fromname, "Subprocess returned %d" % ret)

fileinfocache = None

def open_fileinfo_cache():
	global fileinfocache
	if fileinfocache is None:
		fileinfocache=shelve.open(
			os.path.expanduser("~/.albumidentifycachedb"),
			"c")

def populate_fingerprint_cache(fname):
	(fd,toname)=tempfile.mkstemp(suffix=".wav")
	try:
		update_progress("Decoding "+os.path.basename(fname))
		decode(fname,toname)
		update_progress("Generating fingerprint")
		(fp, dur) = fingerprint.fingerprint(toname)
	except Exception, e:
		print "Error creating fingerprint:",e
		raise e
	finally:
		if os.path.exists(toname):
			os.unlink(toname)

	return fp, dur

def hash_file(fname):
	update_progress("Hashing file")
	return hashlib.md5(open(fname,"r").read()).hexdigest()

def get_file_info(fname):
	fp = None
	dur = None
	fhash = hash_file(fname)
	open_fileinfo_cache()
	if fhash in fileinfocache:
		data = fileinfocache[fhash]
		if len(data) > 2:
			(fname2,artist,trackname,dur,tracks,puid)=data
			print "***",`puid`,`artist`,`trackname`,`os.path.basename(fname)`
			return (fname,artist,trackname,dur,tracks,puid)
		# FP only cached, musicbrainz had nothing last time.
		fp, dur = data
	if not fp:
		fp, dur = populate_fingerprint_cache(fname)
		fileinfocache[fhash]=(fp, dur)

	update_progress("Looking up PUID")
	(trackname, artist, puid) = musicdns.lookup_fingerprint(fp, dur, key)

	print "***",`puid`,`artist`,`trackname`,`os.path.basename(fname)`
	if puid is None:
                genpuid_cmd = albumidentifyconfig.config.get("albumidentify","genpuid_command")
                musicdnskey = albumidentifyconfig.config.get("albumidentify","musicdnskey")

                if not genpuid_cmd:
			print "No genpuid command specified, can't submit fingerprint for %s" % fname
                elif not musicdnskey:
                        print "No musicdnskey specified, can't submit fingerprint for %s" % fname
                else:
			# Submit the PUID for consideration by MusicDNS
			# We probably can't use it this time through (it takes MusicDNS up to
			# a few days to index new PUID's), but next time we're run hopefully we'll
			# figure it out.
                        (fd,toname) = tempfile.mkstemp(suffix = ".wav")
			decode(fname,toname)
			print "Submitting fingerprint to MusicDNS"
			os.system(genpuid_cmd + " " + musicdnskey + " " + toname)
			os.unlink(toname)
		lookups.remove_from_cache("delayed_lookup_fingerprint",fp,dur,key)
		return (fname,None,None,None,[],None)
	update_progress("Looking up tracks by PUID")
	tracks = lookups.get_tracks_by_puid(puid)
	update_progress("Done")
	data=(fname,artist,trackname,dur,tracks,puid)
	return data

def score_track(albumfreq,track):
	return reduce(lambda a,b:a+b, [albumfreq[release.id] for release in track.releases])

def get_dir_info(dirname):
	global fileinfocache
	files=sort.sorted_dir(dirname)
	trackinfo={}
	lastpuid=None
	lastfile=None
	albumfreq={}
	print "Examining",dirname
	for i in files:
		fname=os.path.join(dirname,i)
		trackinfo[fname]=get_file_info(fname)
		# If this is a duplicate of the previous track, ignore it.
		# Dedupe by PUID
		if lastpuid is not None and trackinfo[fname][5] == lastpuid:
			print "WARNING: Duplicate track ignored",`trackinfo[fname][0]`,"and",`trackinfo[lastfile][0]`
			del trackinfo[fname]
		else:
			lastpuid = trackinfo[fname][5]
			lastfile = fname
			for mbtrack in trackinfo[fname][4]:
				for release in mbtrack.releases:
					albumfreq[release.id]=albumfreq.get(release.id,0)+1
	# close the cache, we probably don't need it.
	# This means multiple concurrent runs don't stand on each others feet
	if fileinfocache:
		fileinfocache.close()
		fileinfocache=None
	# Sort by the most likely album first.
	for fileid in trackinfo:
		trackinfo[fileid][4].sort(lambda b,a:cmp(score_track(albumfreq,a),score_track(albumfreq,b)))
	return trackinfo

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
		track = lookups.get_track_by_id(t.id)
		for puid in track.puids:
			if puid in done_puids:
				continue
			done_puids.add(puid)
			tracks2 = lookups.get_tracks_by_puid(puid)
			for t2 in tracks2:
				if t2.id in done_track_ids:
					continue
				yield t2
				done_track_ids.add(t2.id)
				tracks.append(t2)
				#print " via %s considering track: %s" % (puid, t2.title)

def clean_name(name):
	name = re.sub(r"\(.*\)","",name)
	name = re.sub(r"\[.*\]","",name)
	name = re.sub(r"\{.*\}","",name)
	name = re.sub(r"[^A-Za-z0-9]","",name)
	return name.lower()

def _combinations(func,doneargs,todoargs):
	if todoargs==():
		for ret in func(*doneargs):
			yield ret
		return
	if type(todoargs[0]) not in [type(()),type([])]:
		for ret in _combinations(func,doneargs+(todoargs[0],),todoargs[1:]):
			yield ret
		return
	for arg in todoargs[0]:
		for ret in _combinations(func,doneargs+(arg,),todoargs[1:]):
			yield ret
	return
		

def combinations(func,*args):
	"""This function takes a function, and some arguments, some of which may be
collections.  For each sequence, the function is call combinatorially"""
	for ret in _combinations(func,(),args):
		yield ret

def generate_from_metadata(fname, num_tracks):
	"""Return track id's by looking up the name on music brainz

	Args:
		fname: The file containing the track in question.
	
	Yields:
		A set of track_id, by querying based on id3 tags
	"""
	if fname.endswith(".mp3"):
		md = parsemp3.parsemp3(fname)
		if "TALB" in md["v2"]:
			album = md["v2"]["TALB"]
		else:
			return # Give up
		if "TIT2" in md["v2"]:
			title = md["v2"]["TIT2"]
		else:
			return # Give up
		if "TPE1" in md["v2"]:
			artist = md["v2"]["TPE1"]
		else:
			return # Give up
	else:
		return # Can't get the title/artist
	
	update_progress("Searching by text lookup: "+`album`+" "+`artist`)
	for i in combinations(lookups.get_releases_by_cdtext,album, artist, num_tracks):
		release = lookups.get_release_by_releaseid(i.release.id)
		update_progress("Trying "+release.title+" by text lookup")
		for trackind in range(len(release.tracks)):
			rtrackname = release.tracks[trackind].title

			if clean_name(rtrackname) == clean_name(title):
				print "Using album based text comparison for",artist,album,"'s track",trackind+1,`rtrackname`
				yield lookups.get_track_by_id(release.tracks[trackind].id)
	
def comp_name(n1,n2):
	return cleanname(n1) == clean_name(n2)

def generate_track_name_possibilities(fname, fileid, possible_releases):
	"""Return all track ids matching the tracks.

	Args:
		fname: The file containing the track in question.
		track: A list of tracks to match against.
		possible_releases: Dictionary containing releases under consideration.
	
	Yields:
		All releated track_ids. Looks at all track names in the releases under
		consideration and case insensitively compares the tracks, returning any
		matches.
	"""
	if fname.lower().endswith(".flac"):
		return
	elif fname.lower().endswith(".ogg"):
		return
	try:
		mp3data = parsemp3.parsemp3(fname)
	except:
		# Parsing MP3s is a source of bugs... be robust here.
		print "Failed to parse mp3: %s" % fname
		return

	if "TIT2" not in mp3data["v2"]:
		return
	ftrackname = mp3data["v2"]["TIT2"]
	for (rid,v) in possible_releases.items():
		release = lookups.get_release_by_releaseid(rid)
		for trackind in range(len(release.tracks)):
			rtrackname = release.tracks[trackind].title

			# Don't bother if we've already found this track!
			if trackind+1 in v:
				continue

			if combinations(comp_name, rtrackname, ftrackname):
				print "Using text based comparison for track",trackind+1,`rtrackname`
				yield lookups.get_track_by_id(release.tracks[trackind].id)


# We need to choose a track to expand out.
# We want to choose a track that's more likely to give us a result.  For
# For example, if we have a track that appears in several nearly complete
# albums, we probably don't need to expand it that frequently (but we still
# should occasionally).
def choose_track(possible_releases, track_generator, trackinfo):
	track_prob={}
	for fileid in trackinfo:
		if fileid not in track_generator:
			continue
		# use the number of trackid's found as a hint, so we avoid
		# exhausting a track too soon.
		track_prob[fileid]=1+len(trackinfo[fileid][4])
		for release in possible_releases:
			if fileid not in possible_releases[release].values():
				track_prob[fileid]+=len(possible_releases[release])**2
	total = reduce(lambda a,b:a+b,track_prob.values())
	r=random.random()*total
	tot=0
	for fileid in track_prob:
		if fileid not in track_generator:
			continue
		tot+=track_prob[fileid]
		if tot>=r:
			return fileid
	return fileid

def giving_up(removed_releases,fileid):
	if removed_releases:
		print "Possible releases:"
		for releaseid in removed_releases:
			# If this release only has one track that we found,
			# and we have other possible releases, ignore this one.
			#
			# TODO: Actually, we should just display the top 2
			#  releases, by number of tracks found on it.
			if len(removed_releases[releaseid])<2 \
				and len(removed_releases)>1:
					continue
			release = lookups.get_release_by_releaseid(releaseid)
			print release.artist.name,"-",\
				release.title,"(%s)" % releaseid
			for trackind in range(len(release.tracks)):
				if (trackind+1) not in removed_releases[releaseid]:
					print "",trackind+1,release.tracks[trackind].id,release.tracks[trackind].title
				#release.tracks[tracknum-1].title
			#print "",release.tracks[tracknum-1].id
			print "",output_list(removed_releases[releaseid].keys())
	else:
		print "No possible releases left"

def end_of_track(possible_releases,impossible_releases,track_generator,trackinfo,fileid):
	# If there are no more tracks for this
	# skip it and try more.
	del track_generator[fileid]
	print "All possibilities for file",fileid,"exhausted\x1b[K"
	print "filename",trackinfo[fileid][0]
	if trackinfo[fileid][0].lower().endswith(".mp3"):
		md=parsemp3.parsemp3(trackinfo[fileid][0])
		if "TIT2" in md["v2"]:
			print "ID3 Title:",`md["v2"]["TIT2"]`
	print "puid:",trackinfo[fileid][5]#[0].puids
	removed_releases={}
	print "Current possible releases:"
	for i in possible_releases.keys():
		# Ignore any release that doesn't have this
		# track, since we can no longer find it.
		if fileid not in possible_releases[i].values():
			removed_releases[i]=possible_releases[i]
			del possible_releases[i]
			impossible_releases.append(i)
	if possible_releases=={}:
		giving_up(removed_releases, fileid)
		return
	for i in possible_releases:
		print "",lookups.get_release_by_releaseid(i).title,"(tracks found: %s)" % (output_list(possible_releases[i].keys()))

def verify_track(releaseid, release, possible_releases, impossible_releases, 
		trackinfo, fileid, track):
	if len(release.tracks) != len(trackinfo):
		# Ignore release -- wrong number of tracks
		update_progress(release.title.encode("ascii","ignore")[:40]+": wrong number of tracks (%d not %d)" % (len(release.tracks),len(trackinfo)))
		impossible_releases.append(releaseid)
		return False

	if FORCE_ORDER:
		found_tracknumber=lookups.track_number(release.tracks, track)
		file_ids = trackinfo.keys()
		file_ids = sort.sorted_list(file_ids)
		if found_tracknumber != file_ids.index(fileid)+1:
			update_progress(release.title[:40]+": track at wrong position")
			return False

	return True

def add_new_track(release, releaseid, possible_releases, fileid, track, trackinfo, impossible_releases):
	found_tracknumber=lookups.track_number(release.tracks, track)
	if releaseid in possible_releases:
		if found_tracknumber in possible_releases[releaseid]:
			# We already have a file for this track
			return
		if fileid in possible_releases[releaseid].values():
			# This file has already has a track
			return
		possible_releases[releaseid][found_tracknumber]=fileid
		print "Found track",found_tracknumber,"(",release.tracks[found_tracknumber-1].title,")","of",release.title,":",os.path.basename(fileid),"(tracks found: %s)\x1b[K" % (output_list(possible_releases[releaseid].keys()))
		return
	else:
		possible_releases[releaseid]={found_tracknumber:fileid}
		print "Considering new",release.artist.name,"-",release.title," (found track",found_tracknumber,")\x1b[K"

	# Right, lets see if we can find some other tracks quick smart
	for trackind in range(len(release.tracks)):
		# Don't waste time on things we've already found
		if (trackind+1) in possible_releases[releaseid]:
			continue
		track = lookups.get_track_by_id(release.tracks[trackind].id)
		for fileid in trackinfo:
			if fileid in possible_releases[releaseid].values():
				continue
			if trackinfo[fileid][5] in track.puids:
				# yay, found one.
				if verify_track(releaseid, 
						release,
						possible_releases,
						impossible_releases,
						trackinfo,
						fileid,
						track):
					possible_releases[releaseid][trackind+1]=fileid
					print " Also found track %02d: %s" % (trackind+1,release.tracks[trackind].title)
					break
	print " Found tracks: %s  Missing tracks: %s"% (
		output_list(possible_releases[releaseid].keys()),
		output_list(
			list_difference(range(1,len(release.tracks)+1),
			possible_releases[releaseid].keys())))



def guess_album2(trackinfo):
	# trackinfo is
	#  <fname> => (fname,artist,trackname,dur,[mbtrackids],puid)
	#
	# returns a list of possible release id's
	#
	# This version works by trying a breadth first search of releases to try
	# and avoid wasting a lot of time finding releases which are going to
	# be ignored.
	#
	# This function returns a list of release id's
	possible_releases={}
	impossible_releases=[]
	track_generator={}
	completed_releases=[]
	for (fileid,(fname,artist,trackname,dur,trackids,puid)) in trackinfo.iteritems():
		track_generator[fileid]=itertools.chain(
			(track for track in trackids),
			generate_track_puid_possibilities(trackids),
			generate_from_metadata(fname, len(trackinfo)),
			generate_track_name_possibilities(fname,
					fileid,
					possible_releases)
			)

	if track_generator=={}:
		print "No tracks to identify?"
		return

	while track_generator!={}:
		fileid = choose_track(possible_releases, track_generator, trackinfo)
		try:
			track = track_generator[fileid].next()
		except StopIteration, si:
			end_of_track(possible_releases,
				impossible_releases,
				track_generator,
				trackinfo,
				fileid)
			# If we have no more possible releases for the track
			# we're giving up on, we can't # get any more.
			# So give up now.
			if possible_releases == {}:
				return
			continue

		for releaseid in (x.id for x in track.releases):

			# Skip releases we've already seen before.
			if releaseid in impossible_releases:
				continue

			update_progress("Considering %s" %releaseid)
			release = lookups.get_release_by_releaseid(releaseid)

			# Is the track usable?
			if not verify_track(releaseid, 
					release, 
					possible_releases,
					impossible_releases,
					trackinfo,
					fileid,
					track):
				continue

			add_new_track(release, 
					releaseid, 
					possible_releases, 
					fileid, 
					track, 
					trackinfo, 
					impossible_releases)

			if len(possible_releases[releaseid])==len(trackinfo) \
					and releaseid not in completed_releases:
				print release.title,"seems ok\x1b[K"
				print "Musicbrainz Release Id:",release.id
				yield releaseid, possible_releases[releaseid]
				completed_releases.append(releaseid)
			
def guess_album(trackinfo):
	releasedata={}
	for rid,trackmap in guess_album2(trackinfo):
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
		for tracknum,fileid in trackmap.items():
			trk=tracks[tracknum-1]
			(fname,artist,trackname,dur,trackprints,puid) = trackinfo[fileid]
			if trk.artist is None:
				artist=albumartist.name
				sortartist=albumartist.sortName
				artistid=albumartist.id
			else:
				artist=trk.artist.name
				sortartist=trk.artist.sortName
				artistid=trk.artist.id
			#print " ",tracknum+1,"-",artist,"-",trk.title,"%2d:%06.3f" % (int(dur/60000),(dur%6000)/1000),`fname`
			trackdata.append((tracknum,
					artist,
					sortartist,
					trk.title,
					dur,
					fname,
					artistid,
					trk.id))
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


def process_dir(dir_path):
	"""Process a directory and guess the album in it.

	Args:
		dir_path: Full path to the directory to guess from.

	Returns:
		A generator which will yield album_info guesses. See guess_album for
		details of the guess format.
	"""
	trackinfo = get_dir_info(dir_path)
	return guess_album(trackinfo)


if __name__=="__main__":
	album_info = process_dir(sys.argv[1])
	(artist, release, rid, releases, asin, trackdata, albumartist,
			releaseid) = album_info.next()
	print albumartist,"-",release
	print "ASIN:",asin
	print "Release Dates:",
	for i in releases:
		print "",i
	for (tracknum,artist,sortartist,title,dur,fname,artistid,trkid) in trackdata:
		print "",tracknum,"-",artist,"-",title,"%2d:%06.3f" % (int(dur/60000),(dur % 60000)/1000)
		print " ",fname

