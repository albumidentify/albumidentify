#!/usr/bin/env python

from distutils.core import setup

setup(name="albumidentify",
        version="0.0.1",
        description="Tools to identify and manage music albums",
        url="http://www.github.com/scottr/albumidentify",
        package_dir = {'renamealbum': 'src/renamealbum'},
        scripts = ['renamealbum', 'ripcd', 'toflac'],
	packages = ['renamealbum']
        )
        
