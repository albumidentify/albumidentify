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

for d in sys.argv[1:]:
	f = open(os.path.join(d, "result.txt"), 'r')
	s = f.read()
	f.close()
	total = total + 1
	failure = 0
	if s.find("Ambiguous ASIN") != -1:
		amb_asin = amb_asin + 1
	if s.find("Exception: Couldn't find a") != -1:
		no_match = no_match + 1
		failure = 1
	if s.find("No ASIN") != -1:
		no_asin = no_asin + 1
	if s.find("Success") != -1:
		success = success + 1
	if s.find("Ambiguous DiscID") != -1:
		amb_discid = amb_discid + 1
		failure = 1
	if s.find("Exception: Unknown year") != -1:
		unk_year = unk_year + 1
		failure = 1
	if s.find("This disc is part") != -1:
		multi = multi + 1
		failure  = 1

	if failure == 1:
		fails = fails + 1
	s = ""

print "Total Discs    : " + str(total)
print "Failures       : " + str(fails)
print "  No Match     : " + str(no_match)
print "  Unknown year : " + str(unk_year)
print "  Ambig. Discid: " + str(amb_discid)
print "  Multi disc   : " + str(multi)
print "Successful     : " + str(success)
print "  No ASIN      : " + str(no_asin)
print "  Ambig. ASIN  : " + str(amb_asin)
