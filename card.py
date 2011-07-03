#!/usr/bin/python
# $Id: card.sh,v 1.8 2011/03/18 16:57:18 sweda Exp $

import os
import sys
import subprocess
import re
import getopt

datadir = "/home/ibl/iblgame/2011/build"
batters = "d1.genbat"
pitchers = "d1.genpit"
grepcmd = ['/bin/egrep', '-i']

def usage():
    print "usage: %s { -b | -p } ( -g | -h ) player(s)" % sys.argv[0]
    sys.exit(1)

def p_hash(datafile):
    try:
        fp = open(datafile,'rU')
    except IOError, err:
        print str(err)
        sys.exit(1)

    myhash = {}
    for line in file.readlines(fp):
        player = line.split()
        myhash[ ( player[0].lower(), player[1].lower() ) ] = player[:]

    file.close(fp)
    return myhash

def p_grep(player, datafile, cmd):
    cmd.append(player)
    cmd.append(datafile)
    try: 
        fp = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    except IOError, err:
        print str(err)
        sys.exit(1)
    except OSError, err:
        print str(err)
        sys.exit(1)
    
    lines = file.readlines(fp.stdout)
    fp.stdout.close()
    return lines

def p_split(p_str):
    p_list = re.split('\W+', p_str, maxsplit=1)
    if len(p_list) == 2:
        return ( p_list[0].lower(), p_list[1].lower() )
    else:
        return None

def batprint(p):
    print "%-3s %-12s vL %4s%4s%4s%4s%4s%4s  - %4s%4s%4s %3s" % \
        ( p[0], p[1], p[14], p[15], p[16], p[17], p[18], p[19], p[20], p[21], p[22], p[23] )
    print "%-3s %-12s vR %4s%4s%4s%4s%4s%4s  - %4s%4s%4s %3s" % \
        ( p[0], p[1], p[25], p[26], p[27], p[28], p[29], p[30], p[31], p[32], p[33], p[34] )

def pitprint(p):
    print "%-3s %-12s vL %4s%4s%4s%4s%4s%4s%4s  - %4s%4s%4s" % \
        ( p[0], p[1], p[16], p[17], p[18], p[19], p[20], p[21], p[22], p[23], p[24], p[25] )
    print "%-3s %-12s vR %4s%4s%4s%4s%4s%4s%4s  - %4s%4s%4s" % \
        ( p[0], p[1], p[27], p[28], p[29], p[30], p[31], p[32], p[33], p[34], p[35], p[36] )

def main():
    global datadir, batters, pitchers, grepcmd
    bat = 0
    pit = 0
    grepmode = 1    # default
    hashmode = 0

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'pbghwd:')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    for (opt, arg) in opts:
        if opt == '-b':
            bat = 1
        elif opt == '-p':
            pit = 1
        elif opt == '-d':
            datadir = arg
        elif opt == '-g':
            grepmode = 1
            hashmode = 0
        elif opt == '-h':
            hashmode = 1
            grepmode = 0
        elif opt == '-w':
            grepcmd.append('-w')
        else:
            print "bad option:", opt
            usage()

    if 'CARDPATH' in os.environ.keys():
        datadir = os.environ.get('CARDPATH')

    if ( bat and pit ) or ( not bat and not pit ):
        print "must choose between -b (batters) & -p (pitchers)"
        usage()
    elif bat:
        datafile = datadir + '/' + batters
    else:
        datafile = datadir + '/' + pitchers

    if bat:
        print "Player                1B  2B  3B  HR  HB  BB       H  OB  XB  Pw"
    else:
        print "Player                1B  2B  DF  HB  BB IFR OFR       H  OB  XB"

    if hashmode:
        cards = p_hash(datafile)

    for arg in args:
        if hashmode: 
            if p_split(arg) in cards:
                if bat:
                    batprint( cards[ p_split(arg) ] )
                else:
                    pitprint( cards[ p_split(arg) ] )
        else:
            for line in p_grep(arg, datafile, grepcmd):
                if bat:
                    batprint( line.split() )
                else:
                    pitprint( line.split() )


if __name__ == "__main__":
    main()

