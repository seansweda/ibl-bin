#!/usr/bin/env python
#
# flags
# -c: card info
# -d: defensive ratings
# -r: baserunning
# -t: ob + tb totals
# -w: wOBA totals
# -u: MLB usage
# -a: active roster
# -i: inactive roster
# -n: number of players
# -p: picks
# -f: find player
# -B: batters only
# -P: batters only
# -H: no headers
# -A: all teams
# -O: old rosters
# -L: page breaks 

from __future__ import (print_function, unicode_literals)

import os
import sys
import getopt
import subprocess

import psycopg2

import DB

from card import p_split, p_hash, cardpath, batters, pitchers, wOBA
from usage import mlb_usage

def usage():
    print("usage: %s " % sys.argv[0])
    sys.exit(1)

def trim(string):
    if string and len(string) > 0:
        return string.rstrip()
    else:
        return ' '

def star(val, string):
    global do_card, do_def
    if do_card or do_def:
        return trim(string)
    else:
        if val == 1: return ' '
        else : return '*'

def cardtop(p, kind):
    # pitcher
    if kind == 1:
        return ( p[24], p[25], p[26], p[23], '.', p[36], p[37], p[38], p[35] )
    # batter
    else:
        return ( p[21], p[22], p[23], p[24], '.', p[33], p[34], p[35], p[36] )

def cardval(p, kind, calc):
    # pitcher
    if kind == 1:
        if calc == do_tot:
            sum_vL = int(p[25]) + int(p[26])
            sum_vR = int(p[37]) + int(p[38])
        else:
            sum_vL = wOBA(p, kind, 0)
            sum_vR = wOBA(p, kind, 1)

        if sum_vL + sum_vR > 0:
            harm = 2 * sum_vL * sum_vR / float(sum_vL + sum_vR)
        else:
            harm = 0
        mean = (sum_vL + sum_vR) / 2.0
        val = int(mean + abs(mean - harm) + 0.5)

        return ( p[24], p[25], p[26], p[23], str(sum_vL), '.',
                p[36], p[37], p[38], p[35], str(sum_vR), '.', str(val) )

    # batter
    else:
        if calc == do_tot:
            sum_vL = int(p[22]) + int(p[23])
            sum_vR = int(p[34]) + int(p[35])
        else:
            sum_vL = wOBA(p, kind, 0)
            sum_vR = wOBA(p, kind, 1)

        if sum_vL + sum_vR > 0:
            harm = 2 * sum_vL * sum_vR / float(sum_vL + sum_vR)
        else:
            harm = 0
        val = int(harm + 0.5)

        return ( p[21], p[22], p[23], p[24], str(sum_vL), '.',
                p[33], p[34], p[35], p[36], str(sum_vR), '.', str(val) )

def poslist(p, max):
    defense = ''
    index = 0
    while index + 1 < len(p):
        pos = p[index] + " " + p[index + 1]
        if len(defense) + len(pos) < max: 
            defense += pos
            defense += "  "
            index += 2
        else:
            break
    return defense.rstrip()

def brun(p):
    runs = "%2s/%2s/%2s" % ( p[2], p[3], p[4] )
    return runs

def pitrat(p):
    defense = "%s/%s  %s/%s  %s" % \
            ( p[2].replace('/0', '/ 0'), p[3], p[6], p[7], p[5] )
    return defense

def pitfat(p):
    fatigue = "%2s/%2s  " % ( p[2], p[3] )
    if len(p) == 5:
        fatigue += "%11s" % ( p[4] )
    else:
        index = 4
        while index < len(p):
            #print "%s %s %s\n" % (index, len(p), p[index])
            fatigue += " "
            fatigue += p[index]
            index += 1
    return fatigue

# globals
do_bat = True
do_pit = True
do_header = True
do_picks = False
do_active = True
do_inactive = True
do_card = False
do_def = False
do_br = False
do_find = False
do_usage = False
is_tty = False
count = False
eol = ''
do_val = 0
do_tot = 1
do_wOBA = 2
rosters = 'rosters'
players = 'players'
MLB_B = {}
MLB_P = {}

db = DB.connect()
cursor = db.cursor()

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'ABHOPfpaincdrtwuLT')
except getopt.GetoptError as err:
    print(str(err))
    usage()

for (opt, arg) in opts:
    if opt == '-B':
        do_pit = False
    elif opt == '-P':
        do_bat = False
    elif opt == '-H':
        do_header = False
    elif opt == '-O':
        rosters = 'rosters_old'
        players = 'players_old'
    elif opt == '-a':
        do_inactive = False
    elif opt == '-i':
        do_active = False
    elif opt == '-p':
        do_picks = True
        do_pit = False
        do_bat = False
    elif opt == '-A':
        cursor.execute("select distinct(ibl_team) from rosters \
                where ibl_team != 'FA';")
        args += [ row[0] for row in sorted(cursor.fetchall()) ]
    elif opt == '-c':
        do_card = True
    elif opt == '-d':
        do_def = True
    elif opt == '-r':
        do_br = True
    elif opt == '-t':
        do_val = do_tot
    elif opt == '-w':
        do_val = do_wOBA
    elif opt == '-u':
        do_usage = True
        mlb_usage( MLB_P, MLB_B )
    elif opt == '-L':
        eol = ''
    elif opt == '-n':
        count = True
    elif opt == '-f':
        do_find = True
    elif opt == '-T':
        is_tty = True
    else:
        print("bad option:", opt)
        usage()

if not do_bat and not do_pit and not do_picks:
    print("may only choose one of -B | -P")
    usage()
if not do_active and not do_inactive:
    print("may only choose one of -a | -i")
    usage()

# teams table
# status: 1 = active, 2 = inactive
# item_type: 0 = pick, 1 = pitcher, 2 = batter
if do_find:
    sqlbase = "select t.tig_name, rpad(ibl_team, 3, ' ') || ' - ' || \
            case when comments is not null then comments else '' end, \
            status, item_type, uncarded, bats, throws from %s t \
            left outer join %s p on (t.tig_name = p.tig_name) " \
            % ( rosters, players );
    sqlbase += "where t.tig_name ~* (%s) "
else:
    sqlbase = "select t.tig_name, comments, status, item_type, uncarded, \
            bats, throws from %s t \
            left outer join %s p on (t.tig_name = p.tig_name) " \
            % ( rosters, players );
    sqlbase += "where ibl_team = (%s) "
sqlbase += "and item_type %s (%s) = (%s) order by tig_name;" \
        % ( "|" if do_picks else "&", "%s", "%s" )

if do_card or do_def:
    b_cards = p_hash( cardpath() + '/' + batters )
    p_cards = p_hash( cardpath() + '/' + pitchers )
    b_def = p_hash( cardpath() + '/defense.txt' )
    b_run = p_hash( cardpath() + '/br.txt' )
    p_def = p_hash( cardpath() + '/pitrat.txt' )
    p_fat = p_hash( cardpath() + '/bfp.txt' )

if sys.stdout.isatty() or is_tty:
    maxR, maxC = subprocess.check_output(['stty', 'size']).split()
    maxC = int(maxC)
else:
    maxC = 256

# current UC designation
sql = "select max(uncarded) from %s;" % rosters
cursor.execute(sql)
( UCyy, ) = cursor.fetchone()

# skip UC in roster count?
ignore_uc = False

first = True
for arg in args:
    # skip line between multiple args
    if not first:
        print(eol)
    first = False

    b_num = 0
    p_num = 0
    active = 0
    b_act = 0
    p_act = 0
    uncarded = 0

    team = arg.upper()
    for item in 0, 1, 2:
        # do picks or players, not both
        if do_picks:
            if item > 0:
                continue
        else:
            if item == 0:
                continue

        cursor.execute(sqlbase, (team, item, item, ))
        # skip null query
        if cursor.rowcount == 0:
            continue

        # print header
        if do_find:
            header = ''
        else:
            header = team + ' '
        if item == 0 and do_picks and do_header:
            print(header + 'PICKS')
        elif item == 1 and do_pit and do_header:
            print(header + 'PITCHERS')
        elif item == 2 and do_bat and do_header:
            if p_num > 0:
                print()
            print(header + 'BATTERS')

        for tigname, how, status, kind, uc, bats, throws in cursor.fetchall():
            mlb, name = p_split( trim(tigname) )
            cols = 0
            if item == 0 and do_picks:
                print("%-15s %-40s" % ( trim(tigname), trim(how) ))
            if item & kind == 1 and do_pit:
                p_num += 1
                if uc == UCyy:
                    uncarded += 1
                    if ignore_uc:
                        p_num -= 1
                if status == 1:
                    active += 1
                    p_act += 1
                if status == 1 and do_active or status > 1 and do_inactive:
                    if (do_card or do_def) and uc == UCyy and ignore_uc:
                        continue
                    else:
                        print("%s %-3s %-15s" %
                                ( star(status, throws), mlb, name ), end=' ')
                        cols += 23
                    if do_card and (mlb, name) in p_cards:
                        if do_val:
                            for num in cardval(p_cards[(mlb,name)], item, do_val):
                                if num.isdigit():
                                    print("%3s" % num, end=' ')
                                    cols += 4
                                else:
                                    print("%s" % num, end=' ')
                                    cols += len(num) + 1
                        else:
                            for num in cardtop(p_cards[(mlb,name)], item):
                                if num.isdigit():
                                    print("%3s" % num, end=' ')
                                    cols += 4
                                else:
                                    print("%s" % num, end=' ')
                                    cols += len(num) + 1
                        if do_usage and mlb + " " + name in MLB_P:
                            print(". %3.0f" % MLB_P[mlb + " " + name], end=' ')
                            cols += 6
                        if (mlb, name) in p_def:
                            print(".", pitfat(p_fat[(mlb,name)]), end=' ')
                            cols += 19
                        if cols + 25 < maxC and (mlb, name) in p_def:
                            print(" %-24s" % ( pitrat(p_def[(mlb,name)]) ), end=' ')
                    elif not (do_card or do_def):
                        print(" %-20s" % ( trim(how) ), end=' ')
                        if uc > 0:
                            print(" [UC%s]" % uc, end=' ')
                    elif (cols + 24 < maxC or do_def) and (mlb, name) in p_def:
                        print("%-24s" % ( pitrat(p_def[(mlb,name)]) ), end=' ')
                        print(". ",pitfat(p_fat[(mlb,name)]), end=' ')
                    print()
            if item & kind == 2 and do_bat:
                b_num += 1
                if uc == UCyy:
                    uncarded += 1
                    if ignore_uc:
                        b_num -= 1
                if status == 1:
                    active += 1
                    b_act += 1
                if status == 1 and do_active or status > 1 and do_inactive:
                    if (do_card or do_def) and uc == UCyy and ignore_uc:
                        continue
                    else:
                        print("%s %-3s %-15s" %
                                ( star(status, bats), mlb, name ), end=' ')
                        cols += 23
                    if do_card and (mlb, name) in b_cards:
                        if do_val:
                            for num in cardval(b_cards[(mlb,name)], item, do_val):
                                if num.isdigit():
                                    print("%3s" % num, end=' ')
                                    cols += 4
                                else:
                                    print("%s" % num, end=' ')
                                    cols += len(num) + 1
                        else:
                            for num in cardtop(b_cards[(mlb,name)], item):
                                if num.isdigit():
                                    print("%3s" % num, end=' ')
                                    cols += 4
                                else:
                                    print("%s" % num, end=' ')
                                    cols += len(num) + 1
                        if do_usage and mlb + " " + name in MLB_B:
                            print(". %3.0f" % MLB_B[mlb + " " + name], end=' ')
                            cols += 6
                        if (mlb, name) in b_def:
                            if do_br:
                                print(".", end=' ')
                                print(brun( b_run[(mlb,name)] ), ".", end=' ')
                                cols += 11
                            else:
                                print(".", end=' ')
                                cols += 2
                            print(poslist( b_def[(mlb,name)][2:], maxC - cols ), end=' ')
                    elif not (do_card or do_def):
                        print(" %-20s" % ( trim(how) ), end=' ')
                        if uc > 0:
                            print(" [UC%s]" % uc, end=' ')
                    elif do_def and (mlb, name) in b_def:
                        if do_br:
                            print(brun( b_run[(mlb,name)] ), ".", end=' ')
                            cols += 11
                        print(poslist( b_def[(mlb,name)][2:], maxC - cols ), end=' ')
                    print()

    if count and b_num and p_num:
        print("%s: %2s players (%2s pitchers, %2s batters, %s uncarded)" % \
                (team, b_num + p_num, p_num, b_num, uncarded) + \
                " %2s active (%2s/%2s)" % \
                (active, p_act, b_act))

db.close()

