import ConfigParser
import os

config=ConfigParser.ConfigParser()

def readconfig():
	config.add_section("albumidentify")
	config.set("albumidentify","push_shortcut_puids","False")
	config.set("albumidentify","genpuid_command","")
	config.read(os.path.expanduser("~/.albumidentifyrc"))
	
if __name__=="__main__":
	readconfig()
	for section in config.sections():
		print "Section",section
		for option in config.options(section):
			print "",option,config.get(section,option)
