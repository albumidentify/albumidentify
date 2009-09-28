#
# fingerprint.py
# Tools for fingerprinting audio
#
# (C) 2008 Scott Raynel <scottraynel@gmail.com>
#

try:
	import libofa
except:
	pass
import wave

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
	
