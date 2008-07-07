
def _write_fixed_width(f,data,size):
	f.write((data+"\x00"*size)[:size])

# output the id3v1.1 tag
def _id3v1(f,data):
	f.write("TAG")
	_write_fixed_width(f,data["TIT2"].encode("iso8859-1","replace"),30)
	_write_fixed_width(f,data["TPE1"].encode("iso8859-1","replace"),30)
	_write_fixed_width(f,data["TALB"].encode("iso8859-1","replace"),30)
	_write_fixed_width(f,data["TYER"].encode("iso8859-1","replace"),4)
	_write_fixed_width(f,data["COMM"].encode("iso8859-1","replace"),28)
	f.write("\x00") # ID3v1.1 tag
	f.write(chr(int(data["TRCK"].split("/")[0])))
	_write_fixed_width(f,"\xFF",1) # No Genre

def _tag(name,data):
	assert len(name)==4
	assert len(data)<127
	ret =(name)				# Tag Name
	ret+=("\x00\x00\x00"+chr(len(data)))	# Length
	ret+=("\x00\x00")			# Flags
	ret+=(data)
	return ret

def _texttag(name,data):
	try:
		# Try and encode it as latin-1 if we can
		data="\x00"+data.encode("iso8859-1")
	except:
		# If we can't, give up and use utf16
		data="\x01"+data.encode("utf-16")
	# Now write the tag out
	return _tag(name,data)


def _id3v2(f,data):
	f.write("ID3")		# Magic
	f.write("\x03\x00")	# Version ID3v2.3.0
	f.write("\x00")		# %0100-0000 Extended header present
	# Length
	outp =_texttag("TIT2",data["TIT2"])
	outp+=_texttag("TPE1",data["TPE1"])
	outp+=_texttag("TALB",data["TALB"])
	outp+=_texttag("TYER",data["TYER"])
	outp+=_texttag("TDAT",data["TDAT"])
	outp+=_texttag("TRCK",data["TRCK"])
	if "UFID" in data:
		outp+=_tag("UFID",data["UFID"][0]+"\x00"+data["UFID"][1])
	if "TXXX" in data:
		for (k,v) in data["TXXX"]:
			outp+=_texttag("TXXX",k+"\x00"+v)
	#outp+=_tag("TLEN",data["TLEN"])
	#outp+=_tag("TLEN",str(data["TLEN"]))
	f.write("\x00\x00"+chr(len(outp)>>7)+chr(len(outp)&0x7f))
	f.write(outp)

def output(fname,data):
	f=open(fname,"wb")
	_id3v2(f,data)
	f.write(data["bitstream"])
	_id3v1(f,data)
	f.close()
