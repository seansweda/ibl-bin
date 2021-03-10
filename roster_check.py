#!/usr/bin/python

from __future__ import (print_function, unicode_literals)

import os
import sys
import psycopg2
import yaml

import DB
import injreport as IR
import startsdb

maxR = 35   # max players on roster
maxA = 25   # max active players
allA = 24   # first week where all players can be active

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

def main():
    do_json = False
    do_header = True
    is_cgi = False

    if 'GATEWAY_INTERFACE' in os.environ:
        import cgi
        #import cgitb; cgitb.enable()
        form = cgi.FieldStorage()
        is_cgi = True
        if 'noheader' in form:
            do_header = False
        if 'json' in form:
            import json
            do_json = True
            print("Content-Type: application/json")
            print()
        else:
            do_json = False
            print("Content-Type: text/html")
            print()
            if do_header:
                print("<html><head><title>Legal Roster check</title></head><body>")
            #dumpenv(form)

    db = DB.connect()
    cursor = db.cursor()

    week = 1
    if len(sys.argv) > 1:
        week = int(sys.argv[1])
    elif is_cgi and 'week' in form:
        week = int(form.getfirst('week'))
    else:
        # no user input so we'll find latest week with reported results
        cursor.execute("select week, count(*) from games\
                group by week order by week desc limit 1;");
        if cursor.rowcount > 0:
            (week, num) = cursor.fetchone()
            # and use first week afterward
            week += 1

    # current UC designation
    sql = "select max(uncarded) from rosters;"
    cursor.execute(sql)
    ( UCyy, ) = cursor.fetchone()

    # skip UC in roster count?
    ignore_uc = True

    starts = {}
    startsdb.main( starts, module=True )

    inj = {}
    IR.main( inj, module=True )

    # teams/status
    active = 1
    inactive = 2

    # item type
    pitcher = 1
    batter = 2

    def ok( week ):
        for series in list(week.keys()):
            out = [z & (IR.off + IR.inj + IR.sus) for z in week[series]]
            if not [y for y in out if y == 0]:
                return False
        return True

    sql_count = "select status, count(*) from rosters \
            where ibl_team = (%s) and item_type != 0 and uncarded < (%s) \
            group by status;"
    sql_ros = "select trim(tig_name), item_type from rosters \
            where ibl_team = (%s) and item_type != 0 and status = 1 \
            and uncarded < (%s);"

    if not do_json:
        if is_cgi:
            print("<pre>")
        print("WEEK %-2s                pit/bat           #  1  2  3  4  5  6  7  8  9" % week)

    cursor.execute("select distinct(ibl_team) from rosters \
                            where ibl_team != 'FA' order by ibl_team;")
    for (ibl, ) in cursor.fetchall():
        ros = {}
        if ignore_uc:
            cursor.execute( sql_count, (ibl, UCyy ) )
        else:
            cursor.execute( sql_count, (ibl, UCyy + 1 ) )
        for status, count in cursor.fetchall():
            ros[status] = count

        legal = [] 
        for pos in range(10):
            legal.append(0)

        batters = 0
        pitchers = 0
        cursor.execute( sql_ros, (ibl, UCyy ) )
        for player, kind in cursor.fetchall():
            #print player, starts[player]
            if kind == pitcher:
                pitchers += 1
            if kind == batter:
                batters += 1

            # check if player has appearances left
            try:
                if starts[player][0] <= 0:
                    continue
            except KeyError:
                continue

            # check if player is out for a series
            if player in inj:
                if week in inj[player]:
                    if not ok( inj[player][week] ):
                        #print "inj: %s" % player
                        continue

            for pos in range(10):
                try:
                    if starts[player][pos] > 0:
                        legal[pos] += 1
                except KeyError:
                    pass

        if sum(ros.values()) <= maxR \
                and ( ros[active] <= maxA or \
                    ros[active] <= maxR and week >= allA ) \
                and legal[1] >= 4 \
                and len( [z for z in legal[2:] if z >= 2] ) == 8:
            status = "LEGAL"
        else:
            status = "ILLEGAL"

        if do_json:
            print(json.dumps({
                'ibl': ibl,
                'total': sum(ros.values()),
                'active': ros[active],
                'starts': legal,
                'status': status
                }))
        else:
            print(ibl, end=' ')
            print("total %s" % sum(ros.values()), end=' ')
            print("active %s" % ros[active], end=' ')
            print("(%2d/%2d)" % ( pitchers, batters ), end=' ')

            print("starts (", end=' ')
            for pos in range(10):
                print("%2s" % legal[pos], end=' ')
            print(")", end=' ')
            print(status)

    if not do_json:
        if is_cgi:
            print("</pre>")
            if do_header:
                print("</body></html>")

if __name__ == "__main__":
    main()

