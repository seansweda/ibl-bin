#!/bin/bash

if [ $# -eq 0 ]; then
    exec picks.py
else
    if ! [ -s /tmp/picks.txt ]; then
	picks.py >| /tmp/picks.txt
    fi

    for x in $*; do
	awk -v team=`echo $x | tr a-z A-Z` '$2 == team' /tmp/picks.txt
    done
fi

