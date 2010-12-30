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

counts = {}

def add_count(f,*args):
	c = counts
	for i in args[:-1]:
		if i not in c:
			c[i]={}
		c = c[i]
	c[args[-1]] = c.get(args[-1],0) + 1
	log(" - ".join(args)+":",f)

def filenames():
	if len(sys.argv)>1:
		return sys.argv[1:]
	return (x.strip() for x in sys.stdin)

for d in filenames():
	if not os.path.isdir(d):
		add_count(d,"Other","Not a directory")
		continue
	fname=os.path.join(d, "report.txt")
	if not os.path.exists(fname):
		add_count(d,"Other","Unproccessed")
		continue
	f = open(fname, 'r')
	s = f.read()
	f.close()
	if s.find("Ambiguous ASIN") != -1:
		add_count(d,"Ambiguous ASIN")
	if s.find("Too few tracks to be reliable") != -1:
		m=re.match(r".*\(([0-9]+)\).*",s,re.DOTALL)
		if m:
			add_count(d,"Failed","Not enough tracks",m.groups()[0]+" tracks")
		else:
			add_count(d,"Failed","Not enough tracks","unknown")
	elif s.find("no releases found") != -1:
		add_count(d,"Failed","No Release Found")
	elif s.find("Ambiguous DiscID") != -1:
                if s.find("success!") == -1:
                        add_count(d,"Failed","Ambiguous DiscID")
                else:
                        add_count(d,"Success","Ambiguous DiscID resolved")
	elif s.find("couldn't determine year") != -1:
		add_count(d,"Failed","Unknown Year")
	elif s.find("This disc is part") != -1:
		add_count(d,"Failure","Multi Disc")
	elif s.find("TagReadFailedException") != -1:
		add_count(d,"Internal Failure","Failed to read tags")
	elif s.find("WebServiceError: HTTP Error 503: Service Temporarily Unavailable") != -1 \
	  or s.find("WebServiceError: HTTP Error 502: Bad Gateway") != -1 \
	  or s.find("ResourceNotFoundError: HTTP Error 404: Not Found") != -1 \
	  or s.find("IOError: ('http protocol error', 0, 'got a bad status line', None)") != -1 \
	  or s.find("IOError: [Errno socket error] (104, 'Connection reset by peer'") != -1 \
	  or s.find("ConnectionError") != -1 \
	  or s.find("ResponseError") != -1:
		add_count(d,"Internal Failure","Webservice Failure")
	elif s.find("UnicodeDecodeError") != -1 or s.find("UnicodeEncodeError")!=-1:
		add_count(d,"Internal Failure","Unicode Failure")
	elif s.find("IOError") != -1:
		l = s[s.find("IOError:"):].split("\n")[0].strip()
		add_count(d,"Internal Failure","Unknown failure",l)
	elif s.find("OSError") != -1:
		l = s[s.find("OSError:"):].split("\n")[0].strip()
		add_count(d,"Internal Failure","Unknown failure",l)
	elif s.find("GainFailedException") != -1:
		add_count(d,"Internal Failure","Unknown failure", "Replay Gain Failed")
	elif s.find("HTTP Error 400: Bad Request") != -1:
		add_count(d,"Internal Failure","Unknown failure", "Bad webservice request")
	elif s.find('exception') != -1:
		m=re.match(r".*<type '(.*)'>.*",s,re.DOTALL)
		if m:
			add_count(d,"Internal Failure","Unknown failure",m.group(1))
		else:
			add_count(d,"Internal Failure","Unknown failure","Fatal Exception")
	elif s.find("ZeroDivisionError") != -1:
		add_count(d,"Internal Failure","Unknown failure", "Division By Zero")
	elif s.find("TypeError") != -1:
		add_count(d,"Internal Failure","Unknown failure", "TypeError")
	elif s.find("exception") != -1 or s.find("fail!") != -1 or s.find("Traceback") != -1:
		add_count(d,"Internal Failure","Unknown failure","Unknown failure")
	elif s.find("WARNING:") != -1:
		l = s[s.find("Warning:"):].split("\n")[0].strip()
		add_count(d,"Warning",l)
	elif s.find("success!") != -1:
		add_count(d,"Success","No Problems")
	elif s.find("No ASIN") != -1:
		add_count(d,"Success","No ASIN")
	else:
		add_count(d,"Other","Dropped off")

	s = ""


def flatten(c):
	tot = 0
	for i in c:
		if type(c[i]) == type({}):
			r = [ ("  "+k,v) for k,v in flatten(c[i]) ]
			yield i,c[i][""]
			for k,v in r:
				yield k,v
			tot+= c[i][""]
		else:
			yield i,c[i]
			tot += c[i]
	c[""]=tot

outputs = list(flatten({"Total":counts}))

maxlen = 0
for k,v in outputs:
	if len(k) > maxlen:
		maxlen=len(k)

for k,v in outputs:
	print k+" "*(maxlen-len(k)),"%5d" % v,
	if v > outputs[0][1]*.01 and v != outputs[0][1]:
		print "(%3d%%)" % (v*100/outputs[0][1])
	else:
		print
