#
# fingerprint.py
# Tools for fingerprinting audio
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
# (C) 2009 Perry Lorier <perry@coders.net>
#

try:
	import libofa
except:
	pass
import wave
import subprocess
import tempfile
import os
import memocache
import util
import hashlib

def fingerprint_wave(file):
	""" Take a WAVE filename (or an open File object) and use libofa to
	determine its fingerprint.  Returns a tuple of the fingerprint and the
	length in milliseconds, which can be used to query musicdns.  """

	wav = wave.open(file, 'rb')
	if wav.getnchannels() == 1:
		stereo = 0
	elif wav.getnchannels() == 2:
		stereo = 1
	else:
		wav.close()
		raise Exception("Only 1 or 2 channel WAV files supported")

	width = wav.getsampwidth()
	if width != 2:
		wav.close()
		raise Exception("Only 16-bit sample widths supported")

	srate = wav.getframerate()	

	buffer = wav.readframes(wav.getnframes())
	wav.close()

	ms = (len(buffer) / 2)/(srate/1000)
	if stereo == 1:
		ms = ms / 2
	
	fprint = libofa.create_print(buffer, libofa.BYTE_ORDER_LE, len(buffer) / 2,
								srate, stereo);

	return (fprint, ms)

def fingerprint(filename):
	if "libofa" not in globals():
		raise Exception("Fingerprinting not supported")
	if filename.endswith(".wav"):
		result = fingerprint_wave(filename)
	else:
		raise Exception("Format not supported")
	return result

class DecodeFailed(Exception):
	def __init__(self,fname,reason):
		self.fname = fname
		self.reason = reason

	def __str__(self):
		return "Failed to decode file %s (%s)" % (repr(self.fname),self.reason)

def _decode(fromname, towavname):
        if fromname.lower().endswith(".mp3"):
		args = ["mpg123","--quiet","--wav",towavname,fromname]
        elif fromname.lower().endswith(".flac"):
		args = ["flac","-d", "--totally-silent", "-f", "-o", towavname,fromname]
	elif fromname.lower().endswith(".ogg"):
		args = ["oggdec","--quiet","-o",towavname,fromname]
	else:
		raise DecodeFailed(fromname, "Don't know how to decode filename")
	
	try:
		util.update_progress("Decoding file")
		ret = subprocess.call(args)
	except OSError,e:
		raise DecodeFailed(fromname, "Cannot find decoder %s" % args[0])
	if ret != 0:
		raise DecodeFailed(fromname, "Subprocess returned %d" % ret)

def fingerprint_any(filename):
	"Decode an music file to wav, then fingerprint it, returning (fp,dur), or raising an exception"
	(fd,toname)=tempfile.mkstemp(suffix=".wav")
	os.close(fd)
	try:
		_decode(filename,toname)
		return fingerprint(toname)
	finally:
		if os.path.exists(toname):
			os.unlink(toname)

def upload_fingerprint_any(filename,genpuidcmd,musicdnskey):
	(fd,toname)=tempfile.mkstemp(suffix=".wav")
	os.close(fd)
	try:
		_decode(fname,toname)
		os.system(genpuid_cmd + " " + musicdnskey + " " + toname)
	finally:
		if os.path.exists(toname):
			os.unlink(toname)

def hash_file(fname):
	util.update_progress("Hashing file")
	return hashlib.md5(open(fname,"r").read()).hexdigest()

@memocache.memoify(mappingfunc=lambda args,kwargs:(hash_file(args[0]),kwargs))
def populate_fingerprint_cache(fname):
	util.update_progress("Looking up fingerprint for "+os.path.basename(fname))
	return fingerprint_any(fname)

