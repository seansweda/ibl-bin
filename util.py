#!/usr/bin/python
#
# flags
# -B: batters only
# -P: batters only
# -A: all teams
# -p: platoon differential
# -v: vs average
# -s: start week
# -e: end week

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

def zero( stat ):
    stat['vL'] = []
    stat['vR'] = []
    for d in range(0,6):
        stat['vL'].append( 0.0 )
        stat['vR'].append( 0.0 )

def b_avg( stat ):
    # woba weighted average (for offense)
    return( ( stat['vL'][5] + stat['vR'][5] ) / \
            ( stat['vL'][0] + stat['vR'][0] ) )

def p_avg( stat ):
    # woba modified harmonic mean (for pitching)
    wL = stat['vL'][5] / stat['vL'][0]
    wR = stat['vR'][5] / stat['vR'][0]
    mean = ( wL + wR ) / 2.0
    harm = 2.0 * wL * wR / ( wL + wR )
    return( mean + abs(mean - harm) )

def bdump( team, stat, opt ):
    if stat['vL'][0] > 0 or stat['vR'][0] > 0:
        if stat['vL'][0] == 0:
            stat['vL'][0] += 1
        if stat['vR'][0] == 0:
            stat['vR'][0] += 1

        stat['avg'] = b_avg( stat )
        print "%s" % ( team ),
        for d in 1, 2, 3:
            print " %5.1f" % ( stat['vL'][d] / stat['vL'][0] ),
        print " %4.3f" % ( stat['vL'][4] / stat['vL'][0] ),
        print " %3d" % ( stat['vL'][5] / stat['vL'][0] + 0.5 ),
        print ".",
        for d in 1, 2, 3:
            print " %5.1f" % ( stat['vR'][d] / stat['vR'][0] ),
        print " %4.3f" % ( stat['vR'][4] / stat['vR'][0] ),
        print " %3d" % ( stat['vR'][5] / stat['vR'][0] + 0.5 ),
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
    if stat['vL'][0] > 0 or stat['vR'][0] > 0:
        if stat['vL'][0] == 0:
            stat['vL'][0] += 1
        if stat['vR'][0] == 0:
            stat['vR'][0] += 1

        stat['avg'] = p_avg( stat )
        print "%s" % ( team ),
        for d in 1, 2, 3, 4:
            print " %5.1f" % ( stat['vL'][d] / stat['vL'][0] ),
        print " %3d" % ( stat['vL'][5] / stat['vL'][0] + 0.5 ),
        print ".",
        for d in 1, 2, 3, 4:
            print " %5.1f" % ( stat['vR'][d] / stat['vR'][0] ),
        print " %3d" % ( stat['vR'][5] / stat['vR'][0] + 0.5 ),
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

def b_total( team, mlb, name ):
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

def p_total( team, mlb, name ):
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

db = DB.connect()
cursor = db.cursor()

# globals
ibl = {}
tot = {}
do_bat = True
do_pit = True
do_tot = False
do_opp = False
do_weekly = False
overall = 1
platoon = 2
avg = 3
display = overall
start = 1
end = 27
s_arg = ''
e_arg = ''

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'ABPopvws:e:')
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
    elif opt == '-s':
        s_arg = arg
    elif opt == '-e':
        e_arg = arg
    elif opt == '-w':
        do_weekly = True
    elif opt == '-A':
        do_tot = True
        cursor.execute("select distinct(ibl_team) from teams \
                where ibl_team != 'FA';")
        args += [ row[0] for row in sorted(cursor.fetchall()) ]
    else:
        print "bad option:", opt
        usage()

if s_arg and s_arg.isdigit():
    start = int(s_arg)

if e_arg and e_arg.isdigit():
    end = int(e_arg)

if do_weekly and ( s_arg or e_arg ):
    usage()

b_cards = p_hash( cardpath() + '/' + batters )
p_cards = p_hash( cardpath() + '/' + pitchers )

sql_weeks = "where week >= %d and week <= %d and " % ( start, end )

if do_bat:
    if do_pit:
        print "BATTERS"

    sql_select = "select trim(mlb), trim(name), sum(vl), sum(vr) from %s "\
            % ( DB.usage )
    zero( tot )

    for arg in args:
        team = arg.upper()

        ibl[team] = {}
        zero( ibl[team] )

        if do_weekly:
            sql = sql_select + sql_weeks + \
                " week = (%s) and ibl = (%s) and bf = 0 group by mlb, name;"
            for week in range(1,28):
                cursor.execute(sql, (week, team, ) )
                for mlb, name, paL, paR in cursor.fetchall():
                    b_total( team, mlb, name )
                bdump( team, ibl[team], overall )
                zero( ibl[team] )
            print
            continue
        if do_opp:
            sql = sql_select + sql_weeks + \
                " (home = (%s) or away = (%s)) and ibl != (%s) and bf = 0\
                group by mlb, name;"
            cursor.execute(sql, (team, team, team, ) )
        else:
            sql = sql_select + sql_weeks + \
                " ibl = (%s) and bf = 0 group by mlb, name;"
            cursor.execute(sql, (team, ) )

        for mlb, name, paL, paR in cursor.fetchall():
            b_total( team, mlb, name )

        for d in range(0,6):
            tot['vL'][d] += ibl[team]['vL'][d]
            tot['vR'][d] += ibl[team]['vR'][d]
    #end arg loop

    for t in sorted(ibl):
        if display == avg:
            tot['avg'] = b_avg( tot )
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
        if not do_weekly:
            print
        print "PITCHERS"

    sql_select = "select trim(mlb), trim(name), sum(bf) from %s "\
            % ( DB.usage )
    zero( tot )

    for arg in args:
        team = arg.upper()

        ibl[team] = {}
        zero( ibl[team] )

        if do_weekly:
            sql = sql_select + sql_weeks + \
                " week = (%s) and ibl = (%s) and bf > 0 group by mlb, name;"
            for week in range(1,28):
                cursor.execute(sql, (week, team, ) )
                for mlb, name, bf in cursor.fetchall():
                    p_total( team, mlb, name )
                pdump( team, ibl[team], overall )
                zero( ibl[team] )
            print
            continue
        if do_opp:
            sql = sql_select + sql_weeks + \
                " (home = (%s) or away = (%s)) and ibl != (%s) and bf > 0\
                group by mlb, name;"
            cursor.execute(sql, (team, team, team, ) )
        else:
            sql = sql_select + sql_weeks + \
                " ibl = (%s) and bf > 0 group by mlb, name;"
            cursor.execute(sql, (team, ) )

        for mlb, name, bf in cursor.fetchall():
            p_total( team, mlb, name )

        for d in range(0,6):
            tot['vL'][d] += ibl[team]['vL'][d]
            tot['vR'][d] += ibl[team]['vR'][d]
    #end arg loop

    for t in sorted(ibl):
        if display == avg:
            tot['avg'] = p_avg( tot )
            pdump( t, ibl[t], tot['avg'] )
        else:
            pdump( t, ibl[t], display )
    if do_tot:
        if display == avg:
            pdump( '---', tot, 0 )
        else:
            pdump( '---', tot, display )

db.close()

