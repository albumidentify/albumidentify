#!/bin/bash

# Remove disc number tags if there is only 1 disc in the set

function clean_file() {
	ret=`metaflac --show-tag=DISCTOTAL "$1"`
	if [ -z "$ret" ]; then
		echo nothing
		return
	elif [ ${ret#DISCTOTAL=} = "1" ]; then
		echo ret $ret remove
		metaflac --remove-tag=DISC "$1"
		metaflac --remove-tag=DISCC "$1"
		metaflac --remove-tag=DISCNUMBER "$1"
		metaflac --remove-tag=DISCTOTAL "$1"
	else
		echo "$i" keep
	fi
}

function clean_album() {
	for i in "$1"/*.flac; do
		if [ ${i##*.} = "flac" ]; then
			clean_file "$i"
		fi
	done
}

for i in "$@"; do
	if [ -d "$i" ]; then
		echo "directory"
		clean_album "$i"
	fi
done
