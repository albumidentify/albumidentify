#!/bin/bash

dir=$(date +%Y%m%d%H%M%S)

function begin
{
	mkdir cd-$dir
	pushd cd-$dir
}

function finish
{
	cueconvert data.toc data.cue
	bchunk -s -w data.bin data.cue track
	popd cd-$dir
}


if [ "$#" -eq "1" ]; then
	begin
	cdrdao read-cd --device $1 --with-cddb data.toc
	eject $1
	finish
elif [ "$#" -eq "0" ]; then
	begin
	cdrdao read-cd --with-cddb data.toc
	eject
	finish
else
	echo -e "Usage: ripcd.sh [device]"
fi

