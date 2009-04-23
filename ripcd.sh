#!/bin/bash

dir=$(date +%Y%m%d%H%M%S)

function stuff
{
	cueconvert data.toc data.cue
	bchunk -s -w data.bin data.cue track
}

mkdir cd-$dir
pushd cd-$dir

if [ "$#" -eq "1" ]; then
	cdrdao read-cd --device $1 --with-cddb data.toc
	cdrecord dev=$1 -toc > cdrecord.toc
	eject $1
	stuff
elif [ "$#" -eq "0" ]; then
	cdrdao read-cd --with-cddb data.toc
	cdrecord -toc > cdrecord.toc
	eject
	stuff
else
	echo -e "Usage: ripcd.sh [device]"
fi

popd cd-$dir
