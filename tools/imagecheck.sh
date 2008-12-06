#!/bin/bash

# See if any directories are missing a cover image, or if they are too small

function check_album() {
	if [ ! -e "$1/folder.jpg" ]; then
		echo " - MISSING"
	else
		w=`identify -format "%w" "$1/folder.jpg"`
		echo -n " - "$w
		if [ $w -lt 300 ]; then
			echo " (TOOSMALL)"
		else
			echo
		fi
	fi
}

for i in "$@"; do
	if [ -d "$i" ]; then
		echo -n "$i"
		check_album "$i"
	fi
done
