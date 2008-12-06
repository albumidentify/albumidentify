#!/bin/bash

# Encode a directory of flacs to mp3 and copy some tags over

function encode {

FLAC=$2
TITLE="`metaflac --show-tag=TITLE "$FLAC" | awk -F = '{ printf($2) }'`"
ALBUM="`metaflac --show-tag=ALBUM "$FLAC" | awk -F = '{ printf($2) }'`"
ARTIST="`metaflac --show-tag=ARTIST "$FLAC" | awk -F = '{ printf($2) }'`"
TRACKNUMBER="`metaflac --show-tag=TRACKNUMBER "$FLAC" | awk -F = '{ printf($2) }'`"
GENRE="`metaflac --show-tag=GENRE "$FLAC" | awk -F = '{ printf($2) }'`"
COMMENT="`metaflac --show-tag=COMMENT "$FLAC" | awk -F = '{ printf($2) }'`"
DATE="`metaflac --show-tag=DATE "$FLAC" | awk -F = '{ printf($2) }'`"

MP3=`basename "${FLAC%.flac}.mp3"`

	flac -dc "$FLAC" | lame --vbr-new -V 2 -b 192 \
	--tt "$TITLE" \
	--tn "$TRACKNUMBER" \
	--tg "$GENRE" \
	--ty "$DATE" \
	--ta "$ARTIST" \
	--tl "$ALBUM" \
	--add-id3v2 \
	- "/mnt/elgar/Incoming/newmp3/$1/$MP3"
}

function convert {
	mkdir -p "/mnt/elgar/Incoming/newmp3/$1"
	cp "$1"/*.jpg "/mnt/elgar/Incoming/newmp3/$1"
	for i in "$1"/*.flac; do
		encode "$1" "$i"
	done
}


for i in "$@"; do
	if [ -d "/mnt/elgar/Incoming/newmp3/$i" ]; then
		echo "Skipping $i"
	else 
		convert "$i"
	fi
done
