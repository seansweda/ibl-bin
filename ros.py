#!/usr/bin/python
# $Id: card.py,v 1.1 2011/07/03 03:43:49 sweda Exp sweda $

import os
import sys
import getopt

import psycopg2

from card import p_hash, cardpath, batters, pitchers

def usage():
    print "usage: %s " % sys.argv[0]
    sys.exit(1)

def main():
    dobat = 1
    dopit = 1
    b_cards = {}
    p_cards = {}

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], 'BPAc')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)

    cursor = db.cursor()

    for (opt, arg) in opts:
        if opt == '-B':
            dopit = 0
        elif opt == '-P':
            dobat = 0
        elif opt == '-c':
            b_cards = p_hash( cardpath() + '/' + batters )
            p_cards = p_hash( cardpath() + '/' + pitchers )
        elif opt == '-A':
            cursor.execute("select distinct(ibl_team) from teams \
                    where ibl_team != 'FA';")
            args += [ row[0] for row in sorted(cursor.fetchall()) ]
        else:
            print "bad option:", opt
            usage()

    sqlbase = "select tig_name, comments, status, item_type from teams \
            where ibl_team = (%s) and item_type >= (%s) and status >= (%s) \
            order by item_type, tig_name;"

    for arg in args:
        team = arg.upper()
        cursor.execute(sqlbase, ( team, 1, 1 ))
        for tigname, how, status, type in cursor.fetchall():
            print "%-20s %-40s" % ( tigname.rstrip(), how.rstrip() )

if __name__ == "__main__":
    main()

