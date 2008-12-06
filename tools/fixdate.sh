#!/bin/bash

# Check that DATE and YEAR fields are the same.  if not,
# remove DATE and set to YEAR

function check_file {
	odate=`metaflac --show-tag=DATE "$1"`
	oyear=`metaflac --show-tag=YEAR "$1"`
	date=${odate:5:4}
	year=${oyear:5:4}
	if [ "$date" != "$year" ]; then
		metaflac --remove-tag=DATE "$1"
		metaflac --set-tag=DATE=$year "$1"
		#echo -n " "$odate $oyear
		return 1
	fi
}

function check_album {
	r=0
	for i in "$1"/*.flac; do
		check_file "$i"
		if [ $? -eq 1 ]; then
			r=1
		fi
	done
	if [ $r -eq 1 ]; then 
		echo " DATE MISMATCH"
	else
		echo " OK"
	fi
}

for i in "$@"; do
	if [ -d "$i" ]; then
		echo -n "$i"
		check_album "$i"
	elif [ -f "$i" -a "${i#*.}" = "flac" ]; then
		check_file "$i"
	fi
done
