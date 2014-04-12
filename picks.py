#!/usr/bin/python

import os
import sys
import getopt

import psycopg2

def usage():
    print "usage: %s " % sys.argv[0]
    sys.exit(1)

try:
    db = psycopg2.connect("dbname=ibl_stats user=ibl")
except psycopg2.DatabaseError, err:
    print str(err)
    sys.exit(1)
cursor = db.cursor()

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'BPaipAcdLnf')
except getopt.GetoptError, err:
    print str(err)
    usage()

sqlbase = "select ibl_team from teams where item_type=0 and tig_name = (%s);"

tier0 = [ 'TRI', 'NJR', 'CSG', 'BAL', 'WMS' ]
tier1 = [ 'GTY', 'CAN', 'ODM', 'HAV', 'KAT', 'MOR', 'MNM', 'MAD', 'SFP', 'PAD', 'POR' ]
tier2 = [ 'NYK', 'SKY', 'SDQ', 'MCM', 'SEA' ]
tier3 = [ 'BOW', 'PHI', 'COU' ]

order1 = tier0 + tier1 + tier2 + tier3
tier0.reverse()
tier1.reverse()
tier2.reverse()
tier3.reverse()
order2 = tier0 + tier1 + tier2 + tier3

for rnd in xrange(1,16):
    for pick in xrange(1,25):
        original = order1[ pick - 1 ] if rnd % 2 == 1 else order2[ pick - 1 ] 
        pickstr = original + '#' + str(rnd)
        cursor.execute(sqlbase, (pickstr + ' (14)',))
        owner = cursor.fetchone()
        if owner:
            print "%-5s  %3s  (%s)" % ( str(rnd) + '-' + str(pick), 
                    owner[0], pickstr )
    print

exit

