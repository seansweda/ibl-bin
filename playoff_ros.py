#!/usr/bin/env python
#
# -t <team>: select team
# -O: old rosters

import os
import csv
import sys
import psycopg2
import getopt
from io import open

import DB

from man import help
from card import cardpath

MLB_B = {}
MLB_P = {}

sp = 0
rp = 1
vLH = 0
vRH = 1

def usage():
    print("usage: %s [flags]" % sys.argv[0])
    help( __file__ )
    sys.exit(1)

# dump environment and parameters for testing
# not really necessary, mostly for learning purposes
def dumpenv(form):
    for (env, val) in list(os.environ.items()):
        print("<br>", env + " : ", val)
    print("<p>parameters")
    for param in list(form.keys()):
        print("<br>", param + " : ", end=' ')
        for val in form.getlist(param):
            print(val, end=' ')
        print()
    print("<p>")
    return

def mlb_usage( pit_U, bat_U ):
    mlb_file = cardpath() + '/pa-pit.csv'
    try:
        with open( mlb_file, 'r', newline=None ) as s:
            for line in csv.reader(s):
                pit_U[ line[0] ] = [ int(line[1].split()[0]), int(line[1].split()[2]) ]
    except PermissionError:
        print("Permission denied")
        sys.exit(1)
    except OSError as err:
        print(str(err))
        sys.exit(1)

    mlb_file = cardpath() + '/pa-bat.csv'
    try:
        with open( mlb_file, 'r', newline=None ) as s:
            for line in csv.reader(s):
                bat_U[ line[0] ] = [ int(line[1].split()[0]), int(line[1].split()[2]) ]
    except PermissionError:
        print("Permission denied")
        sys.exit(1)
    except OSError as err:
        print(str(err))
        sys.exit(1)


def main():
    do_json = False
    is_cgi = False
    if 'GATEWAY_INTERFACE' in os.environ:
        import cgi
        #import cgitb; cgitb.enable()
        form = cgi.FieldStorage()
        is_cgi = True
        if 'json' in form:
            import json
            do_json = True
            print("Content-Type: application/json")
            print()
        else:
            do_json = False
            print("Content-Type: text/html")
            print()
            print("<html><head><title>Playoff Eligibility</title></head><body>")
            #dumpenv(form)

    team = ''
    rosters = 'rosters'

    if is_cgi:
        if 'team' in form:
            team = form.getfirst('team').upper()
    else:
        for (opt, arg) in opts:
            if opt == '--help':
                usage()
            if opt == '-t':
                team = arg.upper()
            elif opt == '-O':
                rosters = 'rosters_old'

    db = DB.connect()
    cursor = db.cursor()

    mlb_usage( MLB_P, MLB_B )

    sql = "select trim(r.tig_name), retro_id, c, b1, b2, b3, ss, lf, cf, rf from %s r, (select concat(trim(mlb), ' ', trim(name)) as tig_name, c, \"1b\" as b1, \"2b\" as b2, \"3b\" as b3, ss, lf, cf, rf from %s where week is null) as s where trim(r.tig_name) = trim(s.tig_name) and ibl_team = '%s' order by item_type, r.tig_name;" % ( rosters, DB.starts, team )

    if not team:
        usage()

    cursor.execute(sql)
    for line in cursor.fetchall():
        #print( line )
        ( tigname, retroid, c, b1, b2, b3, ss, lf, cf, rf ) = line
        print( "%-3s %-16s" \
                % ( tigname.split()[0], tigname.split()[1] ), end=' ')
        if retroid in MLB_P:
            #print( MLB_P[ retroid ] )
            if MLB_P[retroid][sp] + MLB_P[retroid][rp] < 100:
                print( "ineligible" )
                continue
            if  MLB_P[retroid][sp] >= 150:
                print( "SP", end=' ' )
            else:
                print( "--", end=' ' )
            if  MLB_P[retroid][sp] + MLB_P[retroid][rp] >= 150:
                print( "RP", end=' ' )
            elif  MLB_P[retroid][sp] + MLB_P[retroid][rp] >= 100:
                print( "6I", end=' ' )
            else:
                print( "--", end=' ' )
        if retroid in MLB_B:
            #print( MLB_B[ retroid ] )
            if MLB_B[retroid][vLH] + MLB_B[retroid][vRH] < 100:
                print( "ineligible" )
                continue
            if retroid not in MLB_P:
                print( "-- --", end=' ' )
            if MLB_B[retroid][vLH] + MLB_B[retroid][vRH] >= 150:
                print( "DH", end=' ' )
            elif MLB_B[retroid][vLH] + MLB_B[retroid][vRH] >= 100:
                print( "6I", end=' ' )
            else:
                print( "--", end=' ' )
            if MLB_B[retroid][vLH] >= 50:
                print( "vL", end=' ' )
            else:
                print( "--", end=' ' )
            if MLB_B[retroid][vRH] >= 50:
                print( "vR", end=' ' )
            else:
                print( "--", end=' ' )
            for pos in [c,"c"], [b1,"1b"], [b2,"2b"], [b3,"3b"], [ss,"ss"], [lf,"lf"], [cf,"cf"], [rf,"rf"]:
                if pos[0] >= 48:
                    print( "%-2s" % pos[1].upper(), end=' ' )
                elif pos[0] > 0:
                    print( "%-2s" % pos[1].lower(), end=' ' )
                else:
                    print( "--", end=' ' )
        else:
            print( "-- -- -- -- -- -- -- -- -- -- --", end=' ' )
        print()

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:O', ["help"])
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    main()

