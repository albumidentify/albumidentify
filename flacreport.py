#!/usr/bin/env python

# Generate a report on about the flacnamer process.
# Give this script a list of directories to report on
# i.e. ./flacreport.py cd-*

import sys
import os


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

for d in sys.argv[1:]:
	total = total + 1
	failure = 0
	fname=os.path.join(d, "result.txt")
	if not os.path.exists(fname):
		unprocessed = unprocessed + 1
		continue
	f = open(fname, 'r')
	s = f.read()
	f.close()
	if s.find("Ambiguous ASIN") != -1:
		amb_asin = amb_asin + 1
	if s.find("Exception: Couldn't find a") != -1:
		no_match = no_match + 1
		failure = 1
	elif s.find("No ASIN") != -1:
		no_asin = no_asin + 1
	elif s.find("Success") != -1:
		success = success + 1
	elif s.find("Ambiguous DiscID") != -1:
		amb_discid = amb_discid + 1
		failure = 1
	elif s.find("Exception: Unknown year") != -1:
		unk_year = unk_year + 1
		failure = 1
	elif s.find("This disc is part") != -1:
		multi = multi + 1
		failure = 1
	elif s.find("Exception:") != -1:
		unknown = unknown + 1
		failure = 1

	if failure == 1:
		fails = fails + 1
	else:
		success = success + 1
	s = ""

print "Total Discs    : %3d" % (total)
print "Failures       : %3d" % (fails)
print "  No Release   : %3d" % (no_match)
print "  Unknown year : %3d" % (unk_year)
print "  Ambig. Discid: %3d" % (amb_discid)
print "  Multi disc   : %3d" % (multi)
print "  Unknown Fails: %3d" % (unknown)
print "Successful     : %3d" % (success)
print "  No ASIN      : %3d" % (no_asin)
print "  Ambig. ASIN  : %3d" % (amb_asin)
print "Unprocessed    : %3d" % (unprocessed)
