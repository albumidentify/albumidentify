#!/usr/bin/python

# Find out how many discs a collection has, and set those totals
# Usage: totalfix.py "Band - Album (disc *"

import os
import os.path
import sys
import glob
import subprocess

def fix_dir(dir, num, total):
	print "total of ",total
	for file in glob.glob(os.path.join(i, "*.flac")):
#		print file
		proclist = ["metaflac", "--remove-tag=DISC", "--remove-tag=DISCC", \
				"--remove-tag=DISCNUMBER", "--remove-tag=DISCTOTAL", file]
		subprocess.Popen(proclist, stdout=subprocess.PIPE).communicate()

		flactags='''DISC=%s
DISCC=%s
DISCNUMBER=%s
DISCTOTAL=%s
''' % (str(num), str(total), str(num), str(total))

		proclist = ["metaflac", "--import-tags-from=-", file]
		p = subprocess.Popen(proclist, stdin=subprocess.PIPE)
		p.stdin.write(flactags.encode("utf8"))
		p.stdin.close()
		p.wait()

for i in sys.argv[1:]:
	extra=0
	if i.endswith("/"):
		extra=1
	part = i[-7-extra:-1-extra]
	num = i[-2-extra:-1-extra]
	gl = i.replace(part, "disc *")
	print gl
	files = glob.glob(gl)
	fix_dir(i, num, len(files))
