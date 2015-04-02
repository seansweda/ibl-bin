#!/usr/bin/python
#
# flags
# -c: card info
# -d: defensive ratings
# -a: active roster
# -i: inactive roster
# -n: number of players
# -p: picks
# -f: find player
# -B: batters only
# -P: batters only
# -A: all teams
# -L: page breaks 

import os
import sys
import getopt

import psycopg2

sys.path.append('/home/ibl/bin')
import DB

from card import p_split, p_hash, cardpath, batters, pitchers

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
        if val == 1: return '*'
        else : return ' '

def cardtop(p, type):
    # pitcher
    if type == 1:
        return ( p[24], p[25], p[26], p[23], '.', p[36], p[37], p[38], p[35] )
    # batter
    else:
        return ( p[21], p[22], p[23], p[24], '.', p[33], p[34], p[35], p[36] )

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

def pitrat(p):
    defense = "%s/%s  %s/%s  %s" % \
            ( p[2].replace('/0', '/ 0'), p[3], p[6], p[7], p[8] )
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
do_find = False
count = False
eol = ''

# teams table
# status: 1 = active, 2 = inactive, 3 = uncarded
# item_type: 0 = pick, 1 = pitcher, 2 = batter
sqlbase = "select t.tig_name, comments, status, item_type, bats, throws\
        from teams t left outer join players p on (t.tig_name = p.tig_name)\
        where ibl_team = (%s) order by item_type, tig_name;"

db = DB.connect()
cursor = db.cursor()

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'BPaipAcdLnf')
except getopt.GetoptError, err:
    print str(err)
    usage()

for (opt, arg) in opts:
    if opt == '-B':
        do_pit = False
    elif opt == '-P':
        do_bat = False
    elif opt == '-a':
        do_inactive = False
    elif opt == '-i':
        do_active = False
    elif opt == '-p':
        do_picks = True
        do_pit = False
        do_bat = False
    elif opt == '-A':
        cursor.execute("select distinct(ibl_team) from teams \
                where ibl_team != 'FA';")
        args += [ row[0] for row in sorted(cursor.fetchall()) ]
    elif opt == '-c':
        do_card = True
    elif opt == '-d':
        do_def = True
    elif opt == '-L':
        eol = ''
    elif opt == '-n':
        count = True
    elif opt == '-f':
        do_find = True
        sqlbase = "select t.tig_name, rpad(ibl_team, 3, ' ') || ' - ' ||\
                case when comments is not null then comments else '' end,\
                status, item_type, bats, throws from teams t\
                left outer join players p on (t.tig_name = p.tig_name)\
                where t.tig_name ~* (%s) order by item_type, tig_name;"
    else:
        print "bad option:", opt
        usage()

if not do_bat and not do_pit and not do_picks:
    print "may only choose one of -B | -P"
    usage()
if not do_active and not do_inactive:
    print "may only choose one of -a | -i"
    usage()

if do_card or do_def:
    b_cards = p_hash( cardpath() + '/' + batters )
    p_cards = p_hash( cardpath() + '/' + pitchers )
    b_def = p_hash( cardpath() + '/defense.txt' )
    p_def = p_hash( cardpath() + '/pitrat.txt' )
    p_fat = p_hash( cardpath() + '/bfp.txt' )

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
    for tigname, how, status, type, bats, throws in cursor.fetchall():
        mlb, name = p_split( trim(tigname) )
        if type > last:
            if do_find:
                header = ''
            else:
                header = team + " "
            if type == 0 and do_picks:
                print header + 'PICKS'
            elif type == 1 and do_bat and do_pit:
                print header + 'PITCHERS'
            elif type == 2 and do_bat and do_pit:
                if p_num > 0:
                    print
                print header + 'BATTERS'
            last = type
        if type == 0 and do_picks:
            print "%-15s %-40s" % ( trim(tigname), trim(how) )
        if type == 1 and do_pit:
            p_num += 1
            if status == 1:
                active += 1
                p_act += 1
            elif status == 3:
                uncarded += 1
            if status == 1 and do_active or status > 1 and do_inactive:
                print "%s %-3s %-15s" % ( star(status, throws), mlb, name ),
                if do_card and (mlb, name) in p_cards:
                    for num in cardtop(p_cards[(mlb,name)], type):
                        if num.isdigit():
                            print "%3s" % num,
                        else:
                            print "%s" % num,
                    if (mlb, name) in p_def:
                        print ".", pitfat(p_fat[(mlb,name)]),
                elif not (do_card or do_def):
                    print " %-40s" % ( trim(how) ),
                elif do_def and (mlb, name) in p_def:
                    print "%-24s" % ( pitrat(p_def[(mlb,name)]) ),
                    print ". ",pitfat(p_fat[(mlb,name)]),
                print
        if type == 2 and do_bat:
            b_num += 1
            if status == 1:
                active += 1
                b_act += 1
            elif status == 3:
                uncarded += 1
            if status == 1 and do_active or status > 1 and do_inactive:
                print "%s %-3s %-15s" % ( star(status, bats), mlb, name ),
                if do_card and (mlb, name) in b_cards:
                    for num in cardtop(b_cards[(mlb,name)], type):
                        if num.isdigit():
                            print "%3s" % num,
                        else:
                            print "%s" % num,
                    if (mlb, name) in b_def:
                        print ".", poslist( b_def[(mlb,name)][2:], 24 ),
                elif not (do_card or do_def):
                    print " %-40s" % ( trim(how) ),
                elif do_def and (mlb, name) in b_def:
                    print poslist( b_def[(mlb,name)][2:], 56 ),
                print
    if count and b_num and p_num:
        print "%s: %2s players (%2s pitchers, %2s batters, %s uncarded)" % \
                (team, b_num + p_num, p_num, b_num, uncarded) + \
                " %2s active (%2s/%2s)" % \
                (active, p_act, b_act)

db.close()

