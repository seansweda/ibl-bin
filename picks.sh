#!/bin/bash

data=/tmp/picks.txt

while getopts :t: opt; do
    echo "getopt: \"$opt\",\"$OPTARG\""
    case $opt in
	t)  if [ x`find $data -mtime -1 2>/dev/null` != x${data} ]; then
		picks.py >| $data
	    fi
	    awk -v team=`echo "$OPTARG" | tr a-z A-Z` '$2 ~ team' $data
	    exit
	    ;;
    esac
done

exec picks.py $*
