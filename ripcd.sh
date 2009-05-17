#!/bin/bash

dir=$(date +%Y%m%d%H%M%S)

if [ "$#" -eq "1" ]; then
	mkdir cd-$dir
	pushd cd-$dir	
	cdrdao read-cd --device $1 --with-cddb data.toc
	cdrecord dev=$1 -toc > cdrecord.toc
	eject $1
	cueconvert data.toc data.cue
	bchunk -s -w data.bin data.cue track
	popd cd-$dir
else
	echo -e "Usage: ripcd.sh [device]"
fi

