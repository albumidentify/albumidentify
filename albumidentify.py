#!/usr/bin/python2.5
import sys
import fingerprint
import musicdns
import os
import lookups
import parsemp3

key = 'a7f6063296c0f1c9b75c7f511861b89b'

def decode(frommp3name, towavname):
	os.system("mpg123 --quiet --wav \"%(towavname)s\" \"%(frommp3name)s\"" % locals())


def get_dir_info(dirname):
	files=os.listdir(dirname)
	files.sort()
	tracknum=0
	trackinfo={}
	for i in files:
		if not i.lower().endswith(".mp3"):
			print "Skipping non mp3 file",`i`
			continue
		tracknum=tracknum+1
		fname=os.path.join(dirname,i)
		# While testing this uses a fixed name in /tmp
		# and checks if it exists, and doesn't decode if it does.
		# This is for speed while debugging, should be changed with
		# tmpname later
		toname=os.path.join("/tmp/",i[:-3]+"wav")
		#toname=os.path.join("/tmp/tmp.wav")
		if not os.path.exists(toname):
			print "decoding",fname
			decode(fname,toname)
		(fp, dur) = fingerprint.fingerprint(toname)
		#os.unlink(toname)

		(trackname, artist, puid) = musicdns.lookup_fingerprint(fp, dur, key)
		print "***",tracknum,`artist`,`trackname`,puid
		if puid is None:
			raise "Can't identify Track"
		tracks = lookups.get_tracks_by_puid(puid)
		print [ y.title for x in tracks for y in x.releases]
		trackinfo[tracknum]=(fname,artist,trackname,dur,tracks)
	return trackinfo


def check_release(r, track, tracknum, trackinfo, possible_releases):
	if tracknum>1 and (
		r.id not in possible_releases 
		or possible_releases[r.id] != tracknum-1):
		# Skip this album -- we know it's not going to
		# be a final candidate
		#print "skipping already worthless",r.id
		return None
	# Get the information about this release
	release = lookups.get_release_by_releaseid(r.id)
	# Skip if this album has the wrong number of tracks.
	if len(release.tracks) != len(trackinfo):
		print release.title,"has wrong number of tracks (expected",len(trackinfo)," not ",len(release.tracks),")"
		#for i in release.tracks:
		#	print ">",i.title
		return None
	# Skip if the tracks in the wrong place on this album
	found_tracknumber=lookups.track_number(release.tracks, track.title)
	if found_tracknumber != tracknum:
		print release.title,"doesn't have track in right position (expected",tracknum,"not",found_tracknumber,")"
		return None
	print release.title,"looks ok!"
	return release

def find_more_tracks(tracks):
	# There is a n:n mapping of puid's to tracks.
	# All puid's that match a track should be the same song.
	# Thus if PUIDa maps to TrackA, which also has PUIDb
	# and PUIDb maps to TrackB too, then PUIDa should map to
	# TrackB too...
	tracks=tracks[:]
	donetracks=[]
	donepuids=[]

	while tracks!=[]:
		t=tracks.pop()
		donetracks.append(t)
		newt = lookups.get_track_by_id(t.id)
		for p in newt.puids:
			if p not in donepuids:
				donepuids.append(p)
				ts = lookups.get_tracks_by_puid(p)
				for u in ts:
					if u not in donetracks and u not in tracks:
						print [y.title for y in u.releases]
						tracks.append(u)
	return donetracks


def guess_album(trackinfo):
	# tracinfo is
	#  <tracknum> => (fname,artist,trackname,dur,[mbtrackids])
	#
	# returns a list of possible release id's
	possible_releases={}
	for (tracknum,(fname,artist,trackname,dur,tracks)) in trackinfo.items():
		gotone = False
		print "???",tracknum,`artist`,`trackname`
		for track in tracks:
			for r in track.releases:
				release = check_release(r, track, tracknum, trackinfo, possible_releases)
				if release is None:
					continue
				if release.id in possible_releases:
					possible_releases[release.id] += 1
				else:
					possible_releases[release.id] = 1
				gotone = True
		if not gotone:
			print "No release found for this track (%d), trying harder" % tracknum
			newtracks = find_more_tracks(tracks)
			gotone = False
			for track in newtracks:
				for r in track.releases:
					release = check_release(r, track, tracknum, trackinfo, possible_releases)
					if release is None:
						continue
					if release.id in possible_releases:
						possible_releases[release.id] += 1
					else:
						possible_releases[release.id] = 1
					gotone = True
		if not gotone:
			print "Still cant find a release for this track.  Trying text matching"
			gotone = False
			mp3data = parsemp3.parsemp3(fname)
			if "TIT2" not in mp3data["v2"]:
				print "No v2 title tag, giving up"
				break
			ftrackname = mp3data["v2"]["TIT2"]
			for (rid,v) in possible_releases.iteritems():
				release = lookups.get_release_by_releaseid(rid)
				rtrackname = release.tracks[tracknum-1].title
				#print "tag name",ftrackname,"release name",rtrackname
				if rtrackname == trackname:
					gotone = True
					print " * track name matches release info."
					possible_releases[rid] += 1

		if not gotone:
			print "Sorry, still couldn't find a release for this track"
			break # Give up

	releasedata=[]

	for rid in [x for x in possible_releases if possible_releases[x]==len(trackinfo)]:
		release = lookups.get_release_by_releaseid(rid)
		albumartist=release.artist
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
			(fname,artist,trackname,dur,trackprints) = trackinfo[tracknum+1]
			if trk.artist is None:
				artist=albumartist.name
				artistid=albumartist.id
			else:
				artist=trk.artist.name
				artistid=trk.artist.id
			#print " ",tracknum+1,"-",artist,"-",trk.title,"%2d:%06.3f" % (int(dur/60000),(dur%6000)/1000),`fname`
			trackdata.append((tracknum+1,artist,trk.title,dur,fname,artistid,trk.id))
		asin = lookups.get_asin_from_release(release)
		albuminfo = (
			albumartist.name,
			release.title,
			rid+".html",
			[x.date for x in releaseevents],
			asin,
			trackdata,
			albumartist.id,
			release.id,
		)
		releasedata.append(albuminfo)
	return releasedata

if __name__=="__main__":
	trackinfo=get_dir_info(sys.argv[1])
	for (albumartist,release,rid,releases,asin,trackdata,albumartistid,releaseid) in guess_album(trackinfo):
		print albumartist,"-",release
		print "ASIN:",asin
		print "Release Dates:",
		for i in releases:
			print "",i
		for (tracknum,artist,title,dur,fname,artistid,trkid) in trackdata:
			print "",tracknum,"-",artist,"-",title,"%2d:%06.3f" % (int(dur/60000),(dur % 60000)/1000)
			print " ",fname

