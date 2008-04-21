import sre

_filename_rules = [
	(r"&"," and "), # & -> And
	(r"[/\\]","-"), # / and \ -> -
	(r"[?\"]",""),  # ? and " removed
	("\x00",""),	# Urgh, \x00's in filenames would Be Bad
	(r"\+"," plus "), # "+" -> " plus "
	(r":", " - "), # ":" -> " - "
	(r"[?%*:<>\"\[\]]","_"), # Other stuff to _
	(r"  +"," "),   # Remove duplicate spaces
	(r"\.$"," "), 	# Windows doesn't deal well with filenames that end with a .
]

def FixFilename(fname):
	"Convert a string into a form usable in a filename"
	for (src,rpl) in _filename_rules:
		fname = sre.sub(src,rpl,fname)
			
	fname=fname.strip() # Remove any trailing whitespace
	if type(fname)==type(u""):
		# Filenames are presumed to be in utf8
		fname=fname.encode("utf8")
	return fname


def FixArtist(name):
	"Applies the rules for fixing artist names (including in Tags)"
	if name.startswith("The "):
		name=name[4:]+", The"

	return name

if __name__=="__main__":
	def test(inp,func,expected):
		if func(inp)==expected:
			print "%s -%s-> %s" % (`inp`,func.__name__,`expected`)
		else:
			print "%s -%s-> %s != %s" % (`inp`,func.__name__,`func(inp)`,`expected`)
			raise AssertionError

	test("The Smashing Pumpkins",FixArtist,"Smashing Pumpkins, The")
	test("On My Own (feat. Les Nubian & Mos Def)",
		FixFilename,"On My Own (feat. Les Nubian and Mos Def)")
	test("Test with :\x00: NUlls",
		FixFilename,"Test with __ NUlls")


		
