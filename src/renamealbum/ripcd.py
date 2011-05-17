#!/usr/bin/python

import os
import subprocess
import sys
import time
import CD

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

def main():
    import optparse
    opts = optparse.OptionParser(usage="%s <device> [destination]" % sys.argv[0])
    opts.add_option("-c",
	    "--continuous",
	    dest="continuous",
	    default=False,
	    action="store_true",
	    help="After each rip eject the tray and wait for more cds. Ripping will start as soon as another cd is inserted"
    )

    (options, args) = opts.parse_args()

    if len(args) == 2:
	destdir = args[1]
    elif len(args) == 1:
	destdir = os.getcwd()
    else:
	opts.print_help()
	sys.exit(2)

    device = args[0]

    if not options.continuous:
	dest = os.path.join(destdir,("cd-%s" % (time.strftime("%Y%m%d%H%M%S"),)))
	if not os.path.exists(dest):
		os.mkdir(dest)
	rip_cd(device,dest)
    else:
	try:
		CD.status(device)
	except CD.PlatformNotSupportedException, e:
		print "-c is not currently supported on your platform"
		sys.exit(1)
	print "Press Ctrl+c to exit"
	while True:
		if CD.status(device) == 1:
			dest = os.path.join(destdir,("cd-%s" % (time.strftime("%Y%m%d%H%M%S"),)))
			if not os.path.exists(dest):
				os.mkdir(dest)
			# backoff an extra 2 seconds
			try:
				time.sleep(2)
			except KeyboardInterrupt, e:
				sys.exit(0)
			rip_cd(device,dest)
			CD.eject(device)
		else:
			try:
				time.sleep(2)
			except KeyboardInterrupt, e:
				sys.exit(0)

if __name__ == "__main__":
    main()
