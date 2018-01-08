#!/usr/bin/python
#
# flags
# -c: card info
# -d: defensive ratings
# -r: baserunning
# -t: ob + tb totals
# -w: wOBA totals
# -a: active roster
# -i: inactive roster
# -n: number of players
# -p: picks
# -f: find player
# -B: batters only
# -P: batters only
# -A: all teams
# -O: old rosters
# -L: page breaks 

import os
import sys
import getopt
import subprocess

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

        mean = (sum_vL + sum_vR) / 2.0
        harm = 2 * sum_vL * sum_vR / float(sum_vL + sum_vR)
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

        harm = 2 * sum_vL * sum_vR / float(sum_vL + sum_vR)
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
do_picks = False
do_active = True
do_inactive = True
do_card = False
do_def = False
do_br = False
do_find = False
count = False
eol = ''
do_val = 0
do_tot = 1
do_wOBA = 2
rosters = 'rosters'
players = 'players'

db = DB.connect()
cursor = db.cursor()

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'ABOPfpaincdrtwL')
except getopt.GetoptError, err:
    print str(err)
    usage()

for (opt, arg) in opts:
    if opt == '-B':
        do_pit = False
    elif opt == '-P':
        do_bat = False
    elif opt == '-O':
        rosters = 'teams_old'
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
    elif opt == '-L':
        eol = ''
    elif opt == '-n':
        count = True
    elif opt == '-f':
        do_find = True
    else:
        print "bad option:", opt
        usage()

if not do_bat and not do_pit and not do_picks:
    print "may only choose one of -B | -P"
    usage()
if not do_active and not do_inactive:
    print "may only choose one of -a | -i"
    usage()

# teams table
# status: 1 = active, 2 = inactive, 3 = uncarded
# item_type: 0 = pick, 1 = pitcher, 2 = batter
if do_find:
    sqlbase = "select t.tig_name, rpad(ibl_team, 3, ' ') || ' - ' ||\
            case when comments is not null then comments else '' end,\
            status, item_type, bats, throws from %s t\
            left outer join %s p on (t.tig_name = p.tig_name) "\
            % ( rosters, players );
    sqlbase += "where t.tig_name ~* (%s) order by item_type, tig_name;"
else:
    sqlbase = "select t.tig_name, comments, status, item_type, bats, throws\
            from %s t left outer join %s p on (t.tig_name = p.tig_name) "\
            % ( rosters, players );
    sqlbase += "where ibl_team = (%s) order by item_type, tig_name;"

if do_card or do_def:
    b_cards = p_hash( cardpath() + '/' + batters )
    p_cards = p_hash( cardpath() + '/' + pitchers )
    b_def = p_hash( cardpath() + '/defense.txt' )
    b_run = p_hash( cardpath() + '/br.txt' )
    p_def = p_hash( cardpath() + '/pitrat.txt' )
    p_fat = p_hash( cardpath() + '/bfp.txt' )

maxR, maxC = subprocess.check_output(['stty', 'size']).split()
maxR = int(maxR)
maxC = int(maxC)

last = -1
for arg in args:
    if last > 0:
        last = -1
        print eol
    b_num = 0
    p_num = 0
    active = 0
    b_act = 0
    p_act = 0
    uncarded = 0

    team = arg.upper()
    cursor.execute(sqlbase, (team,))
    for tigname, how, status, kind, bats, throws in cursor.fetchall():
        mlb, name = p_split( trim(tigname) )
        cols = 0
        if kind > last:
            if do_find:
                header = ''
            else:
                header = team + " "
            if kind == 0 and do_picks:
                print header + 'PICKS'
            elif kind == 1 and do_bat and do_pit:
                print header + 'PITCHERS'
            elif kind == 2 and do_bat and do_pit:
                if p_num > 0:
                    print
                print header + 'BATTERS'
            last = kind
        if kind == 0 and do_picks:
            print "%-15s %-40s" % ( trim(tigname), trim(how) )
        if kind == 1 and do_pit:
            p_num += 1
            if status == 1:
                active += 1
                p_act += 1
            elif status == 3:
                uncarded += 1
            if status == 1 and do_active or status > 1 and do_inactive:
                print "%s %-3s %-15s" % ( star(status, throws), mlb, name ),
                cols += 23
                if do_card and (mlb, name) in p_cards:
                    if do_val:
                        for num in cardval(p_cards[(mlb,name)], kind, do_val):
                            if num.isdigit():
                                print "%3s" % num,
                                cols += 4
                            else:
                                print "%s" % num,
                                cols += len(num) + 1
                    else:
                        for num in cardtop(p_cards[(mlb,name)], kind):
                            if num.isdigit():
                                print "%3s" % num,
                                cols += 4
                            else:
                                print "%s" % num,
                                cols += len(num) + 1
                    if (mlb, name) in p_def:
                        print ".", pitfat(p_fat[(mlb,name)]),
                        cols += 19
                    if cols + 25 < maxC and (mlb, name) in p_def:
                        print " %-24s" % ( pitrat(p_def[(mlb,name)]) ),
                elif not (do_card or do_def):
                    print " %-40s" % ( trim(how) ),
                elif (cols + 24 < maxC or do_def) and (mlb, name) in p_def:
                    print "%-24s" % ( pitrat(p_def[(mlb,name)]) ),
                    print ". ",pitfat(p_fat[(mlb,name)]),
                print
        if kind == 2 and do_bat:
            b_num += 1
            if status == 1:
                active += 1
                b_act += 1
            elif status == 3:
                uncarded += 1
            if status == 1 and do_active or status > 1 and do_inactive:
                print "%s %-3s %-15s" % ( star(status, bats), mlb, name ),
                cols += 23
                if do_card and (mlb, name) in b_cards:
                    if do_val:
                        for num in cardval(b_cards[(mlb,name)], kind, do_val):
                            if num.isdigit():
                                print "%3s" % num,
                                cols += 4
                            else:
                                print "%s" % num,
                                cols += len(num) + 1
                    else:
                        for num in cardtop(b_cards[(mlb,name)], kind):
                            if num.isdigit():
                                print "%3s" % num,
                                cols += 4
                            else:
                                print "%s" % num,
                                cols += len(num) + 1
                    if (mlb, name) in b_def:
                        if do_br:
                            print ".",
                            print brun( b_run[(mlb,name)] ), ".",
                            cols += 11
                        else:
                            print ".",
                            cols += 2
                        print poslist( b_def[(mlb,name)][2:], maxC - cols ),
                elif not (do_card or do_def):
                    print " %-40s" % ( trim(how) ),
                elif do_def and (mlb, name) in b_def:
                    if do_br:
                        print brun( b_run[(mlb,name)] ), ".",
                        cols += 11
                    print poslist( b_def[(mlb,name)][2:], maxC - cols ),
                print
    if count and b_num and p_num:
        print "%s: %2s players (%2s pitchers, %2s batters, %s uncarded)" % \
                (team, b_num + p_num, p_num, b_num, uncarded) + \
                " %2s active (%2s/%2s)" % \
                (active, p_act, b_act)

db.close()

