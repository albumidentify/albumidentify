#!/bin/sh

echo '<h1>Missing Release Events</h1>'
echo '<ul>'
(
for i in "$@"; do
	find $i -name 'report.txt' -print0 2>/dev/null | xargs -0 grep -i "No release events for" | sed 's/.*No release events for//'
done
) | sort | uniq | while read release; do
	echo '<li> <a href='$release.html' target=musicbrainz>'${release##*/}'</a>'
done
