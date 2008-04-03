import sre

_filename_rules = [
	(r"&"," and "), # & -> And
	(r"[/\\]","-"), # / and \ -> -
	(r"[?\"]",""),  # ? and " removed
	(r"[?%*:<>\"\[\]+]","_"), # Other stuff to _
	(r"  +"," "),   # Remove duplicate spaces
]

def FixFilename(fname):
	"Convert a string into a form usable in a filename"
	for (src,rpl) in _filename_rules:
		fname = sre.sub(src,rpl,fname)
			
	fname=fname.strip() # Remove any trailing whitespace
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


		
