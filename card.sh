#!/bin/sh
# $Id: usage,v 1.1 2007/07/19 03:40:15 sweda Exp $

# -b: batters
# -p: pitchers

year=2007
ibl=/home/ibl/iblgame

while getopts bp opt; do
    case $opt in
    p)	if [ $awkf ]; then
	    usage
	else
	    awkf=${ibl}/${year}/build/d0.genpit
	fi
	;;

    b)	if [ $awkf ]; then
	    usage
	else
	    awkf=${ibl}/${year}/build/d0.genbat
	fi
	;;

    *)	usage
	;;

    esac
done

if [ ! $awkf ]; then
    usage
fi

shift `expr $OPTIND - 1`

echo $awkf | grep -q pit 
if [ $? -eq 0 ]; then
    echo "Player                1B  2B  DF  HB  BB IFR OFR       H  OB  XB"
    for player in $*; do
	egrep -i "$player" $awkf | awk '{ printf "%-3s %-12s vL %4d%4d%4d%4d%4d%4d%4d  - %4d%4d%4d\n",
	    $1, $2, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23 }'
	egrep -i "$player" $awkf | awk '{ printf "%-3s %-12s vR %4d%4d%4d%4d%4d%4d%4d  - %4d%4d%4d\n",
	    $1, $2, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34 }'
    done
else
    echo "Player                1B  2B  3B  HR  HB  BB       H  OB  XB  Pw"
    for player in $*; do
	egrep -i "$player" $awkf | awk '{ printf "%-3s %-12s vL %4d%4d%4d%4d%4d%4d  - %4d%4d%4d %3s\n",
	    $1, $2, $14, $15, $16, $17, $18, $19, $20, $21, $22, $23 }'
	egrep -i "$player" $awkf | awk '{ printf "%-3s %-12s vR %4d%4d%4d%4d%4d%4d  - %4d%4d%4d %3s\n",
	    $1, $2, $25, $26, $27, $28, $29, $30, $31, $32, $33, $34 }'
    done
fi

