#!/usr/bin/python2.5
import sys
import fingerprint
import musicdns
import os
import lookups

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
			print "decoding"
			decode(fname,toname)
		(fp, dur) = fingerprint.fingerprint(toname)
		#os.unlink(toname)

		(trackname, artist, puid) = musicdns.lookup_fingerprint(fp, dur, key)
		print "***",tracknum,`artist`,`trackname`,puid
		tracks = lookups.get_tracks_by_puid(puid)
		print [ y.title for x in tracks for y in x.releases]
		trackinfo[tracknum]=(fname,artist,trackname,dur,tracks)
	return trackinfo


def check_release(r, track, tracknum, trackinfo, possible_releases):
	print `r.title`
	if tracknum>1 and (
		r.id not in possible_releases 
		or possible_releases[r.id] != tracknum-1):
		# Skip this album -- we know it's not going to
		# be a final candidate
		print "skipping already worthless",r.id
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
	if lookups.track_number(release.tracks, track.title) != tracknum:
		print release.title,"doesn't have track in right position"
		return None
	print release.title,"looks ok!"
	return release


def guess_album(trackinfo):
	# tracinfo is
	#  <tracknum> => (fname,artist,trackname,dur,[mbtrackids])
	#
	# returns a list of possible release id's
	possible_releases={}
	for (tracknum,(fname,artist,trackname,dur,tracks)) in trackinfo.items():
		gotone = False
		for track in tracks:
			print "***",tracknum,`artist`,`trackname`
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
			print "No release found for this track, trying harder"
			newtracks = []
			puids = []
			for t in tracks:
				newt = lookups.get_track_by_id(t.id)
				for p in newt.puids:
					if p not in puids:
						print p
						puids.append(p)
						ts = lookups.get_tracks_by_puid(p)
						for u in ts:
							if u not in newtracks and u not in tracks:
								newtracks.append(u)
			gotone = False
			for track in newtracks:
				print "***",tracknum,`artist`,`trackname`
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
				print "Sorry, still couldn't find a release for this track"

	releasedata=[]

	for rid in [x for x in possible_releases if possible_releases[x]==len(trackinfo)]:
		release = lookups.get_release_by_releaseid(rid)
		albumartist=release.artist
		print albumartist.name,":",release.title+" ("+rid+".html)"
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
			else:
				artist=trk.artist.name
			#print " ",tracknum+1,"-",artist,"-",trk.title,"%2d:%06.3f" % (int(dur/60000),(dur%6000)/1000),`fname`
			trackdata.append((tracknum+1,artist,trk.title,dur,fname))
		asin = lookups.get_asin_from_release(release)
		albuminfo = (
			albumartist.name,
			release.title,
			rid+".html",
			[x.date for x in releaseevents],
			asin,
			trackdata
		)
		releasedata.append(albuminfo)
	return releasedata

if __name__=="__main__":
	trackinfo=get_dir_info(sys.argv[1])
	#print trackinfo
	print guess_album(trackinfo)

