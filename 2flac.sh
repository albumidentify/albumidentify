#!/bin/bash -e
set -x
for i in raw/cd-*; do
	DIR=$(basename $i)
	SRC=$i
	DST=flac/$DIR
	# Skip directories that already exist
	if [ -d $DST ]; then
		continue
	fi
	mkdir $DST
	echo $DIR:
	flac \
		--verify			\
		--replay-gain			\
		--max-lpc-order=12		\
		--blocksize=4096		\
		--mid-side			\
		--exhaustive-model-search	\
		--rice-partition-order=6	\
		--qlp-coeff-precision-search	\
		--padding=131027		\
		$SRC/*.wav

	mv ${SRC}/*.flac ${DST}
	cp $SRC/data.toc $DST/data.toc || cp $SRC/TOC $DST/data.toc
done
