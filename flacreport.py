#!/usr/bin/env python

# Generate a report on about the flacnamer process.
# Give this script a list of directories to report on
# i.e. ./flacreport.py cd-*

import sys
import os
import re

verbose=1

def log(*args):
	if verbose:
		print " ".join(args)


total = 0
no_match = 0
no_asin = 0
amb_asin = 0
amb_discid = 0
success = 0
unk_year = 0
multi = 0
fails = 0
unprocessed = 0
unknown = 0
too_short = 0
webfail=0
notdir=0

for d in sys.argv[1:]:
	total = total + 1
	failure = 0
	if not os.path.isdir(d):
		notdir+=1
		continue
	fname=os.path.join(d, "report.txt")
	if not os.path.exists(fname):
		unprocessed = unprocessed + 1
		continue
	f = open(fname, 'r')
	s = f.read()
	f.close()
	if s.find("Ambiguous ASIN") != -1:
		amb_asin = amb_asin + 1
	if s.find("Too few tracks to be reliable") != -1:
		m=re.match(r".*\(([0-9]+)\).*",s,re.DOTALL)
		too_short += 1
		failure = 1
		if m:
			log("Too short (%d): %s" % (int(m.groups()[0]),d))
		else:
			log("Too short: %s" % d)
	elif s.find("no releases found") != -1:
		no_match = no_match + 1
		failure = 1
		log("No release found:",d)
	elif s.find("No ASIN") != -1:
		no_asin = no_asin + 1
	elif s.find("Success") != -1:
		success = success + 1
	elif s.find("Ambiguous DiscID") != -1:
		amb_discid = amb_discid + 1
		failure = 1
	elif s.find("Unknown year") != -1:
		unk_year = unk_year + 1
		failure = 1
	elif s.find("This disc is part") != -1:
		multi = multi + 1
		failure = 1
	elif s.find("WebServiceError: HTTP Error 503: Service Temporarily Unavailable") != -1 \
	  or s.find("WebServiceError: HTTP Error 502: Bad Gateway") != -1 \
	  or s.find("ResourceNotFoundError: HTTP Error 404: Not Found") != -1 \
	  or s.find("IOError: ('http protocol error', 0, 'got a bad status line', None)") != -1 \
	  or s.find("IOError: [Errno socket error] (104, 'Connection reset by peer'") != -1:
		webfail += 1
		failure = 1
		log("Webservice failure:",d)
	elif s.find("UnicodeDecodeError") != -1:
		unknown += 1
		failure = 1
		log("Unicode failure")
	elif s.find("exception") != -1 or s.find("fail!") != -1 or s.find("Traceback") != -1:
		unknown = unknown + 1
		failure = 1
		log("Unknown:",d)

	if failure == 1:
		fails = fails + 1
	else:
		success = success + 1
	s = ""

print "Not directories: %3d" % notdir
print "Total Discs    : %3d" % (total)
print "Failures       : %3d (%.02f%%)" % (fails,fails*100.0/total)
print "  No Release   : %3d" % (no_match)
print "  Unknown year : %3d" % (unk_year)
print "  Ambig. Discid: %3d" % (amb_discid)
print "  Multi disc   : %3d" % (multi)
print "  Lookup Fail  : %3d" % (webfail)
print "  Unknown Fails: %3d" % (unknown)
print "  Too short    : %3d" % (too_short)
print "Successful     : %3d (%.02f%%)" % (success,success*100.0/total)
print "  No ASIN      : %3d" % (no_asin)
print "  Ambig. ASIN  : %3d" % (amb_asin)
print "Unprocessed    : %3d" % (unprocessed)
