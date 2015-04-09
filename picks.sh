#!/bin/bash

data=/tmp/picks.txt
year=${IBL_PICKSYEAR:-`date +%Y`}

if [ $# -eq 0 ]; then
    exec picks.py -y $year
else
    if [ x`find $data -mtime -1 2>/dev/null` != x${data} ]; then
	picks.py -y $year >| /tmp/picks.txt
    fi

    for x in $*; do
	awk -v team=`echo $x | tr a-z A-Z` '$2 ~ team' /tmp/picks.txt
    done
fi

