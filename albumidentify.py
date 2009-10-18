#!/usr/bin/python2.5
import fingerprint
import musicdns
import os
import lookups
import parsemp3
import musicbrainz2
import itertools
import random
import albumidentifyconfig
import sort
import util
import memocache
import musicfile

# Strategys
import strat_transitive
import strat_metadata
import strat_trackname
import strat_musicbrainzid

# If set to True, this will force tracks to be found in order
# if set to False, tracks can be found in any order (has false positives)
#FORCE_ORDER=True
FORCE_ORDER=False

# trackind's are 0 based
# tracknum's are 1 based

def duration_to_string(duration):
	duration = duration / 1000.0 # ms -> s
	if duration > 60:
		return "%02d:%05.2f" % (duration/60,duration%60)
	return "%05.2f" % (duration)

def score_track(albumfreq,track):
	""""Returns the total number of albums this release is on that other
tracks are on"""
	return reduce(lambda a,b:a+b, 
		[albumfreq[release.id] for release in track.releases])

def cmp_track(freq, tracka, trackb):
	return cmp(score_track(freq, tracka), score_track(freq, trackb))

def get_dir_info(dirname):
	files=sort.sorted_dir(dirname)
	trackinfo={}
	lastpuid=None
	lastfile=None
	albumfreq={}
	print "Examining",dirname
	for i in files:
		print "",i
		fname=os.path.join(dirname,i)
		trackinfo[fname]=musicfile.MusicFile(fname)
		# If this is a duplicate of the previous track, ignore it.
		# Dedupe by PUID
		if lastpuid is not None and trackinfo[fname].getPUID() == lastpuid:
			print "WARNING: Duplicate track ignored",repr(trackinfo[fname].getFilename()),"and",repr(trackinfo[lastfile].getFilename())
			del trackinfo[fname]
			continue
		lastpuid = trackinfo[fname].getFilename()
		lastfile = fname
		for mbtrack in trackinfo[fname].getTracks():
			for release in mbtrack.releases:
				albumfreq[release.id]=albumfreq.get(release.id,0)+1
	# Sort by the most likely album first.
	for fileid in trackinfo:
		trackinfo[fileid].getTracks().sort(
			lambda b,a:cmp_track(albumfreq,a,b))
	return trackinfo

# We need to choose a track to expand out.
# We want to choose a track that's more likely to give us a result.  For
# For example, if we have a track that appears in several nearly complete
# albums, we probably don't need to expand it that frequently (but we still
# should occasionally to prevent exploring deadends).
def choose_track(possible_releases, track_generator, trackinfo):
	track_prob={}
	for fileid in trackinfo:
		if fileid not in track_generator:
			continue
		# use the number of trackid's found as a hint, so we avoid
		# exhausting a track too soon.
		track_prob[fileid]=1+len(trackinfo[fileid].getTracks())
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
	if not removed_releases:
		print "No possible releases left"
		return
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
		print "%s - %s (%s)" % (
			release.artist.name,
			release.title,
			releaseid)
		for trackind in range(len(release.tracks)):
			if (trackind+1) in removed_releases[releaseid]:
				continue
			print " #%02d %s %s" % (
				trackind+1,
				release.tracks[trackind].id,
				release.tracks[trackind].title)
		print " %s" % (
			util.output_list(removed_releases[releaseid].keys())
			)

def end_of_track(possible_releases,impossible_releases,track_generator,trackinfo,fileid):
	# If there are no more tracks for this
	# skip it and try more.
	del track_generator[fileid]
	print "All possibilities for file",fileid,"exhausted\x1b[K"
	print "filename",trackinfo[fileid].getFilename()
	print "Metadata Title:",trackinfo[fileid].getMDTrackTitle()
	print "puid:",trackinfo[fileid].getPUID()
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
		print "",lookups.get_release_by_releaseid(i).title,"(tracks found: %s)" % (util.output_list(possible_releases[i].keys()))

def get_puids_for_release(releaseid):
	puids=[]
	release = lookups.get_release_by_releaseid(releaseid)
	for track in release.tracks:
		track = lookups.get_track_by_id(track.id)
		puids = puids + track.puids
	return puids

def verify_track(release, possible_releases, impossible_releases, 
			trackinfo, fileid, track):
	# Step One: Has this file already been found on this release?
	releaseid = release.id
	if releaseid in possible_releases and fileid in possible_releases[releaseid].values():
		util.update_progress("Already found on this release:" + fileid )
		return False
	# Step Two: Check for the right number of tracks
	if len(release.tracks) != len(trackinfo):
		# Ignore release -- wrong number of tracks
		util.update_progress(release.title.encode("ascii","ignore")[:40]+": wrong number of tracks (%d not %d)" % (len(release.tracks),len(trackinfo)))
		impossible_releases.append(releaseid)
		return False

	# Step Three: Have we found a file for this track on this release?
	tracknum = lookups.track_number(release.tracks, track)
	if releaseid in possible_releases and tracknum in possible_releases[releaseid]:
		util.update_progress("Already found a file for track %02d: %s" % (tracknum,possible_releases[releaseid][tracknum]))
		return False

	# Step Four: (optionally) Check that track 'n' maps to file 'n'.
	if FORCE_ORDER:
		found_tracknumber=lookups.track_number(release.tracks, track)
		file_ids = trackinfo.keys()
		file_ids = sort.sorted_list(file_ids)
		if found_tracknumber != file_ids.index(fileid)+1:
			util.update_progress(release.title[:40]+": track at wrong position")
			return False

	# Step Five: Make sure if there is another mapping on this album
	# that we don't accept this one.
 	if trackinfo[fileid].getPUID() in get_puids_for_release(releaseid):
		if trackinfo[fileid].getPUID() not in lookups.get_track_by_id(track.id).puids:
			print "Track exists elsewhere on this release"
			print "",fileid
			print "",track.title
			
			for ntrackind,ntrack in enumerate(release.tracks):
				ntrack = lookups.get_track_by_id(ntrack.id)
				if trackinfo[fileid].getPUID() in ntrack.puids:
					print " should be:",ntrack.title
					
			return False

	# Step Six: Make sure the song is within 10% of the length of the 
	# track we expect it to be.
	dur_ratio = track.getDuration() * 1.0 / trackinfo[fileid].getDuration()
	if dur_ratio < .9 or dur_ratio > 1.1:
		print "Track lengths differ"
		print " (%s) %s" % (
			duration_to_string(trackinfo[fileid].getDuration()),
			trackinfo[fileid].getFilename(),
			)
		print " (%s) %s" % (
			duration_to_string(track.getDuration()),
			track.title,
			)
		return False

	# Well, after passing through that gauntlet, we might consider this track!
	return True

def add_new_track(release, possible_releases, fileid, track, trackinfo, impossible_releases):
	releaseid = release.id
	found_tracknumber=lookups.track_number(release.tracks, track)
	if releaseid in possible_releases:
		assert found_tracknumber not in possible_releases[releaseid]
		assert fileid not in possible_releases[releaseid].values(),(fileid,possible_releases[releaseid])
		possible_releases[releaseid][found_tracknumber]=fileid
		print "Found track",found_tracknumber,"(",release.tracks[found_tracknumber-1].title,")","of",release.title,":",os.path.basename(fileid),"(tracks found: %s)\x1b[K" % (util.output_list(possible_releases[releaseid].keys()))
		return
	else:
		possible_releases[releaseid]={found_tracknumber:fileid}
		print "Considering new %s - %s (found track %d)\x1b[K" % (
			release.artist.name,
			release.title,
			found_tracknumber)

	# Right, lets see if we can find some other tracks quick smart
	for trackind in range(len(release.tracks)):
		# Don't waste time on things we've already found
		if (trackind+1) in possible_releases[releaseid]:
			continue
		track = lookups.get_track_by_id(release.tracks[trackind].id)
		for fileid in trackinfo:
			if fileid in possible_releases[releaseid].values():
				continue
			if trackinfo[fileid].getPUID() in track.puids:
				# yay, found one.
				if verify_track(release,
						possible_releases,
						impossible_releases,
						trackinfo,
						fileid,
						track):
					possible_releases[releaseid][trackind+1]=fileid
					print " Also found track %02d: %s" % (trackind+1,release.tracks[trackind].title)
					break
	print " Found tracks: %s" % (
		util.output_list(possible_releases[releaseid].keys())),
	if util.list_difference(range(1,len(release.tracks)+1),
			possible_releases[releaseid].keys()):
		print " Missing tracks: %s"% (
			util.output_list(
				util.list_difference(range(1,len(release.tracks)+1),
				possible_releases[releaseid].keys())))
	else:
		print

def guess_album2(trackinfo):
	# trackinfo is
	#  <fname> => <musicfile.MusicFile>
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

	if trackinfo=={}:
		print "No tracks to identify?"
		return

	for (fileid,file) in trackinfo.iteritems():
		track_generator[fileid]=itertools.chain(
			file.getTracks(),
			strat_musicbrainzid.generate_from_metadata(file),
			strat_transitive.generate_track_puid_possibilities(
				file.getTracks()),
			strat_metadata.generate_from_metadata(
				file,
				len(trackinfo)),
			strat_trackname.generate_track_name_possibilities(	
					file,
					fileid,
					possible_releases)
			)

	while track_generator!={}:
		fileid = choose_track(
				possible_releases,
				 track_generator,
				 trackinfo)
		try:
			track = track_generator[fileid].next()
		except StopIteration:
			end_of_track(
				possible_releases,
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

			util.update_progress("Considering %s" %releaseid)
			release = lookups.get_release_by_releaseid(releaseid)

			# Is the track usable?
			if not verify_track(release, 
					possible_releases,
					impossible_releases,
					trackinfo,
					fileid,
					track):
				continue

			add_new_track(release, 
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
		releaseevents=release.getReleaseEvents()
		tracks=release.getTracks()
		trackdata=[]
		for tracknum,fileid in trackmap.items():
			trk=tracks[tracknum-1]
			musicfile = trackinfo[fileid]
			if trk.artist is None:
				artist=albumartist.name
				sortartist=albumartist.sortName
				artistid=albumartist.id
			else:
				artist=trk.artist.name
				sortartist=trk.artist.sortName
				artistid=trk.artist.id
			trackdata.append((
					tracknum,			
					artist,
					sortartist,
					trk.title,
					musicfile.getDuration(),
					musicfile.getFilename(),
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

def tracks_in_order(trackdata):
	fids = [x[5] for x in trackdata]
	fids = sort.sorted_list(fids)
	for (tracknum,artist,sortartist,title,dur,fname,artistid,trkid),fid in zip(trackdata,fids):
		if fname != fid:
			return False
	return True


def guess_best_album(trackinfo):
	count = 0
	possibilities={}
	for (directoryname, 
			title,
			rid, 
			revents, 
			asin, 
			trackdata, 
			albumartist, 
			releaseid) in guess_album(trackinfo):
		count+=1
		possibilities[releaseid]=title
		if tracks_in_order(trackdata):
			yield (directoryname, 
				title, 
				rid,
				revents, 
				asin, 
				trackdata, 
				albumartist, 
				releaseid)
	if count == 0:
		print "Unable to identify album"
	if count == 1:
		yield (directoryname, 
			release.title, 
			rid,
			revents, 
			asin, 
			trackdata, 
			albumartist, 
			releaseid)
	if count > 1:
		print "Too many out of order tracks"
		print "Possible releases:"
		for releaseid,releasetitle in possibilities.items():
			print " %s: %s" % (releaseid, releasetitle)
	
def process_dir(dir_path):
	"""Process a directory and guess the album in it.

	Args:
		dir_path: Full path to the directory to guess from.

	Returns:
		A generator which will yield album_info guesses. See guess_album for
		details of the guess format.
	"""
	trackinfo = get_dir_info(dir_path)
	return guess_best_album(trackinfo)

if __name__=="__main__":
	import sys
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

