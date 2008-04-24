#!/usr/bin/python
import toc
import sys
import os
import urlparse
import urllib
import discid

def parse_toc(srcpath):
        if os.path.exists(os.path.join(srcpath, "data.toc")):
                tocfilename = "data.toc"
        elif os.path.exists(os.path.join(srcpath, "TOC")):
                tocfilename = "TOC"
        else:   
                print "No TOC in source path!"
                sys.exit(4)

        return toc.Disc(cdrdaotocfile=os.path.join(srcpath, tocfilename))

def musicbrainz_submission_url(disctoc):
	return  urlparse.urlunparse((
		'http',
		'musicbrainz.org',
		'/bare/cdlookup.html',
		'',
		urllib.urlencode({ 'id' : discid.generate_musicbrainz_discid(
				disctoc.get_first_track_num(),
				disctoc.get_last_track_num(),
				disctoc.get_track_offsets()),
		  'toc' : " ".join(map(str,[
			disctoc.get_first_track_num(),
			disctoc.get_last_track_num()]+disctoc.get_track_offsets())),
		  'tracks' : len(disctoc.get_track_offsets()) }),
		''
	))

if __name__ == "__main__":
	disctoc=parse_toc(sys.argv[1])
	print "Title:",disctoc.title
	print "Performer:",disctoc.performer
	print musicbrainz_submission_url(disctoc)

