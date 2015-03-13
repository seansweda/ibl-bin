#!/usr/bin/python

import os
import csv
import sys
import psycopg2

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

    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)
    cursor = db.cursor()

    player = {}
    cursor.execute("select * from inj2015 order by week, tig_name");
    for injury in cursor.fetchall():
        week, home, away, day, code, ibl, name, length, dtd, desc = injury

        if not player.has_key(name):
            player[name] = {}

        print injury
        print
        served = 3 - day + 1
        print "served: %i" % served
        length -= served

        if ibl == home:
            last = 'home'
        else:
            last = 'away'
        while length > 0:
                week += 1
                served = min( 3, length )
                print "week %i %s: %i (%i)" % (week, last, served, length)
                length -= served
                if last == 'home':
                    last = 'away'
                else:
                    last = 'home'
                served = min( 3, length )
                print "week %i %s: %i (%i)" % (week, last, served, length)
                length -= served


if __name__ == "__main__":
    main()

