#!/bin/sh

# Must be run from inside ..../albums
# Must provide relative arguments
# Call this script with the list of filetype root folders you have
# it will link those folders together so the different filetypes
# appear in one folder.

for filetype in "$@"; do
	for artist in "$filetype"/*; do
		artist=$(basename "$artist")
		echo $filetype/$artist
		mkdir -p "$artist"
		for album in "$filetype/$artist/"*; do
			album=$(basename "$album")
			rm "$artist/$album" &>/dev/null
			ln -sf "../$filetype/$artist/$album" "$artist/$album"
		done
	done
done

