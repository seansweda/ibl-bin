#!/bin/bash

data=/tmp/picks.txt
#year=${IBL_PICKSYEAR:-`date +%Y`}

if [ $# -ne 0 ]; then
    if [ x`find $data -mtime -1 2>/dev/null` != x${data} ]; then
	picks.py >| /tmp/picks.txt
    fi

    for x in $*; do
	awk -v team=`echo $x | tr a-z A-Z` '$2 ~ team' /tmp/picks.txt
    done
else
    exec picks.py
fi

