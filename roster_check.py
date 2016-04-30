#!/usr/bin/python

import os
import sys
import psycopg2
import yaml

import DB
import injreport
import startsdb

# dump environment and parameters for testing
# not really necessary, mostly for learning purposes
def dumpenv(form):
    for (env, val) in os.environ.items():
        print "<br>", env + " : ", val
    print "<p>parameters"
    for param in form.keys():
        print "<br>", param + " : ",
        for val in form.getlist(param):
            print val,
        print
    print "<p>"
    return

def main():
    do_json = False
    is_cgi = False
    if 'GATEWAY_INTERFACE' in os.environ:
        import cgi
        #import cgitb; cgitb.enable()
        form = cgi.FieldStorage()
        is_cgi = True
        if form.has_key('json'):
            import json
            do_json = True
            print "Content-Type: application/json"
            print
        else:
            do_json = False
            print "Content-Type: text/html"
            print
            print "<html><head><title>Free Agent signing order</title></head><body>"
            #dumpenv(form)

    db = DB.connect()
    cursor = db.cursor()

    week = 0
    if len(sys.argv) > 1:
        week = int(sys.argv[1])
    elif is_cgi and form.has_key('week'):
        week = int(form.getfirst('week'))
    else:
        # no user input so we'll find latest week with reported results
        cursor.execute("select week, count(*) from games\
                group by week order by week desc limit 1;");
        (week, num) = cursor.fetchone()
        # and use first week afterward
        week += 1

    starts = {}
    startsdb.main( starts, module=True )

    inj = {}
    injreport.main( inj, module=True )

    # teams/status
    active = 1
    inactive = 2
    uncarded = 3

    def ok( week ):
        for series in week.keys():
            out = map( lambda z: z & ( 2 + 8 ),  week[series] )
            if not filter( lambda y: y == 0, out ):
                return False
        return True

    sql_count = "select status, count(*) from teams \
            where ibl_team = (%s) and item_type != 0 \
            group by status;"
    sql_ros = "select trim(tig_name) from teams \
            where ibl_team = (%s) and item_type != 0 and status = 1;"

    if is_cgi:
        print "<pre>"
    print "WEEK %-2s                            # 1 2 3 4 5 6 7 8 9" % week

    cursor.execute("select distinct(ibl_team) from teams \
                            where ibl_team != 'FA' order by ibl_team;")
    for (ibl, ) in cursor.fetchall():
        ros = {}
        cursor.execute( sql_count, (ibl, ) )
        for status, count in cursor.fetchall():
            ros[status] = count

        legal = [] 
        for pos in range(10):
            legal.append(0)

        cursor.execute( sql_ros, (ibl, ) )
        for player, in cursor.fetchall():
            #print player, starts[player]

            # check if player has appearances left
            if starts[player][0] <= 0:
                continue

            # check if player is out for a series
            if inj.has_key(player):
                if inj[player].has_key(week):
                    if not ok( inj[player][week] ):
                        #print "inj: %s" % player
                        continue

            for pos in range(10):
                if starts[player][pos] > 0:
                    legal[pos] += 1

        print ibl,
        print "total %s," % sum(ros.values()),
        print "active %s," % ros[active],

        print "starts (",
        for pos in range(10):
            print legal[pos],
        print ")",

        if sum(ros.values()) == 35 \
                and ( ros[active] <= 25 or ros[active] <= 35 and week >= 24 ) \
                and legal[1] >= 4 \
                and len( filter( lambda z: z >= 2, legal[2:] ) ) == 8:
            print "LEGAL"
        else:
            print "ILLEGAL"

    if is_cgi:
        print "</pre></body></html>"

if __name__ == "__main__":
    main()
