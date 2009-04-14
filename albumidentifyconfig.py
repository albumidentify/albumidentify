import ConfigParser
import os

config=ConfigParser.RawConfigParser()

def readconfig():
	config.add_section("albumidentify")
        config.add_section("renamealbum")
	config.set("albumidentify","push_shortcut_puids","False")
	config.set("albumidentify","genpuid_command","")
        config.set("albumidentify","musicdnskey", "")
        config.set("renamealbum", "naming_scheme", "%(sortalbumartist)s - %(year)i - %(album)s/%(tracknumber)02i - %(trackartist)s - %(trackname)s")
	config.read(os.path.expanduser("~/.albumidentifyrc"))
	
if __name__=="__main__":
	readconfig()
	for section in config.sections():
		print "Section",section
		for option in config.options(section):
			print "",option,config.get(section,option)
