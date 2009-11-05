# albumidentify #

Tools to identify and manage music albums.

(c) 2008-2009 The albumidentify team.

## Installation ##

You don't really have to install anything if you don't want to. You can run all
of the scripts straight from the source directory. If you do want to install
albumidentify, use:

    $ sudo python setup.py install

Make sure you have the python-musicbrainz2 package installed from your
distribution. libofa is also required for audio fingerprinting.

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

### Submitting PUIDs ###

To submit PUIDs back to MusicBrainz and help other people rename their music
more quickly, create a file ~/.albumidentifyrc with contents:

    [albumidentify]
    push_shortcut_puids=True
    genpuid_command=</path/to/genpuid>
    musicdnskey=<music dns key>

    [musicbrainz]
    username=<your mb username>
    password=<your mb password>

This requires the genpuid command to be installed and a musicDNS key.

### Custom Naming Schemes ###

renamealbum supports custom renaming schemes, which are specified as a standard 
Python string expansion. The default scheme is:

	%(sortalbumartist)s - %(year)i - %(album)s/%(tracknumber)02i - %(trackartist)s - %(trackname)s

See --scheme-help for a list of supported expansions.

Use --scheme to specify a custom scheme, making sure to quote appropriately.

If you specify a scheme which results in directories being created per-track,
the coverart and cd-toc will be placed in the last directory created. This
might change in the future. 

You can also specify the default naming scheme to use in the ~/.albumidentifyrc
file, using the naming_scheme key in the renamealbum section:

    [renamealbum]
    naming_scheme=%(album)s - %(trackname)s

### Ripping new CDs ###

renamealbum can rip, encode and tag a CD in one pass. However, if you want to rip
lots of CDs at once, it can be more efficient to do it in steps.

We've included a couple of scripts to make ripping and encoding CDs a bit
easier. These are python scripts that rely on several binaries that will need to
be installed through your distribution. They are:

*  cdrdao
*  cueconvert
*  bchunk
*  flac

To rip CDs, run the ripcd.py command. Then use the toflac.py command to convert
the files to flacs. The important part of this process is keeping the CD's
Table of Contents (TOC) so that renamealbum can make a much more precise guess
as to what the album is.

Once you have a directory of flacs you can pass these to renamealbum as you
would any other album.

If an album cannot be identified, you can add it to MusicBrainz. Run

    submit.py <flac directory>

to get a URL to submit to. renamealbum may give you a URL to use if it
identifies the album with a different method. This allows you to connect the
computed discID with the actual release.

## Bug reports / Contribute ##

Our project page is [here](http://github.com/scottr/albumidentify). Feel free to
fork the repository and submit pull requests with new features, bug fixes, etc.

Issues are tracked with [GitHub Issues](http://github.com/scottr/albumidentify/issues)

## Contributors ##

The following people have contributed to albumidentify:

*  Perry Lorier
*  Scott Raynel
*  Alastair Porter
*  Matt Brown
*  Nathan Overall
