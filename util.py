#!/usr/bin/python
#
# flags
# -B: batters only
# -P: batters only
# -A: all teams
# -M: MLB usage (-a for active only)
# -p: platoon differential
# -v: vs average
# -s: start week
# -e: end week

from __future__ import (print_function, unicode_literals)

import sys
import getopt

import psycopg2
import DB

from card import p_split, p_hash, cardpath, batters, pitchers, wOBA
from usage import mlb_usage

# identifiers
pit = 1
bat = 2
left = 0
right = 1

def usage():
    print("usage: %s [-ABP] <team>" % sys.argv[0])
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

def bE_avg( stat ):
    # batter woba estimated using generic 27/73 (vLHP/vRHP) split
    wL = stat['vL'][5] / stat['vL'][0]
    wR = stat['vR'][5] / stat['vR'][0]
    return( wL * 0.27 + wR * 0.73 )

def pE_avg( stat ):
    # pitcher woba estimated using generic 43/57 (vLHB/vRHB) split
    wL = stat['vL'][5] / stat['vL'][0]
    wR = stat['vR'][5] / stat['vR'][0]
    return( wL * 0.43 + wR * 0.57 )

def bdump( team, stat, opt, afunc ):
    if stat['vL'][0] > 0 or stat['vR'][0] > 0:
        if stat['vL'][0] == 0:
            stat['vL'][0] += 1
        if stat['vR'][0] == 0:
            stat['vR'][0] += 1

        stat['avg'] = afunc( stat )
        print("%s" % ( team ), end=' ')
        for d in 1, 2, 3:
            print(" %5.1f" % ( stat['vL'][d] / stat['vL'][0] ), end=' ')
        print(" %4.3f" % ( stat['vL'][4] / stat['vL'][0] ), end=' ')
        print(" %3d" % ( stat['vL'][5] / stat['vL'][0] + 0.5 ), end=' ')
        print(".", end=' ')
        for d in 1, 2, 3:
            print(" %5.1f" % ( stat['vR'][d] / stat['vR'][0] ), end=' ')
        print(" %4.3f" % ( stat['vR'][4] / stat['vR'][0] ), end=' ')
        print(" %3d" % ( stat['vR'][5] / stat['vR'][0] + 0.5 ), end=' ')
        print(".", end=' ')
        if opt == 0:
            print("%5.1f" % ( 0.0 ))
        elif opt == overall:
            print(" %3d" % ( stat['avg'] + 0.5 ))
        elif opt == platoon:
            # platoon differential
            print("%+5.1f" % ( stat['vL'][5] / stat['vL'][0] -
                    stat['vR'][5] / stat['vR'][0] ))
        else:
            # vs average
            print("%+5.1f" % ( stat['avg'] - opt ))

def pdump( team, stat, opt, afunc ):
    if stat['vL'][0] > 0 or stat['vR'][0] > 0:
        if stat['vL'][0] == 0:
            stat['vL'][0] += 1
        if stat['vR'][0] == 0:
            stat['vR'][0] += 1

        stat['avg'] = afunc( stat )
        print("%s" % ( team ), end=' ')
        for d in 1, 2, 3, 4:
            print(" %5.1f" % ( stat['vL'][d] / stat['vL'][0] ), end=' ')
        print(" %3d" % ( stat['vL'][5] / stat['vL'][0] + 0.5 ), end=' ')
        print(".", end=' ')
        for d in 1, 2, 3, 4:
            print(" %5.1f" % ( stat['vR'][d] / stat['vR'][0] ), end=' ')
        print(" %3d" % ( stat['vR'][5] / stat['vR'][0] + 0.5 ), end=' ')
        print(".", end=' ')
        if opt == 0:
            print("%5.1f" % ( 0.0 ))
        elif opt == overall:
            print(" %3d" % ( stat['avg'] + 0.5 ))
        elif opt == platoon:
            # platoon differential
            print("%+5.1f" % ( stat['vR'][5] / stat['vR'][0] -
                    stat['vL'][5] / stat['vL'][0] ))
        else:
            # vs average
            print("%+5.1f" % ( opt - stat['avg'] ))

# batter array: pa, h, ob, tb, pwr, woba
def b_total( team, mlb, name ):
    if (mlb, name) in b_cards:
        vl = vsL(b_cards[mlb, name], bat)
        vr = vsR(b_cards[mlb, name], bat)
        #print mlb, name, paL, vl
        #print mlb, name, paR, vr
        ibl[team]['vL'][0] += paL
        ibl[team]['vR'][0] += paR
        for d in 1, 2, 3, 4:
            ibl[team]['vL'][d] += vl[d - 1] * paL
            ibl[team]['vR'][d] += vr[d - 1] * paR
        ibl[team]['vL'][5] += wOBA(b_cards[mlb, name], bat, left) * paL
        ibl[team]['vR'][5] += wOBA(b_cards[mlb, name], bat, right) * paR

# pitcher array: bf, h, ob, tb, df, woba
def p_total( team, mlb, name ):
    if (mlb, name) in p_cards:
        vl = vsL(p_cards[mlb, name], pit)
        vr = vsR(p_cards[mlb, name], pit)
        #print mlb, name, bf, vl
        #print mlb, name, bf, vr
        ibl[team]['vL'][0] += bf
        ibl[team]['vR'][0] += bf
        for d in 1, 2, 3, 4:
            ibl[team]['vL'][d] += vl[d - 1] * bf
            ibl[team]['vR'][d] += vr[d - 1] * bf
        ibl[team]['vL'][5] += wOBA(p_cards[mlb, name], pit, left) * bf
        ibl[team]['vR'][5] += wOBA(p_cards[mlb, name], pit, right) * bf

db = DB.connect()
cursor = db.cursor()

# globals
ibl = {}
tot = {}
MLB_B = {}
MLB_P = {}
do_bat = True
do_pit = True
do_tot = False
do_opp = False
do_weekly = False
do_mlb = False
overall = 1
platoon = 2
avg = 3
display = overall
start = 1
end = 27
s_arg = ''
e_arg = ''
active = ''

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'ABPMaopvws:e:y:')
except getopt.GetoptError as err:
    print(str(err))
    usage()

for (opt, arg) in opts:
    if opt == '-B':
        do_pit = False
    elif opt == '-P':
        do_bat = False
    elif opt == '-a':
        active = ' and status = 1'
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
    elif opt == '-y':
        DB.usage = 'usage' + arg
    elif opt == '-A':
        do_tot = True
        cursor.execute("select distinct(ibl_team) from rosters \
                where ibl_team != 'FA';")
        args += [ row[0] for row in sorted(cursor.fetchall()) ]
    elif opt == '-M':
        do_mlb = True
        mlb_usage( MLB_P, MLB_B )
    else:
        print("bad option:", opt)
        usage()

if s_arg and s_arg.isdigit():
    start = int(s_arg)

if e_arg and e_arg.isdigit():
    end = int(e_arg)

if do_weekly and ( s_arg or e_arg or do_opp or display == avg ):
    usage()

if do_mlb and ( do_weekly or do_opp ):
    usage()

b_cards = p_hash( cardpath() + '/' + batters )
p_cards = p_hash( cardpath() + '/' + pitchers )

sql_weeks = "where week >= %d and week <= %d and " % ( start, end )

if do_mlb:
    # current UC designation
    sql = "select max(uncarded) from rosters;"
    cursor.execute(sql)
    ( UCyy, ) = cursor.fetchone()

if do_bat:
    if do_pit:
        print("BATTERS")

    sql_select = "select trim(mlb), trim(name), sum(vl), sum(vr) from %s "\
            % ( DB.usage )
    zero( tot )

    if do_mlb:
        avg_B = bE_avg
    else:
        avg_B = b_avg

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
                if display == platoon:
                    bdump( team, ibl[team], platoon, avg_B )
                else:
                    bdump( team, ibl[team], overall, avg_B )
                zero( ibl[team] )
            print()
            continue
        if do_mlb:
            sql = "select trim(tig_name) from rosters where \
                    ibl_team = (%s) and uncarded < (%s) and item_type = 2"
            cursor.execute(sql + active, (team, UCyy ) )
        elif do_opp:
            sql = sql_select + sql_weeks + \
                " (home = (%s) or away = (%s)) and ibl != (%s) and bf = 0\
                group by mlb, name;"
            cursor.execute(sql, (team, team, team, ) )
        else:
            sql = sql_select + sql_weeks + \
                " ibl = (%s) and bf = 0 group by mlb, name;"
            cursor.execute(sql, (team, ) )

        if do_mlb:
            for tig_name in cursor.fetchall():
                tigname = tig_name[0]
                mlb, name = tigname.split()
                paL = paR = MLB_B[tigname]
                b_total( team, mlb, name )
        else:
            for mlb, name, paL, paR in cursor.fetchall():
                b_total( team, mlb, name )

        for d in range(0,6):
            tot['vL'][d] += ibl[team]['vL'][d]
            tot['vR'][d] += ibl[team]['vR'][d]
    #end arg loop

    for t in sorted(ibl):
        if display == avg:
            tot['avg'] = avg_B( tot )
            bdump( t, ibl[t], tot['avg'], avg_B )
        else:
            bdump( t, ibl[t], display, avg_B )
    if do_tot:
        if display == avg:
            bdump( '---', tot, 0, avg_B )
        else:
            bdump( '---', tot, display, avg_B )

if do_pit:
    if do_bat:
        if not do_weekly:
            print()
        print("PITCHERS")

    sql_select = "select trim(mlb), trim(name), sum(bf) from %s "\
            % ( DB.usage )
    zero( tot )

    if do_mlb:
        avg_P = pE_avg
    else:
        avg_P = p_avg

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
                if display == platoon:
                    pdump( team, ibl[team], platoon, avg_P )
                else:
                    pdump( team, ibl[team], overall, avg_P )
                zero( ibl[team] )
            print()
            continue
        if do_mlb:
            sql = "select trim(tig_name) from rosters where \
                    ibl_team = (%s) and uncarded < (%s) and item_type = 1"
            cursor.execute(sql + active, (team, UCyy ) )
        elif do_opp:
            sql = sql_select + sql_weeks + \
                " (home = (%s) or away = (%s)) and ibl != (%s) and bf > 0\
                group by mlb, name;"
            cursor.execute(sql, (team, team, team, ) )
        else:
            sql = sql_select + sql_weeks + \
                " ibl = (%s) and bf > 0 group by mlb, name;"
            cursor.execute(sql, (team, ) )

        if do_mlb:
            for tig_name in cursor.fetchall():
                tigname = tig_name[0]
                mlb, name = tigname.split()
                bf = MLB_P[tigname]
                p_total( team, mlb, name )
        else:
            for mlb, name, bf in cursor.fetchall():
                p_total( team, mlb, name )

        for d in range(0,6):
            tot['vL'][d] += ibl[team]['vL'][d]
            tot['vR'][d] += ibl[team]['vR'][d]
    #end arg loop

    for t in sorted(ibl):
        if display == avg:
            tot['avg'] = avg_P( tot )
            pdump( t, ibl[t], tot['avg'], avg_P )
        else:
            pdump( t, ibl[t], display, avg_P )
    if do_tot:
        if display == avg:
            pdump( '---', tot, 0, avg_P )
        else:
            pdump( '---', tot, display, avg_P )

db.close()

