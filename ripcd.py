#!/usr/bin/python

import os
import subprocess
import sys
import time

class CDRipFailedException(Exception):
        def __init__(self,message):
                self.message=message
        def __str__(self):
                return self.message


def rip_cd(device, destpath):
        oldwd = os.getcwd()
        print "ripping device %s to %s" % (device, destpath)
        os.chdir(destpath)

        proclist = ["cdrdao", "read-cd", "--with-cddb", "--device", device, "data.toc"]
	try:
	        p = subprocess.Popen(proclist)
	        p.communicate()
	except OSError, e:
		raise CDRipFailedException("cdrdao not installed. Cannot rip CD")

        if p.returncode != 0:
                raise CDRipFailedException("cdrdao failed with returncode %i" % p.returncode)

	try:
	        p2 = subprocess.Popen(["cueconvert", "data.toc", "data.cue"])
	        p2.communicate()
	except OSError, e:
		raise CDRipFailedException("cueconvert not installed. Cannot rip CD")

        if p2.returncode != 0:
                raise CDRipFailedException("cueconvert failed with returncode %i" % p2.returncode)

	try:
	        p3 = subprocess.Popen(["bchunk", "-s", "-w", "data.bin", "data.cue", "track"])
	        p3.communicate()
	except OSError, e:
                raise CDRipFailedException("bchunk not installed. Cannot rip CD")

        if p3.returncode != 0:
                raise CDRipFailedException("bchunk failed with returncode %i" % p3.returncode)

        os.chdir(oldwd)
        return True

if __name__ == "__main__":
    if len(sys.argv) == 3:
        rip_cd(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 2:
	dest = "cd-%s" % (time.strftime("%Y%m%d%H%M%S"),)
        os.mkdir(dest)
        rip_cd(sys.argv[1], dest)
    else:
        print("Usage: %s <device> [destination]" % (sys.argv[0],))
        sys.exit(1)
