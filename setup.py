#!/usr/bin/env python

from distutils.core import setup

setup(name="albumidentify",
        version="0.0.1",
        description="Tools to identify and manage music albums",
        url="http://www.github.com/scottr/albumidentify",
        py_modules = ['albumidentify', 'albumidentifyconfig', 'amazon4', \
                      'discid', 'fingerprint', 'libofa', 'lookups', \
                      'mp3names', 'musicbrainz', 'musicdns', 'parsemp3', \
                      'puidsubmit', 'serialisemp3', 'submit', 'tag', 'toc'],
        scripts = ['renamealbum']
        )
        
