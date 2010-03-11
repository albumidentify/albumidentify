import subprocess

class GainFailedException(Exception):
	def __init__(self, args, reason):
		self.reason = reason
		self.args = args
	def __str__(self):
		return "%s %s" % (self.reason, repr(self.args))

def get_gain(filename):
        if filename.lower().endswith(".flac") == False:
                return None
        gaindict = {}
        args = ["metaflac", "--export-tags-to=-", filename]
        p = subprocess.Popen(args, stdout=subprocess.PIPE)
        (sout, serr) = p.communicate()
        for line in sout.split('\n'):
                line = line.strip()
                parts = line.split('=', 1)
                if parts[0].startswith("REPLAYGAIN_"):
                        gaindict[parts[0]] = parts[1]
        return gaindict

def set_gain(filename, gain):
        if filename.lower().endswith(".flac") == False:
                return
        args = ["metaflac"]
        for k in gain.keys():
                args.append("--set-tag=%s=%s" % (k,gain[k]))
        args.append(filename)
        subprocess.call(args)

def remove_gain(filename):
	if filename.lower().endswith(".mp3"):
		args = ["mp3gain", "-u", "-q", filename]
	elif filename.lower().endswith(".ogg"):
		args = ["vorbisgain", "-c", "-q", filename]
	elif filename.lower().endswith(".flac"):
		args = ["metaflac", "--remove-replay-gain", filename]
	else:
		raise GainFailedException(filename, 
				"Cannot remove gain from file (unrecognised filetype)")

	try:
		ret = subprocess.call(args)
	except OSError,e:
		raise GainFailedException(filename, 
				"Cannot find gain tool, install %s to enable replaygain support" % args[0])
	if ret != 0:
		raise GainFailedException(filename, 
				"Subprocess returned %d" % ret)

def add_gain(files):
	if type(files) != type([]):
		raise Exception("Need a list of files to add gain to")
	exts = set([x.rsplit(".")[-1:][0].lower() for x in files])
	
	if len(exts) == 1 and "mp3" in exts:
		args = ["mp3gain", "-a", "-c"]
	elif len(exts) == 1 and "ogg" in exts:
		args = ["vorbisgain", "-a"]
	elif len(exts) == 1 and "flac" in exts:
		args = ["metaflac", "--add-replay-gain"]
	else:
		raise GainFailedException(files, "unknown set of files to add gain to")

	args.extend(files)

	try:
		ret = subprocess.call(args)
	except OSError,e:
		raise GainFailedException("", "Cannot find gain tool %s, install to enable replaygain support" % args[0])
	if ret != 0:
		raise GainFailedException("", "Subprocess returned %d" % ret)

