#!/bin/bash

# Add a cover image to an album
# Usage: imagefix <image> <directory>

function fix_album() {
	cp "$1" "$2/folder.jpg"
	for i in "$2"/*.flac; do
		metaflac --block-type=PICTURE --dont-use-padding --remove "$i"
		metaflac --import-picture-from="$1" "$i"
	done
}


if [ -f "$1" -a -d "$2" ]; then
	echo "Fixing $2..."
	fix_album "$1" "$2"
	echo "...done"
fi
