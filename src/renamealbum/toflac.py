#!/usr/bin/env python

import sys
import Queue
import optparse
import subprocess
import os
import shutil
import threading
import glob

q = Queue.Queue()

def process_item(path, destdir, pathcheck=True):
        dir = os.path.basename(path)
        src = path
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
                    "--totally-silent",
					"--output-prefix=%s/" % dst
                    ]

        for f in glob.glob(os.path.join(src, "*.wav")):
                proclist.append(f)

        p = subprocess.Popen(proclist)
        p.communicate()

        print "%s completed with returncode %i" % (src, p.returncode)

        if (p.returncode != 0):
                # Clean up any mess that flac left
                for f in glob.glob(os.path.join(src, "*.flac")):
                        os.unlink(f)
                return

        for f in glob.glob(os.path.join(src, "*.flac")):
                shutil.move(f, os.path.join(dst, os.path.basename(f)))

        # Copy the tocfile if it exists
        tocfilename = ""
        if os.path.exists(os.path.join(src, "TOC")):
                tocfilename = os.path.join(src, "TOC")
        if os.path.exists(os.path.join(src, "data.toc")):
                tocfilename = os.path.join(src, "data.toc")

        if tocfilename:
                shutil.copy(tocfilename, os.path.join(dst, "data.toc"))
        

def worker():
        t = threading.currentThread()
        while not q.empty():
                item = q.get()
                print "%s encoding %s" % (t.name, item[0])
                process_item(item[0],item[1])
                q.task_done()

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
                default=1,
                metavar="THREADS",
                help="Spawn multipled THREADS for encoding"
        )

        (options,args) = opts.parse_args()

        if len(args) == 0:
            opts.print_help()
            sys.exit(1)

        # Check that src paths exist
        for path in args:
                if not os.path.exists(os.path.abspath(path)):
                        print("%s doesn't exist!" % path)
                        opts.print_help()
                        sys.exit(1)

        # Queue paths for work
        for path in args:
                if os.path.isdir(path):
                        q.put((path, options.destpath))

        # Spawn worker threads to deal with the work
        for i in range(options.numcpus):
                t = threading.Thread(target=worker)
                t.setDaemon(True)
                t.start()

        # Wait until all threads have finished (queue is processed)
        q.join()
        print "All worker threads finished"

if __name__ == "__main__":
	main()
