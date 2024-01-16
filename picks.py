#!/usr/bin/env python
#
# -t <team>: select team
# -r <round>: select round
# -L <round>: last round
# -y <year>: override season
# -s: skip unusable picks
# -S: skip & remove unusable picks

import os
import sys
import getopt
import time
import yaml
import psycopg2
from io import open

import DB

from man import help

def usage():
    print("usage: %s [flags]" % sys.argv[0])
    help( __file__ )
    sys.exit(1)

db = DB.connect()
cursor = db.cursor()

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'L:sSt:r:y:', ["help"])
except getopt.GetoptError as err:
    print(str(err))
    usage()

try:
    with open( DB.bin_dir() + '/data/tiers.yml', 'r', newline=None ) as f:
        y = yaml.safe_load(f)

        if 'year' in y:
            year = str( y['year'] )
        else:
            # default is year + 1
            year = int(time.strftime("%Y"))
            year = "%s" % ( int(year) + 1 )

except PermissionError:
    print("Permission denied")
    sys.exit(1)
except OSError as err:
    print(str(err))
    sys.exit(1)

ros_max = 36    # max players on roster
skip = 0
remove = 0
all_teams = 1
all_rounds = 1
last_round = 10
do_round = 0

for (opt, arg) in opts:
    if opt == '--help':
        usage()
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

# current UC designation
sql = "select max(uncarded) from rosters;"
cursor.execute(sql)
( UCyy, ) = cursor.fetchone()

# skip UC in roster count?
ignore_uc = False

sql_count = "select ibl_team, count(*) from rosters where item_type > 0 and uncarded < (%s) group by ibl_team;"
if ignore_uc:
    cursor.execute( sql_count, ( UCyy, ) )
else:
    cursor.execute( sql_count, ( UCyy + 1, ) )
for ibl, count in cursor.fetchall():
    roster[ibl] = count

cursor.execute( "select ibl_team, trim(tig_name) from rosters where item_type = 0 and trim(tig_name) ~ '.(%s).$'" % year[-2:] )
for ibl, pk in cursor.fetchall():
    picks[ pk.split()[0] ] = ibl

for rnd in range( 1, last_round + 1 ):
    pick = 1
    for slot in range(1,25):
        original = order1[ slot - 1 ] if rnd % 2 == 1 else order2[ slot - 1 ]
        pickstr = original + '#' + str(rnd)
        if pickstr in picks:
            owner = picks[ pickstr ]
        else:
            if not remove:
                pick += 1
            continue
        if not skip or roster[owner] < ros_max:
            if ( all_teams or do_team == owner ) and ( all_rounds or do_round == rnd ):
                print("%s%-5s  %3s  (%s)" % (
                    ' ' if roster[owner] < ros_max else '*',
                    str(rnd) + '-' + ( str(pick) if skip else str(slot) ),
                    owner, pickstr
                    ))
            roster[owner] += 1
            pick += 1
            continue
        if skip and not remove:
            pick += 1

    if ( all_teams and all_rounds):
        print()

if skip and not do_round:
    for team in sorted(roster):
        if roster[team] < ros_max:
            print("\t%s: %i" % (team, ros_max - roster[team]))

