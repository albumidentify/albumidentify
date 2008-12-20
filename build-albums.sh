#!/bin/sh

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

