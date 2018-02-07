#!/usr/bin/python
# flags
# -y: year
# -r: round
# -L: last round
# -t: team
# -s: skip unusable picks
# -S: skip & remove unusable picks

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
    (opts, args) = getopt.getopt(sys.argv[1:], 'L:sSt:r:y:')
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
remove = 0
all_teams = 1
all_rounds = 1
last_round = 10
do_round = 1

for (opt, arg) in opts:
    if opt == '-y':
        year = arg
    elif opt == '-s':
        skip = 1
    elif opt == '-S':
        skip = 1
        remove = 1
    elif opt == '-t':
        all_teams = 0
        do_team = arg.upper()
    elif opt == '-L':
        last_round = int(arg)
    elif opt == '-r':
        all_rounds = 0
        do_round = int(arg)

if not all_rounds:
    last_round = do_round

sqlbase = "select ibl_team from rosters where item_type=0 and tig_name = (%s);"

order1 = y['tier0'] + y['tier1'] + y['tier2'] + y['tier3']
y['tier0'].reverse()
y['tier1'].reverse()
y['tier2'].reverse()
y['tier3'].reverse()
order2 = y['tier0'] + y['tier1'] + y['tier2'] + y['tier3']

roster = {}
picks = {}

cursor.execute( "select ibl_team, count(*) from rosters where item_type > 0 group by ibl_team;" )
for ibl, count in cursor.fetchall():
    roster[ibl] = count

cursor.execute( "select ibl_team, trim(tig_name) from rosters where item_type = 0 and trim(tig_name) ~ '.(%s).$'" % year[-2:] )
for ibl, pk in cursor.fetchall():
    picks[ pk.split()[0] ] = ibl

for rnd in xrange( 1, last_round + 1 ):
    pick = 1
    for slot in xrange(1,25):
        original = order1[ slot - 1 ] if rnd % 2 == 1 else order2[ slot - 1 ]
        pickstr = original + '#' + str(rnd)
        if picks.has_key( pickstr ):
            owner = picks[ pickstr ]
        else:
            if not remove:
                pick += 1
            continue
        if not skip or roster[owner] < 35:
            if ( all_teams or do_team == owner ) and ( all_rounds or do_round == rnd ):
                print "%s%-5s  %3s  (%s)" % (
                    ' ' if roster[owner] < 35 else '*',
                    str(rnd) + '-' + ( str(pick) if skip else str(slot) ),
                    owner, pickstr
                    )
            roster[owner] += 1
            pick += 1
            continue
        if skip and not remove:
            pick += 1

    if ( all_teams and all_rounds):
        print

if skip:
    for team in sorted(roster):
        if roster[team] < 35:
            print "\t%s: %i" % (team, 35 - roster[team])

