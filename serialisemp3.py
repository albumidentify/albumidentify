
def _write_fixed_width(f,data,size):
	f.write((data+"\x00"*size)[:size])

# output the id3v1.1 tag
def _id3v1(f,data):
	f.write("TAG")
	_write_fixed_width(f,data["TIT2"].encode("iso8859-1","replace"),30)
	_write_fixed_width(f,data["TPE1"].encode("iso8859-1","replace"),30)
	_write_fixed_width(f,data["TALB"].encode("iso8859-1","replace"),30)
	_write_fixed_width(f,data["TYER"].encode("iso8859-1","replace"),4)
	# Grab the value of the first comment tag
	_write_fixed_width(f,data["COMM"][0][1].encode("iso8859-1","replace"),28)
	f.write("\x00") # ID3v1.1 tag
	f.write(chr(int(data["TRCK"].split("/")[0])))
	_write_fixed_width(f,"\xFF",1) # No Genre

def _tag(name,data):
	assert len(name)==4
	assert len(data)<127*127*127
	assert type(data) == type("") # Must be a (byte) string, not a unicode string!
	assert type(name) == type("") # ditto
	ret =(name)				# Tag Name
	# id3 v2.3 does not have synchsafe integers.  We can use
	# all the way up to the highest bit for sizes
	ret+=("\x00"+chr(len(data)/(256*256))+
			chr((len(data)/256)%256)+
			chr(len(data)%256))	# Length
	ret+=("\x00\x00")			# Flags
	ret+=(data)
	return ret

def _encode(data):
	try:
		# Try and encode it as latin-1 if we can
		data=data.encode("iso8859-1")
		type = "\x00"
	except:
		# If we can't, give up and use utf16
		data=data.encode("utf-16")
		type = "\x01"
	return (type,data)

def _texttag(name,data):
	(type,data) = _encode(data)
	return _tag(name, type+data)

def _id3v2(f,data):
	f.write("ID3")		# Magic
	f.write("\x03\x00")	# Version ID3v2.3.0
	f.write("\x00")		# %0100-0000 Extended header present
	# Length
	outp =_texttag("TIT2",data["TIT2"])
	outp+=_texttag("TPE1",data["TPE1"])
	if "TPE2" in data:
		outp+=_texttag("TPE2",data["TPE2"])
	outp+=_texttag("TALB",data["TALB"])
	outp+=_texttag("TYER",data["TYER"])
	outp+=_texttag("TDAT",data["TDAT"])
	outp+=_texttag("TRCK",data["TRCK"])
	if "UFID" in data:
		# UFID doesn't get encoded so uses tag not texttag
		assert type(data["UFID"][0]) == type("")
		assert type(data["UFID"][1]) == type("")
		outp+=_tag("UFID",data["UFID"][0]+"\x00"+data["UFID"][1])
	if "TSOB" in data \
			and len(data["TSOP"])>0 \
			and data["TSOP"]!=data["TPE1"]:
		outp+=_texttag("TSOB",data["TSOB"])
	if "TSO2" in data and len(data["TSO2"])>0:
		outp+=_texttag("TSO2",data["TSO2"])
	if "TMOO" in data and len(data["TMOO"])>0:
		outp+=_texttag("TMOO",data["TMOO"])
	if "TCON" in data and len(data["TCON"])>0:
		outp+=_texttag("TCON","\x00".join(data["TCON"]))
	if "TXXX" in data:
		for (k,v) in data["TXXX"]:
			outp+=_texttag("TXXX",k+u"\x00"+v)
	#outp+=_tag("TLEN",data["TLEN"])
	#outp+=_tag("TLEN",str(data["TLEN"]))
	if "COMM" in data:
		for (k,v) in data["COMM"]:
			(encoding, payload) = _encode("\x00"+v)
			outp+= _tag("COMM", encoding+"eng"+"Tags\x00"+payload)
	# Output the APIC tag last
	if "APIC" in data:
		# encoding, mimetype, \x00, pic type (\x03 = front cover), desc, \x00, data
		(mimetype, pictype, desc, stream) = data["APIC"]
		(encoding,desc) = _encode(desc)
		#mimetype = mimetype.encode("ascii").encode("utf8")
                d=encoding
                d+=mimetype.encode("utf8")+"\x00"
                d+=pictype
                d+=desc.encode("utf8")+"\x00"
                d+=stream
		outp+=_tag("APIC",d)
	f.write(chr(len(outp)>>21)+
		chr((len(outp)>>14)&0x7f)+
		chr((len(outp)>>7)&0x7f)+
		chr(len(outp)&0x7f))
	f.write(outp)

def output(fname,data):
	f=open(fname,"wb")
	_id3v2(f,data)
	f.write(data["bitstream"])
	_id3v1(f,data)
	f.close()
