#!/usr/bin/python

import os
import sys
import getopt
import time
import yaml
import psycopg2

import DB

def usage():
    print "usage: %s " % sys.argv[0]
    sys.exit(1)

db = DB.connect()
cursor = db.cursor()

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'st:r:y:')
except getopt.GetoptError, err:
    print str(err)
    usage()

try:
    f = open( DB.bin_dir() + '/data/tiers.yml', 'rU')
except IOError, err:
    print str(err)
    sys.exit(1)

y = yaml.safe_load(f)

if y.has_key('year'):
    year = str( y['year'] )
else:
    # default is year + 1
    year = int(time.strftime("%Y"))
    year = "%s" % ( int(year) + 1 )

skip = 0
all_teams = 1
all_rounds = 1

for (opt, arg) in opts:
    if opt == '-y':
        year = arg
    elif opt == '-s':
        skip = 1
    elif opt == '-t':
        all_teams = 0
        do_team = arg.upper()
    elif opt == '-r':
        all_rounds = 0
        do_round = int(arg)

sqlbase = "select ibl_team from teams where item_type=0 and tig_name = (%s);"

order1 = y['tier0'] + y['tier1'] + y['tier2'] + y['tier3']
y['tier0'].reverse()
y['tier1'].reverse()
y['tier2'].reverse()
y['tier3'].reverse()
order2 = y['tier0'] + y['tier1'] + y['tier2'] + y['tier3']

roster = {}

cursor.execute( "select ibl_team, count(*) from teams where item_type > 0 group by ibl_team;" )
for ibl, count in cursor.fetchall():
    roster[ibl] = count

for rnd in xrange(1,16):
    pick = 1
    for slot in xrange(1,25):
        original = order1[ slot - 1 ] if rnd % 2 == 1 else order2[ slot - 1 ]
        pickstr = original + '#' + str(rnd)
        cursor.execute(sqlbase, (pickstr + ' (%s)' % year[-2:],))
        owner = cursor.fetchone()
        if owner and ( not skip or roster[owner[0]] < 35 ):
            if ( all_teams or do_team == owner[0] ) and ( all_rounds or do_round == rnd ):
                print "%s%-5s  %3s  (%s)" % (
                    ' ' if roster[owner[0]] < 35 else '*',
                    str(rnd) + '-' + ( str(pick) if skip else str(slot) ),
                    owner[0], pickstr
                    )
            roster[owner[0]] += 1
            pick += 1
    if ( all_teams and all_rounds):
        print

exit

