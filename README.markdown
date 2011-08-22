# albumidentify #

Tools to identify and manage music albums.

(c) 2008-2010 The albumidentify team.

## Installation ##

### Dependencies ###
In order to run renamealbum you will need the following dependencies:

    python-musicbrainz2 libofa

And these optional dependencies:
    python-imaging libsndfile sndfile-programs

Depending on what filetypes you want to rename, you will need some additional
dependencies.

MP3:
    mpg123 mp3gain

flac:
    flac

ogg:
    vorbis-tools vorbisgain

Ripping CDs:
    cdrdao cueconvert bchunk flac

To install albumidentify, run:

    $ sudo python setup.py install

If you don't want to install it, you can run all of the files from the
directory you downloaded it to.

## Renaming albums (basic) ##

Use the renamealbum script to identify, tag and sort your music albums.

    $ renamealbum --dest-path=/dest/path /source/album/path

This will attempt to identify the album (flac, ogg or mp3) at
/source/album/path by fingerprinting, meta-data search or by CD-TOC if present
(see section "Ripping new CDs") and will copy the album to /dest/path/
creating subdirectories underneath that.

If you pass a block device as a source path, renamealbum will attempt to rip it as
if it were an audio CD and encode it to FLAC before naming the album.

## Renaming albums (advanced) ##

There are a lot of advanced options for renaming albums, and you can view a list
of them with with "renamealbum --help".

### Config File ###

A detailed example config file is included with albumidentify in the root 
directory. Simple copy albumidentifyrc.dist to either your home directory 
and rename it ".albumidentifyrc" or "/etc/albumidentifyrc". Options specified 
in the local config file will overide those provided in the global config file. 
Beware however of login information accessible from these files if you don't 
restrict access to them. It is recomended that if you have a need for a global 
config file you don't store login information in it and instead include that 
in your personal config file. Also be aware that any options provided in config 
files will be overridden by command line options provided at runtime.

### Submitting PUIDs ###

To submit PUIDs back to MusicBrainz and help other people rename their music
more quickly, create a config file (see above) with contents:

    [albumidentify]
    push_shortcut_puids=True
    genpuid_command=</path/to/genpuid>
    musicdnskey=<music dns key>

    [musicbrainz]
    username=<your mb username>
    password=<your mb password>

This requires the [genpuid](http://ftp.musicbrainz.org/pub/musicbrainz/genpuid/)
command to be installed and a musicDNS key.

### Custom Naming Schemes ###

renamealbum supports custom renaming schemes, which are specified as a standard 
Python string expansion. The default scheme is:

	%(sortalbumartist)s - %(year)i - %(album)s/%(tracknumber)02i - %(trackartist)s - %(trackname)s

See --scheme-help for a list of supported expansions.

Use --scheme to specify a custom scheme, making sure to quote appropriately.

If you specify a scheme which results in directories being created per-track,
the coverart and cd-toc will be placed in the last directory created. This
might change in the future. 

You can also specify the default naming scheme to use in the config file
(see above), using the naming_scheme key in the renamealbum section:

    [renamealbum]
    naming_scheme=%(album)s - %(trackname)s

### Ripping new CDs ###

renamealbum can rip, encode and tag a CD in one pass. However, if you want to rip
lots of CDs at once, it can be more efficient to do it in steps.

We've included a couple of scripts to make ripping and encoding CDs a bit
easier. These are python scripts that rely on several binaries that will need to
be installed through your distribution. See the list at the beginning of
this document to ensure you have them all.

To rip CDs, run
    $ ripcd /dev/cdrom destdir

Then use the toflac.py command to convert the files to flacs.
    $ mkdir flacs
    $ toflac -d flacs destdir

The important part of this process is keeping the CD's
Table of Contents (TOC) so that renamealbum can make a much more precise guess
as to what the album is.

Once you have a directory of flacs you can pass these to renamealbum as you
would any other album.
    $ renamealbum flacs/destdir

If an album cannot be identified, you can add it to MusicBrainz. Run

    $ submit.py <flac directory>

to get a URL to submit to. renamealbum may give you a URL to use if it
identifies the album with a different method. This allows you to connect the
computed discID with the actual release.

## Other Miscelaneous Scripts Provided ##

*  build-albums.sh - link different filetype source folders into 1 folder
*  build-todo-page.sh - output a html summary of a renamed folder
*  fetch-artist-art - finds an image for a specified artist
*  moveflac.sh - move flac files into folders named after their SORTALBUMARTIST tag

## Bug reports / Contribute ##

Our project page is [here](http://github.com/scottr/albumidentify). Feel free to
fork the repository and submit pull requests with new features, bug fixes, etc.

To enable correct tabbing in vim ensure you have modeline enabled.

Issues are tracked with [GitHub Issues](http://github.com/scottr/albumidentify/issues)

Visit us on IRC, irc.undernet.org #albumidentify

## Contributors ##

The following people have contributed to albumidentify:

*  [Perry Lorier](https://github.com/isomer) 
*  [Scott Raynel](https://github.com/scottr)
*  [Alastair Porter](https://github.com/alastair)
*  [Matt Brown](https://github.com/mattbnz)
*  [Nathan Overall](https://github.com/shweppsie)
*  [Kuno Woudt](https://github.com/warpr)
*  [Dominic Evans](https://github.com/oldmanuk)
