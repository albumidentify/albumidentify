#!/usr/bin/python

import sys
import os
import operator
import re

import tag

class SortFailedException(Exception):
	def __str__(self):
		return "Failed to sort directory in a meaningful way"

pattern = re.compile("(\D*?)(\d+)\D*")

def sorted_dir(dirname):
	dir = os.listdir(dirname)
	dir = [i for i in dir if os.path.splitext(i)[1].lower() in tag.supported_extensions]
	dir = sorted_list(dir)
	return dir

def sorted_list(list):
	""" Sort a list numerically if possible. 
	If the items in the list are part of a directory path, only the
	file component is used in sorting.  The remainder of the path
	is not tested.
	"""
	if len(list) < 2:
		return list

	orig = [i for i in list]

	# First item
	filename = os.path.basename(list[0])
	(prefix, key) = get_key(filename)
	deco = [(list[0], key)]
	keys = [key]
	common_pre = prefix
	list = list[1:]

	for item in list:
		filename = os.path.basename(item)
		(prefix, key) = get_key(filename)
		if key == "":
			print "Found a name with no numbers in it: %s, trying by tag" % item
			return tag_sorted_list(orig)
		elif prefix != common_pre:
			print "Got inconsistent prefixes, expected '%s' got '%s', trying by tag" % (common_pre, prefix)
			return tag_sorted_list(orig)
		elif key in keys:
			print "Found a duplicate key, trying by tag"
			return tag_sorted_list(orig)
		deco.append((item, key))

	list = sorted(deco, key=operator.itemgetter(1), cmp=comparator)
	return [i for i, k in list]

def tag_sorted_list(list):
	""" Sort a list of files by the track number tag """
	return sorted(list)
	deco = []
	for item in list:
		tags = tag.read_tags(item)
		if tag.TRACK_NUMBER not in tags:
			raise SortFailedException
		tracknum = tags[tag.TRACK_NUMBER]
		deco.append((item, tracknum))

	list = sorted(deco, key=operator.itemgetter(1), cmp=comparator)
	return [i for i, k in list]

def get_key(item):
	""" Find the first number in a string and return it, along with
	any non-numeric prefix in the string.
	"""
	file, ext = os.path.splitext(item)
	m = pattern.match(file)
	if m is not None:
		return m.group(1,2)
	else:
		return (file, "")

def comparator(a,b):
	""" Compare 2 numbers.  Asumes both numbers are integers """
	return int(a)-int(b)

def get_sorted_directory(dirname):
        files = sorted_dir(dirname)
        tracknum = 1
        # Assumes tracks are named in a sorted order
        tracknames = {}
        for i in files:
                fname=os.path.join(dirname,i)
                tracknames[tracknum] = fname
                tracknum+=1
        return tracknames

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "usage: sort <dir>"
		sys.exit(0)
	else:
		print sorted_dir(sys.argv[1])


