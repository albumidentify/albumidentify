#!/bin/sh

dir=$(date +%Y%m%d%H%M%S)

mkdir cd-$dir
pushd cd-$dir
cdrdao read-cd --with-cddb data.toc
cdrecord -toc > cdrecord.toc
eject
cueconvert data.toc data.cue
bchunk -s -w data.bin data.cue track
popd cd-$dir
