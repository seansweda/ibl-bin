#!/usr/bin/python
# $Id: ros.py,v 1.4 2011/07/03 21:37:49 sweda Exp sweda $

import os
import sys
import getopt

import psycopg2

from card import p_split, p_hash, cardpath, batters, pitchers

def usage():
    print "usage: %s " % sys.argv[0]
    sys.exit(1)

def trim(string):
    if string and len(string) > 0:
        return string.rstrip()
    else:
        return ''

def star(val):
    if val == 1: return '*'
    else: return ' '

def cardtop(p, type):
    # pitcher
    if type == 1:
        return ( p[23], p[24], p[25], '  ', '.', p[34], p[35], p[36], '  ' )
    # batter
    else:
        return ( p[20], p[21], p[22], p[23], '.', p[31], p[32], p[33], p[34] )

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

def main():
    do_bat = True
    do_pit = True
    do_picks = False
    do_active = True
    do_inactive = True
    do_card = False
    do_def = False
    b_cards = {}
    p_cards = {}
    b_def = {}
    count = False
    eol = ''

    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)
    cursor = db.cursor()

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'BPaipAcdLn')
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
            b_cards = p_hash( cardpath() + '/' + batters )
            p_cards = p_hash( cardpath() + '/' + pitchers )
        elif opt == '-d':
            do_def = True
            b_def = p_hash( cardpath() + '/defense.txt' )
        elif opt == '-L':
            eol = ''
        elif opt == '-n':
            count = True
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
    sqlbase = "select tig_name, comments, status, item_type from teams \
            where ibl_team = (%s) order by item_type, tig_name;"

    last = -1
    for arg in args:
        if last > 0:
            last = -1
            print eol
        bnum = 0
        pnum = 0
        team = arg.upper()
        cursor.execute(sqlbase, (team,))
        for tigname, how, status, type in cursor.fetchall():
            mlb, name = p_split( trim(tigname) )
            if type > last:
                if type == 0 and do_picks:
                    print team, "PICKS"
                elif type == 1 and do_bat and do_pit:
                    print team, "PITCHERS"
                elif type == 2 and do_bat and do_pit:
                    print "\n", team, "BATTERS"
                last = type
            if type == 0 and do_picks:
                print "%-3s %-15s %-40s" % ( mlb, name, trim(how) )
            if type == 1 and do_pit:
                pnum += 1
                if status == 1 and do_active or status > 1 and do_inactive:
                    print "%s %-3s %-15s" % ( star(status), mlb, name ),
                    if do_card and (mlb, name) in p_cards:
                        for num in cardtop(p_cards[(mlb,name)], type):
                            if num.isdigit():
                                print "%3s" % num,
                            else:
                                print "%s" % num,
                    elif not do_card:
                        print " %-40s" % ( trim(how) ),
                    print
            if type == 2 and do_bat:
                bnum += 1
                if status == 1 and do_active or status > 1 and do_inactive:
                    print "%s %-3s %-15s" % ( star(status), mlb, name ),
                    if do_card and (mlb, name) in b_cards:
                        for num in cardtop(b_cards[(mlb,name)], type):
                            if num.isdigit():
                                print "%3s" % num,
                            else:
                                print "%s" % num,
                        if do_def and (mlb, name) in b_def:
                            print ".", poslist( b_def[(mlb,name)][2:], 22 ),
                    elif not (do_card or do_def):
                        print " %-40s" % ( trim(how) ),
                    elif do_def and (mlb, name) in b_def:
                        print poslist( b_def[(mlb,name)][2:], 55 ),
                    print
        if count and bnum and pnum:
            print "%s players: %s (%s pitchers, %s batters" % \
                    (team, bnum + pnum, pnum, bnum)
    db.close()

if __name__ == "__main__":
    main()

