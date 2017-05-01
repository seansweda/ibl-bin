#!/usr/bin/python
#
# flags
# -B: batters only
# -P: batters only
# -A: all teams
# -p: platoon differential
# -v: vs average

import sys
import getopt

import psycopg2
import DB

from card import p_split, p_hash, cardpath, batters, pitchers, wOBA

def usage():
    print "usage: %s [-ABP] <team>" % sys.argv[0]
    sys.exit(1)


def trim(string):
    if string and len(string) > 0:
        return string.rstrip()
    else:
        return ' '

def power( rating ):
    if rating == "Ex":
        return 0.5
    elif rating == "Vg":
        return 0.4
    elif rating == "Av":
        return 0.3
    elif rating == "Fr":
        return 0.2
    else:
        return 0.1

def vsL(p, kind):
# pitcher
    if kind == 1:
        return( [ int(p[24]), int(p[25]), int(p[26]), int(p[18]) ] )
    else:
        return( [ int(p[21]), int(p[22]), int(p[23]), power(p[24]) ] )

def vsR(p, kind):
# pitcher
    if kind == 1:
        return( [ int(p[36]), int(p[37]), int(p[38]), int(p[30]) ] )
    else:
        return( [ int(p[33]), int(p[34]), int(p[35]), power(p[36]) ] )

def bdump( team, stat, opt ):
    print "%s" % ( team ),
    for d in 1, 2, 3:
        print " %5.1f" % ( stat['vL'][d] / stat['vL'][0] ),
    print " %4.3f" % ( stat['vL'][4] / stat['vL'][0] ),
    print " %d" % ( stat['vL'][5] / stat['vL'][0] + 0.5 ),
    print ".",
    for d in 1, 2, 3:
        print " %5.1f" % ( stat['vR'][d] / stat['vR'][0] ),
    print " %4.3f" % ( stat['vR'][4] / stat['vR'][0] ),
    print " %d" % ( stat['vR'][5] / stat['vR'][0] + 0.5 ),
    print ".",
    if opt == 0:
        print "%5.1f" % ( 0.0 )
    elif opt == overall:
        print " %3d" % ( stat['avg'] + 0.5 )
    elif opt == platoon:
        # platoon differential
        print "%+5.1f" % ( stat['vL'][5] / stat['vL'][0] -
                stat['vR'][5] / stat['vR'][0] )
    else:
        # vs average
        print "%+5.1f" % ( stat['avg'] - opt )

def pdump( team, stat, opt ):
    print "%s" % ( team ),
    for d in 1, 2, 3, 4:
        print " %5.1f" % ( stat['vL'][d] / stat['vL'][0] ),
    print " %d" % ( stat['vL'][5] / stat['vL'][0] + 0.5 ),
    print ".",
    for d in 1, 2, 3, 4:
        print " %5.1f" % ( stat['vR'][d] / stat['vR'][0] ),
    print " %d" % ( stat['vR'][5] / stat['vR'][0] + 0.5 ),
    print ".",
    if opt == 0:
        print "%5.1f" % ( 0.0 )
    elif opt == overall:
        print " %3d" % ( stat['avg'] + 0.5 )
    elif opt == platoon:
        # platoon differential
        print "%+5.1f" % ( stat['vL'][5] / stat['vL'][0] -
                stat['vR'][5] / stat['vR'][0] )
    else:
        # vs average
        print "%+5.1f" % ( opt - stat['avg'] )

db = DB.connect()
cursor = db.cursor()

# globals
ibl = {}
tot = {}
do_bat = True
do_pit = True
do_tot = False
do_opp = False
overall = 1
platoon = 2
avg = 3
display = overall

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'ABPopv')
except getopt.GetoptError, err:
    print str(err)
    usage()

for (opt, arg) in opts:
    if opt == '-B':
        do_pit = False
    elif opt == '-P':
        do_bat = False
    elif opt == '-o':
        do_opp = True
    elif opt == '-p':
        display = platoon
    elif opt == '-v':
        display = avg
    elif opt == '-A':
        do_tot = True
        cursor.execute("select distinct(ibl_team) from teams \
                where ibl_team != 'FA';")
        args += [ row[0] for row in sorted(cursor.fetchall()) ]
    else:
        print "bad option:", opt
        usage()

b_cards = p_hash( cardpath() + '/' + batters )
p_cards = p_hash( cardpath() + '/' + pitchers )

if do_bat:
    if do_pit:
        print "BATTERS"

    tot['vL'] = []
    tot['vR'] = []
    for d in range(0,6):
        tot['vL'].append( 0.0 )
        tot['vR'].append( 0.0 )

    for arg in args:
        team = arg.upper()

        ibl[team] = {}
        ibl[team]['vL'] = []
        ibl[team]['vR'] = []
        for d in range(0,6):
            ibl[team]['vL'].append( 0.0 )
            ibl[team]['vR'].append( 0.0 )

        if do_opp:
            sql = "select trim(mlb), trim(name), sum(vl), sum(vr) from %s\
                where (home = '%s' or away = '%s') and ibl != '%s' and bf = 0\
                group by mlb, name;" % ( DB.usage, team, team, team )
        else:
            sql = "select trim(mlb), trim(name), sum(vl), sum(vr)\
                from %s where ibl = '%s' and bf = 0\
                group by mlb, name;" % ( DB.usage, team )
        cursor.execute(sql)
        for mlb, name, paL, paR in cursor.fetchall():
            if (mlb, name) in b_cards:
                vl = vsL(b_cards[mlb, name], 2)
                vr = vsR(b_cards[mlb, name], 2)
                #print mlb, name, paL, vl
                #print mlb, name, paR, vr
                ibl[team]['vL'][0] += paL
                ibl[team]['vR'][0] += paR
                for d in 1, 2, 3, 4:
                    ibl[team]['vL'][d] += vl[d - 1] * paL
                    ibl[team]['vR'][d] += vr[d - 1] * paR
                ibl[team]['vL'][5] += wOBA(b_cards[mlb, name], 2, 0) * paL
                ibl[team]['vR'][5] += wOBA(b_cards[mlb, name], 2, 1) * paR

        # woba weighted average
        ibl[team]['avg'] = ( ibl[team]['vL'][5] + ibl[team]['vR'][5] ) /\
                ( ibl[team]['vL'][0] + ibl[team]['vR'][0] )

        for d in range(0,6):
            tot['vL'][d] += ibl[team]['vL'][d]
            tot['vR'][d] += ibl[team]['vR'][d]
        # woba weighted average
        tot['avg'] = ( tot['vL'][5] + tot['vR'][5] ) /\
                ( tot['vL'][0] + tot['vR'][0] )
    #end arg loop

    for t in sorted(ibl):
        if display == avg:
            bdump( t, ibl[t], tot['avg'] )
        else:
            bdump( t, ibl[t], display )
    if do_tot:
        if display == avg:
            bdump( '---', tot, 0 )
        else:
            bdump( '---', tot, display )

if do_pit:
    if do_bat:
        print
        print "PITCHERS"

    tot['vL'] = []
    tot['vR'] = []
    for d in range(0,6):
        tot['vL'].append( 0.0 )
        tot['vR'].append( 0.0 )

    for arg in args:
        team = arg.upper()

        ibl[team] = {}
        ibl[team]['vL'] = []
        ibl[team]['vR'] = []
        for d in range(0,6):
            ibl[team]['vL'].append( 0.0 )
            ibl[team]['vR'].append( 0.0 )

        if do_opp:
            sql = "select trim(mlb), trim(name), sum(bf) from %s\
                where (home = '%s' or away = '%s') and ibl != '%s' and bf > 0\
                group by mlb, name;" % ( DB.usage, team, team, team )
        else:
            sql = "select trim(mlb), trim(name), sum(bf)\
                from %s where ibl = '%s' and bf > 0\
                group by mlb, name;" % ( DB.usage, team )
        cursor.execute(sql)
        for mlb, name, bf in cursor.fetchall():
            if (mlb, name) in p_cards:
                vl = vsL(p_cards[mlb, name], 1)
                vr = vsR(p_cards[mlb, name], 1)
                #print mlb, name, bf, vl
                #print mlb, name, bf, vr
                ibl[team]['vL'][0] += bf
                ibl[team]['vR'][0] += bf
                for d in 1, 2, 3, 4:
                    ibl[team]['vL'][d] += vl[d - 1] * bf
                    ibl[team]['vR'][d] += vr[d - 1] * bf
                ibl[team]['vL'][5] += wOBA(p_cards[mlb, name], 1, 0) * bf
                ibl[team]['vR'][5] += wOBA(p_cards[mlb, name], 1, 1) * bf

        # woba modified harmonic mean
        wL = ibl[team]['vL'][5] / ibl[team]['vL'][0]
        wR = ibl[team]['vR'][5] / ibl[team]['vR'][0]
        mean = ( wL + wR ) / 2.0
        harm = 2.0 * wL * wR / ( wL + wR )
        ibl[team]['avg'] = mean + abs(mean - harm)

        for d in range(0,6):
            tot['vL'][d] += ibl[team]['vL'][d]
            tot['vR'][d] += ibl[team]['vR'][d]
        # woba modified harmonic mean
        wL = tot['vL'][5] / tot['vL'][0]
        wR = tot['vR'][5] / tot['vR'][0]
        mean = ( wL + wR ) / 2.0
        harm = 2.0 * wL * wR / ( wL + wR )
        tot['avg'] = mean + abs(mean - harm)
    #end arg loop

    for t in sorted(ibl):
        if display == avg:
            pdump( t, ibl[t], tot['avg'] )
        else:
            pdump( t, ibl[t], display )
    if do_tot:
        if display == avg:
            pdump( '---', tot, 0 )
        else:
            pdump( '---', tot, display )

db.close()
