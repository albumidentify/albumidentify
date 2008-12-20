#!/bin/bash


movefile() {
SORTARTIST=$(metaflac --show-tag=SORTARTIST "$1"/01*)
SORTARTIST=${SORTARTIST#SORTARTIST=}

echo "$1" -\> "$2/$SORTARTIST/"
mkdir -p "$2/$SORTARTIST/"
mv "$1" "$2/$SORTARTIST/"
}

for i in `seq 1 $[ $BASH_ARGC-1 ]`; do
	movefile "${BASH_ARGV[$i]}" "${BASH_ARGV[0]}"
done
