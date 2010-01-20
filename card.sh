#!/bin/sh
# $Id: card,v 1.4 2008/03/10 08:31:38 sweda Exp sweda $

# -b: batters
# -p: pitchers
# -d: data directory
# -w: use -w flag with egrep (exact match)

year="2009"
dir="/home/ibl/iblgame/${year}/build"

if [ -f $HOME/.card ]; then
    . $HOME/.card
fi

usage() {
    echo "usage: $0 { -b | -p  } player"
    exit 1
}

while getopts bpwd: opt; do
    case $opt in
    p)	if [ $awkf ]; then
	    usage
	else
	    awkf=${dir}/d0.genpit
	fi
	;;

    b)	if [ $awkf ]; then
	    usage
	else
	    awkf=${dir}/d0.genbat
	fi
	;;

    d)  dir=$OPTARG
	;;

    w)  match="-w"
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
	egrep $match -i "$player" $awkf | awk '{ printf "%-3s %-12s vL %4d%4d%4d%4d%4d%4d%4d  - %4d%4d%4d\n",
	    $1, $2, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24 }'
	egrep $match -i "$player" $awkf | awk '{ printf "%-3s %-12s vR %4d%4d%4d%4d%4d%4d%4d  - %4d%4d%4d\n",
	    $1, $2, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35 }'
    done
else
    echo "Player                1B  2B  3B  HR  HB  BB       H  OB  XB  Pw"
    for player in $*; do
	egrep $match -i "$player" $awkf | awk '{ printf "%-3s %-12s vL %4d%4d%4d%4d%4d%4d  - %4d%4d%4d %3s\n",
	    $1, $2, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24 }'
	egrep $match -i "$player" $awkf | awk '{ printf "%-3s %-12s vR %4d%4d%4d%4d%4d%4d  - %4d%4d%4d %3s\n",
	    $1, $2, $26, $27, $28, $29, $30, $31, $32, $33, $34, $35 }'
    done
fi

