import ConfigParser
import os

config=ConfigParser.RawConfigParser()

def readconfig():
	config.add_section("albumidentify")
        config.add_section("renamealbum")
	config.set("albumidentify","push_shortcut_puids","False")
	config.set("albumidentify","genpuid_command","")
        config.set("albumidentify","musicdnskey", "")
	# TIMELIMIT > 0 -- after this many seconds, give up.
	# TIMELIMIT <= 0 -- try until exhausting all possibilities
	config.set("albumidentify","timelimit", "0")
        config.set("renamealbum", "naming_scheme", "%(sortalbumartist)s - %(year)i - %(album)s/%(tracknumber)02i - %(trackartist)s - %(trackname)s")
        config.set("renamealbum", "dest_path", "")
        config.set("renamealbum", "leave_soundtrack_artist", "False")
	config.read(os.path.expanduser("~/.albumidentifyrc"))

if __name__=="__main__":
	readconfig()
	for section in config.sections():
		print "Section",section
		for option in config.options(section):
			print "",option,config.get(section,option)
else:
	# Read config if we have been imported
	readconfig()
