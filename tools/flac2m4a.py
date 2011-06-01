#!/usr/bin/python
#
# Convert a series of FLAC files into m4a
# 
# Usage: flac2m4a [-c coverart] [-d destdir] <src>
#
# Currently <src> is treated as a set of FLACs to transcode. By default we
# transcode to the current directory. Set the destination path with -d. 
#
# TODO:
#  - If <src> is a directory, rather than a file, encode the entire directory
#    and be smart about detecting folder.jpg to embed.
#  - Check for existence of flac and faac binaries before running.
#  - Support for other output formats.
#  - Fix any bugs ;)
#

import sys
import os
import subprocess
import optparse

opts = optparse.OptionParser(usage="%s [options] <src>" % sys.argv[0])

opts.add_option(
        "-c", "--cover-art",
        dest="coverart",
        default="",
        metavar="cover.jpg",
        help="Embed cover.jpg as coverart in each output file")

opts.add_option(
        "-d", "--dest-path",
        dest="destdir",
        default="",
        metavar="DESTPATH",
        help="Write output files into DESTPATH. Defaults to current directory")

(options, args) = opts.parse_args()

def extract_metadata(f):
        metadict = {}
        p = subprocess.Popen("metaflac --export-tags-to=- \"%s\"" % f,
                                shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                close_fds=True)
        (stdoutdata, stderrdata) = p.communicate()
        for line in stdoutdata.split("\n"):
                line = line.strip()
                if line == "":
                        continue
                parts = line.split("=", 1)
                metadict[parts[0]] = parts[1]
        return metadict

def faacmetastring(metadict, flacmeta, faacmeta):
        s = " "
        if metadict.has_key(flacmeta):
                s = faacmeta + " \"" + metadict[flacmeta] + "\" "                
        return s

def convert_file(infile, outfile, coverart = ""):
        print infile,"->",outfile
        metadict = extract_metadata(infile)
        decoder = "flac --decode --stdout \"" + infile + "\"" 
        encoder = "faac -b 256 -o \"" + outfile + "\" -w "
        if coverart != "":
                encoder += "--cover-art \"" + coverart + "\" "
        encoder += faacmetastring(metadict, "ARTIST", "--artist")
        encoder += faacmetastring(metadict, "TITLE", "--title")
        encoder += faacmetastring(metadict, "GENRE", "--genre")
        encoder += faacmetastring(metadict, "ALBUM", "--album")
        encoder += faacmetastring(metadict, "YEAR", "--year")

        if metadict.has_key("TRACKNUMBER") and metadict.has_key("TRACKTOTAL"):
                encoder += "--track \"%s/%s\" " % (metadict["TRACKNUMBER"], metadict["TRACKTOTAL"])
        if metadict.has_key("DISCNUMBER") and metadict.has_key("DISCTOTAL"):
                encoder += "--disc \"%s/%s\" " % (metadict["DISCNUMBER"], metadict["DISCTOTAL"])

        encoder += " - "

        ret = os.system (decoder + " | " + encoder)

        if ret != 0:
                print "Caught non-zero return from transcoder pipeline: " + str(ret)
                return False

        return True

if len(args) == 0:
        opts.print_help()
        sys.exit(1)

for i in args:
        (root,ext) = os.path.splitext(i)
        if not convert_file(i, os.path.join(options.destdir, os.path.basename(root)) + ".m4a", options.coverart):
                break
