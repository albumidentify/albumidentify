
import os
import tempfile
import urllib
import operator

import sort
import lookups
import tag
import util

# Find album art
# Try to fetch from Amazon (by ASIN), if that fails, see if we already have album art and use that.
def find_albumart(srcpath,disc,options):
	imageurl = lookups.get_album_art_url_for_asin(disc.asin)
	images = []
	if imageurl is not None:
                print "Downloading album art from %s" % imageurl
		if not options.noact:
                        try:
                                (fd,tmpfile) = tempfile.mkstemp(suffix = ".jpg")
                                os.close(fd)
                                (f,h) = urllib.urlretrieve(imageurl, tmpfile)
                                if h.getmaintype() != "image":
                                        print "WARNING: image url returned unexpected mimetype: %s" % h.gettype()
                                        os.unlink(tmpfile)
                                else:
                                        imagemime = h.gettype()
                                        imagepath = tmpfile
					images.append((imagepath, imagemime, True, "amazon"))
			except:
                                print "WARNING: Failed to retrieve coverart (%s)" % imageurl
	if os.path.exists(os.path.join(srcpath, "folder.jpg")):
		print "Found existing image file"
                imagemime="image/jpeg"
                imagepath = os.path.join(srcpath, "folder.jpg")
		images.append((imagepath, imagemime, False, "local file"))
	
	dir = sort.sorted_dir(srcpath)
	filetags = tag.read_tags(dir[0])
	if tag.IMAGE in filetags:
		for image in filetags[tag.IMAGE]:
			print "Found image embedded in file"
			if image['mime'] == "image/jpeg":
				suffix = ".jpg"
			elif image['mime'] == "image/png":
				suffix = ".png"
			else:
				print "Embeded Image is of unknown Mime Type"
				continue
			if image['pictype'] != 3:
				print "Embeded Image not coverart"
				continue
			(fd,tmpfile) = tempfile.mkstemp(suffix)
			os.write(fd, image['imagedata'])
			os.close(fd)
			images.append((tmpfile, image['mime'], True, "embedded tag"))

	best = find_best_image(images)[0]
	if best[0] is not None:
		util.report("Best cover image: %s (from %s)" % (best[0], best[3]))
	return best

def find_best_image(images):
	""" images = [(path, mime, need_unlink, source)]
	    Given a list of image paths, choose the biggest one.
	    Try with image dimensions, otherwise use filesize.
	    Returns a filename to use. """
	if len(images) == 0:
		return [(None, None, False, None)]
	elif len(images) == 1:
		return images

	dec = []
	try:
		import Image
		for (fname, mime, need_unlink, source) in images:
			try:
				i = Image.open(fname)
				dec.append((fname, mime, need_unlink, source, i.size[0]))
			except IOError, e:
				pass
	except ImportError, e:
		for (fname, mime, need_unlink, source) in images:
			dec.append((fname, mime, need_unlink, source, os.path.getsize(fname)))
	except IOError, e:
		# Error doing Image.open
		pass

	sortimages = sorted(dec, key=operator.itemgetter(4), reverse=True)

	if len(sortimages) == 0:
		return [(None, None, False, None)]

	return [(p, m, d, so) for (p, m, d, so, si) in sortimages]

