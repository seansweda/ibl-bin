#!/usr/bin/python
#
# flags
# -A: average card
# -b: batter card
# -p: pitcher card
# -g: grep mode (default)
# -h: hash mode

import os
import sys
import yaml
import subprocess
import re
import getopt
import time

import DB

batters = "d1.genbat"
pitchers = "d1.genpit"

try:
    f = open( DB.bin_dir() + '/data/avgcard.yml', 'rU' )
except IOError, err:
    print str(err)
    sys.exit(1)

y = yaml.safe_load(f)

# wOBA consts
wBB = y['wBB']
w1B = y['w1B']
w2B = y['w2B']
w3B = y['w3B']
wHR = y['wHR']

# cardengine consts.h
IFR1B = y['IFR1B']
IFR2B = y['IFR2B']
OFR1B = y['OFR1B']
OFR2B = y['OFR2B']
PARK1B = y['PARK1B']
PARK2B = y['PARK2B']
PARK3B = y['PARK3B']
WILD1B = y['WILD1B']
WILD2B = y['WILD2B']
WILD3B = y['WILD3B']
WILDBB = y['WILDBB']
WILDHB = y['WILDHB']

avg_pwr = "Av"

def usage():
    print "usage: %s { -b | -p } ( -g | -h ) player(s)" % sys.argv[0]
    sys.exit(1)

def cardpath():
    if 'IBL_CARDPATH' in os.environ.keys():
        cardpath = os.environ.get('IBL_CARDPATH')
    else:
        cardpath = "/home/iblgame/" + time.strftime("%Y") + "/build"
    return cardpath

def p_hash(datafile, lower=False):
    try:
        fp = open(datafile,'rU')
    except IOError, err:
        print str(err)
        sys.exit(1)

    myhash = {}
    for line in file.readlines(fp):
        line = line.rstrip('\n')
        player = re.split(r'[\s,]+', line)
        if lower:
            myhash[ ( player[0].lower(), player[1].lower() ) ] = player[:]
        else:
            myhash[ ( player[0], player[1] ) ] = player[:]

    file.close(fp)
    return myhash

def p_grep(player, datafile):
    cmd = ['egrep', '-i']
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

def p_split(p_str, lower=False):
    p_list = re.split('\W+', p_str, maxsplit=1)
    if len(p_list) == 2:
        if lower:
            return ( p_list[0].lower(), p_list[1].lower() )
        else:
            return ( p_list[0], p_list[1] )
    else:
        return None

def batprint(p):
    print "%-3s %-15s vL %4s%4s%4s%4s%4s%4s%4s  .%4i .%4s%4s%4s %3s" % \
        ( p[0], p[1], p[14], p[15], p[16], p[17], p[18], p[19], p[20], wOBA(p, 0, 0), p[21], p[22], p[23], p[24], )
    print "%-3s %-15s vR %4s%4s%4s%4s%4s%4s%4s  .%4i .%4s%4s%4s %3s" % \
        ( p[0], p[1], p[26], p[27], p[28], p[29], p[30], p[31], p[32], wOBA(p, 0, 1), p[33], p[34], p[35], p[36], )

def pitprint(p):
    print "%-3s %-15s vL %4s%4s%4s%4s%4s%4s%4s%4s  .%4i .%4s%4s%4s" % \
        ( p[0], p[1], p[16], p[17], p[18], p[19], p[20], p[21], p[22], p[23], wOBA(p, 1, 0), p[24], p[25], p[26] )
    print "%-3s %-15s vR %4s%4s%4s%4s%4s%4s%4s%4s  .%4i .%4s%4s%4s" % \
        ( p[0], p[1],  p[28], p[29], p[30], p[31], p[32], p[33], p[34], p[35], wOBA(p, 1, 1), p[36], p[37], p[38] )

def power( rating ):
    if rating == "Ex":
        return 0.5
    elif rating == "Vg":
        return 0.4
    elif rating == "Fr":
        return 0.2
    elif rating == "Pr":
        return 0.1
    else:
        try:
            float(rating)
        except ValueError:
            return 0.3

        return float(rating)

def bat_wOBA( card = y['batcard'] ):
    woba = 0
    woba += card[0] * w1B
    woba += card[1] * w2B
    woba += card[2] * w3B
    woba += card[3] * wHR
    woba += card[4] * wBB
    woba += card[5] * wBB
    woba += (PARK1B + WILD1B) * w1B
    woba += (PARK2B + WILD2B) * w2B
    woba += (PARK3B + WILD3B) * w3B
    woba += (WILDBB + WILDHB) * wBB
    return woba

def pit_wOBA( pwr, card = y['pitcard'] ):
    woba = 0
    woba += card[0] * w1B
    woba += card[1] * w2B
    woba += card[2] * power(pwr) * wHR
    woba += card[3] * wBB
    woba += card[4] * wBB
    woba += card[5] * IFR1B * w1B
    woba += card[5] * IFR2B * w2B
    woba += card[6] * OFR1B * w1B
    woba += card[6] * OFR2B * w2B
    woba += (PARK1B + WILD1B) * w1B
    woba += (PARK2B + WILD2B) * w2B
    woba += (PARK3B + WILD3B) * w3B
    woba += (WILDBB + WILDHB) * wBB
    return woba

def wOBA(p, kind, side):
    global avg_pwr
    # pitcher
    if kind == 1:
        if side == 0:
            index = 16
        else:
            index = 28

        woba = 0
        woba += int(p[index]) * w1B
        woba += int(p[index + 1]) * w2B
        woba += int(p[index + 2]) * power(avg_pwr) * wHR
        woba += int(p[index + 3]) * wBB
        woba += int(p[index + 4]) * wBB
        woba += int(p[index + 5]) * IFR1B * w1B
        woba += int(p[index + 5]) * IFR2B * w2B
        woba += int(p[index + 6]) * OFR1B * w1B
        woba += int(p[index + 6]) * OFR2B * w2B
        return int(woba + bat_wOBA() + 0.5)

    # batter
    else:
        if side == 0:
            index = 14
        else:
            index = 26

        woba = 0
        woba += int(p[index]) * w1B
        woba += int(p[index + 1]) * w2B
        woba += int(p[index + 2]) * w3B
        woba += int(p[index + 3]) * wHR
        woba += int(p[index + 4]) * wBB
        woba += int(p[index + 5]) * wBB
        return int(woba + pit_wOBA( p[index + 10] ) + 0.5)

def avgcard():
    b_cards = p_hash( cardpath() + '/' + batters )
    p_cards = p_hash( cardpath() + '/' + pitchers )

    bat = []
    for d in range(0,7):
        bat.append(0.0)

    for c in sorted( b_cards ):
        for index in 14, 26:
            if c[0] != 'Player':
                bat[6] += float(b_cards[c][index + 11])
                for d in range(0,6):
                    bat[d] += ( float(b_cards[c][index + d]) *
                            float(b_cards[c][index + 11]) )

    print "         1B     2B     3B     HR     HB     BB"
    print "BAT: ",
    for d in range(0,6):
        bat[d] /= bat[6]
    for d in range(0,6):
        print "%5.1f " % ( bat[d] ),
    print "%5.1f " % ( bat[6] )
    print yaml.dump( bat, default_flow_style=False )

    pit = []
    for d in range(0,8):
        pit.append(0.0)

    for c in sorted( p_cards ):
        for index in 16, 28:
            if c[0] != 'Player':
                pit[7] += float(p_cards[c][index + 11])
                for d in range(0,7):
                    pit[d] += ( float(p_cards[c][index + d]) *
                            float(p_cards[c][index + 11]) )

    print "         1B     2B     DF     HB     BB    IFR    OFR"
    print "PIT: ",
    for d in range(0,7):
        pit[d] /= pit[7]
    for d in range(0,7):
        print "%5.1f " % ( pit[d] ),
    print "%5.1f " % ( pit[7] )
    print yaml.dump( pit, default_flow_style=False )

    woba = bat_wOBA( bat ) + pit_wOBA( 'Av', pit )
    # don't double-count park/wild
    woba -= (PARK1B + WILD1B) * w1B
    woba -= (PARK2B + WILD2B) * w2B
    woba -= (PARK3B + WILD3B) * w3B
    woba -= (WILDBB + WILDHB) * wBB
    print "wOBA: %s (%s/%s)" % ( int(woba + 0.5), int(bat_wOBA( bat )),
            int(pit_wOBA( 'Av', pit )) )
    sys.exit(0)

def main():
    global batters, pitchers, grepcmd, avg_pwr
    bat = 0
    pit = 0
    grepmode = 1    # default
    hashmode = 0
    datadir = cardpath()

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'Apbghwd:P:')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    for (opt, arg) in opts:
        if opt == '-b':
            bat = 1
        elif opt == '-p':
            pit = 1
        elif opt == '-d':
            # overrides cardpath()
            datadir = arg
        elif opt == '-g':
            grepmode = 1
            hashmode = 0
        elif opt == '-h':
            hashmode = 1
            grepmode = 0
        elif opt == '-w':
            grepcmd.append('-w')
        elif opt == '-A':
            avgcard()
        elif opt == '-P':
            avg_pwr = arg
        else:
            print "bad option:", opt
            usage()

    if ( bat and pit ) or ( not bat and not pit ):
        print "must choose between -b (batters) & -p (pitchers)"
        usage()
    elif bat:
        datafile = datadir + '/' + batters
    else:
        datafile = datadir + '/' + pitchers

    if bat:
        print "Player                   1B  2B  3B  HR  HB  BB  HG   wOBA     H  OB  TB  Pw"
    else:
        print "Player                   1B  2B  DF  HB  BB IFR OFR  HG   wOBA     H  OB  TB"

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
            for line in p_grep(arg, datafile):
                if bat:
                    batprint( line.split() )
                else:
                    pitprint( line.split() )


if __name__ == "__main__":
    main()

