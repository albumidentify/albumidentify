import re
import sys
import time

def clean_name(name):
	"Clean up an mp3 name for comparison"
	name = re.sub(r"\(.*\)","",name)
	name = re.sub(r"\[.*\]","",name)
	name = re.sub(r"\{.*\}","",name)
	name = re.sub(r"[^A-Za-z0-9]","",name)
	return name.lower()

def comp_name(n1,n2):
	"Copmare two names for equality, after applying cleanups"
	return clean_name(n1) == clean_name(n2)


def _combinations(func,doneargs,todoargs):
	if todoargs==():
		for ret in func(*doneargs):
			yield ret
		return
	if type(todoargs[0]) not in [type(()),type([])]:
		for ret in _combinations(func,doneargs+(todoargs[0],),todoargs[1:]):
			yield ret
		return
	for arg in todoargs[0]:
		for ret in _combinations(func,doneargs+(arg,),todoargs[1:]):
			yield ret
	return
		

def combinations(func,*args):
	"""This function takes a function, and some arguments, some of which may be
collections.  For each sequence, the function is call combinatorially"""
	for ret in _combinations(func,(),args):
		yield ret

def update_progress(msg):
	"Display some progress"
	if type(msg) == type(''):
		msg = msg.decode('utf8','ignore')
	sys.stdout.write(time.strftime("%H:%M:%S ")+msg.encode("ascii","ignore")+"\x1b[K\r\n")
	sys.stdout.flush()

def output_list(l):
	"Give na list of integers, return a string with ranges collapsed"
	if not l:
		return "[]"
	l.sort()
	ret=[]
	start=l[0]
	end=l[0]
	for i in l[1:]:
		if end+1==i:
			end=i
			continue
		if start!=end:
			ret.append("%d-%d" % (start,end))
		else:
			ret.append("%d" % start)
		start=i
		end=i
	if start!=end:
		ret.append("%d-%d" % (start,end))
	else:
		ret.append("%d" % start)
	return "[%s]" % (",".join(ret))

def list_difference(src,remove):
	res=src[:]
	for i in remove:
		if i in res:
			res.remove(i)
	return res


