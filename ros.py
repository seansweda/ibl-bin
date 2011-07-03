#!/usr/bin/python
# $Id: ros.py,v 1.1 2011/07/03 09:14:59 sweda Exp sweda $

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
        return ( p[23], p[24], p[25], '', '.', p[34], p[35], p[36], '' )
    # batter
    else:
        return ( p[20], p[21], p[22], p[23], '.', p[31], p[32], p[33], p[34] )

def main():
    do_bat = True
    do_pit = True
    do_picks = False
    do_active = True
    do_inactive = True
    do_card = False
    b_cards = {}
    p_cards = {}
    eol = ''

    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)
    cursor = db.cursor()

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'BPaipAcL')
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
        elif opt == '-L':
            eol = ''
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
                if status == 1 and do_active or status > 1 and do_inactive:
                    print "%s %-3s %-15s" % ( star(status), mlb, name ),
                    if do_card:
                        for num in cardtop(p_cards[(mlb,name)], type):
                            print "%3s" % num,
                        print
                    else:
                        print " %-40s" % ( trim(how) )
            if type == 2 and do_bat:
                if status == 1 and do_active or status > 1 and do_inactive:
                    print "%s %-3s %-15s" % ( star(status), mlb, name ),
                    if do_card:
                        for num in cardtop(b_cards[(mlb,name)], type):
                            print "%3s" % num,
                        print
                    else:
                        print " %-40s" % ( trim(how) )

if __name__ == "__main__":
    main()

