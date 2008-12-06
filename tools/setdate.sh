#!/bin/bash

# Set the date of all the flacs

function set_file {
	echo "setting year to $1"
		metaflac --remove-tag=DATE "$2"
		metaflac --set-tag=DATE=$1 "$2"
		metaflac --remove-tag=YEAR "$2"
		metaflac --set-tag=YEAR=$1 "$2"
		#echo -n " "$odate $oyear
}

function set_album {
	for i in "$2"/*.flac; do
		set_file "$1" "$i"
	done
}

if [ -d "$2" ]; then
	echo -n "$2"
	set_album "$1" "$2"
elif [ -f "$i" -a "${i#*.}" = "flac" ]; then
	set_file "$1" "$2"
fi
