#!/usr/bin/python2.5

import os
import subprocess
import sys

class CDRipFailedException(Exception):
        def __init__(self,message):
                self.message=message
        def __str__(self):
                return "CD Rip Failed: %s" % self.message


def rip_cd(device, destpath):
        oldwd = os.getcwd()
        os.chdir(destpath)

        proclist = ["cdrdao", "read-cd", "--with-cddb", "--device", device, "data.toc"]
        p = subprocess.Popen(proclist)
        p.communicate()

        if p.returncode != 0:
                raise CDRipFailedException("cdrdao failed with returncode %i" % p.returncode)

        p2 = subprocess.Popen(["cueconvert", "data.toc", "data.cue"])
        p2.communicate()

        if p2.returncode != 0:
                raise CDRipFailedException("cueconvert failed with returncode %i" % p2.returncode)

        p3 = subprocess.Popen(["bchunk", "-s", "-w", "data.bin", "data.cue", "track"])
        p3.communicate()

        if p3.returncode != 0:
                raise CDRipFailedException("bchunk failed with returncode %i" % p3.returncode)

        os.chdir(oldwd)
        return True

if __name__ == "__main__":
        if len(sys.argv) == 3:
            rip_cd(sys.argv[1], sys.argv[2])
        else:
            print("Usage: "+sys.argv[0]+" <device> <destination>")
            sys.exit(1)
	sys.exit(0)
