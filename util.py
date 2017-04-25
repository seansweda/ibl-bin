#!/usr/bin/python
#
# flags
# -B: batters only
# -P: batters only
# -A: all teams

import sys
import getopt

import psycopg2
import DB

from card import p_split, p_hash, cardpath, batters, pitchers, wOBA

def usage():
    print "usage: %s " % sys.argv[0]
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
        return( [ int(p[24]), int(p[25]), int(p[26]) ] )
    else:
        return( [ int(p[21]), int(p[22]), int(p[23]), power(p[24]) ] )

def vsR(p, kind):
# pitcher
    if kind == 1:
        return( [ int(p[36]), int(p[37]), int(p[38]) ] )
    else:
        return( [ int(p[33]), int(p[34]), int(p[35]), power(p[36]) ] )

db = DB.connect()
cursor = db.cursor()

# globals
do_bat = True
do_pit = True

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'ABP')
except getopt.GetoptError, err:
    print str(err)
    usage()

for (opt, arg) in opts:
    if opt == '-B':
        do_pit = False
    elif opt == '-P':
        do_bat = False
    elif opt == '-A':
        cursor.execute("select distinct(ibl_team) from teams \
                where ibl_team != 'FA';")
        args += [ row[0] for row in sorted(cursor.fetchall()) ]
    else:
        print "bad option:", opt
        usage()

b_cards = p_hash( cardpath() + '/' + batters )
p_cards = p_hash( cardpath() + '/' + pitchers )

for arg in args:
    totL = []
    totR = []
    for d in range(0,6):
        totL.append( 0.0 )
        totR.append( 0.0 )

    team = arg.upper()
    sql = "select trim(mlb) as mlb, trim(name) as name, sum(vl), sum(vr)\
            from %s where ibl = '%s' and bf = 0\
            group by mlb, name;" % ( DB.usage, team )
    cursor.execute(sql)
    for mlb, name, paL, paR in cursor.fetchall():
        if (mlb, name) in b_cards:
            vl = vsL(b_cards[mlb, name], 2)
            vr = vsR(b_cards[mlb, name], 2)
            #print mlb, name, paL, vl
            #print mlb, name, paR, vr
            totL[0] += paL
            totR[0] += paR
            for d in 1, 2, 3, 4:
                totL[d] += vl[d - 1] * paL
                totR[d] += vr[d - 1] * paR
            totL[5] += wOBA(b_cards[mlb, name], 2, 0) * paL
            totR[5] += wOBA(b_cards[mlb, name], 2, 1) * paR

    #print totL, totR
    print "%s" % ( team ),
    for d in 1, 2, 3:
        print " %5.1f" % ( totL[d] / totL[0] ),
    print " %4.3f" % ( totL[4] / totL[0] ),
    print " %d" % ( totL[5] / totL[0] + 0.5 ),
    print ".",
    for d in 1, 2, 3:
        print " %5.1f" % ( totR[d] / totR[0] ),
    print " %4.3f" % ( totR[4] / totR[0] ),
    print " %d" % ( totR[5] / totR[0] + 0.5 ),
    print ".",
    print "%+5.1f" % ( totL[5] / totL[0] - totR[5] / totR[0] )

db.close()

