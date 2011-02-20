#!/usr/bin/env python

import sys
import Queue
import optparse
import subprocess
import os
import shutil
import threading
import glob

import albumidentifyconfig

q = Queue.Queue()

def prepare_folder(path, destdir):
        dst = os.path.abspath(destdir)

        if os.path.exists(dst):
            if len(os.listdir(dst))>0:
                print "%s is not empty" % dst
                return
        else:
            os.makedirs(dst)

        # XXX We should do some better sanity checks here. For example, if
        # the dest path exists, we should check that there is
        #  a) the same number of flacs as wavs
        #  b) that the flacs verify
        #  c) that the flac dir has a tocfile

        for f in glob.glob(os.path.join(path, "*.wav")):
		q.put(f)

def finish_folder(path, destdir):
        for f in glob.glob(os.path.join(path, "*.flac")):
                shutil.move(f, os.path.join(destdir, os.path.basename(f)))

        # Copy the tocfile if it exists
        tocfilename = ""
        if os.path.exists(os.path.join(path, "TOC")):
                tocfilename = os.path.join(src, "TOC")
        if os.path.exists(os.path.join(path, "data.toc")):
                tocfilename = os.path.join(path, "data.toc")

        if tocfilename:
                shutil.copy(tocfilename, os.path.join(dst, "data.toc"))
        

def process_file(filename):
        proclist = ["flac",
                    "--verify",
                    "--replay-gain",
                    "--max-lpc-order=12",
                    "--blocksize=4096",
                    "--mid-side",
                    "--exhaustive-model-search",
                    "--rice-partition-order=6",
                    "--qlp-coeff-precision-search",
                    "--padding=131027",
		    "--force"
                    ]
	proclist.append(filename)
        p = subprocess.Popen(proclist, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        error = p.communicate()[1]
		

        if (p.returncode == 0):
		print "%s completed successfully" % filename
	else:
                # Clean up any mess that flac left
                os.unlink(filename.replace('.wav','.flac'))
		print "ERROR: An error occurred converting %s" % filename
		print error

def worker():
        t = threading.currentThread()
        while not q.empty():
                item = q.get()
                print "%s encoding %s" % (t.name, item)
                process_file(item)
                q.task_done()

def process_paths(paths, destpath, numcpus=1):
        # Check that src paths exist
        for path in paths:
                if not os.path.exists(os.path.abspath(path)):
                        print("%s doesn't exist!" % path)
                        opts.print_help()
                        sys.exit(1)

        # Queue paths for work
        for path in paths:
		path = os.path.abspath(path)
		if len(paths) > 1:
			dest = os.path.join(destpath, os.path.basename(path))
		else:
			dest = destpath
                if os.path.isdir(path):
			print "Encoding \"%s\" to \"%s\"" % (os.path.basename(path), dest)
			prepare_folder(os.path.abspath(path), dest) 

        # Spawn worker threads to deal with the work
        for i in range(numcpus):
                t = threading.Thread(target=worker)
                t.setDaemon(True)
                t.start()
        
	# Wait until all threads have finished (queue is processed)
        q.join()
	

        for path in paths:
		path = os.path.abspath(path)
		if len(paths) > 1:
			dest = os.path.join(destpath, os.path.basename(path))
		else:
			dest = destpath
                if os.path.isdir(path):
			finish_folder(os.path.abspath(path), dest) 

        print "All worker threads finished"

def path_arg_cb(option, opt_str, value, parser):
        path = os.path.abspath(value)
        setattr(parser.values, option.dest, path)

def main():
        opts = optparse.OptionParser(usage="%s [options] <srcdirs>" % sys.argv[0])
        opts.add_option(
                "-d", "--dest-path",
                type="str",
                dest="destpath",
                default="flacs/",
                metavar="PATH",
                action="callback",
                callback=path_arg_cb,
                help="Prefix output directories with PATH"
        )

        opts.add_option(
                "-j",
                type="int",
                dest="numcpus",
                default=albumidentifyconfig.config.get("albumidentify", "threads"),
                metavar="THREADS",
                help="Spawn multipled THREADS for encoding"
        )

        (options,args) = opts.parse_args()

        if len(args) == 0:
            opts.print_help()
            sys.exit(1)

	numcpus = options.numcpus
	if numcpus < 1:
		import multiprocessing
		numcpus = multiprocessing.cpu_count()

	process_paths(args, options.destpath, numcpus)

if __name__ == "__main__":
	main()
