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
    if 'GATEWAY_INTERFACE' in os.environ:
        import cgi
        import cgitb; cgitb.enable()
        form = cgi.FieldStorage()
        print "Content-Type: text/html"     # HTML is following
        print                               # blank line, end of headers
        print "<html><head><title>Free Agent signing order</title></head><body>"
        #dumpenv(form)
        is_cgi = True

    else:
        is_cgi = False

    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)
    cursor = db.cursor()

    def late(team):
        # results must be current
        if status[team][1] != week:
            return 1
        # boxes can be 1 week behind
        if status[team][0] < week - 1:
            return 1
        # otherwise return 0, team has nothing outstanding
        return 0

    if len(sys.argv) > 1:
        week = int(sys.argv[1])
    elif is_cgi and form.has_key('week'):
        week = int(form.getfirst('week'))
    else:
        cursor.execute( "select max(week) from games;" )
        week = int(cursor.fetchall()[0][0])

    # start with last year
    # lastyear.csv should be ordered to break ties
    fa = []
    lastyear = {}
    with open( '/home/ibl/bin/lastyear.csv', 'rU' ) as s:
        for line in csv.reader(s):
            fa.append( line[0] )
            lastyear[line[0]] = float(line[1])/(float(line[1])+float(line[2]))
    #print fa
    #print lastyear

    # initial sort by last year's standings
    fa.sort( key=lambda v: lastyear[v] )
    #print fa

    # we begin using current season standings as of week 3
    standings = {}
    if week >= 3:
        for w in range(2, week):
            cursor.execute( "select nickname,\
                    sum(case when home_team_id = f.id and\
                    home_score > away_score then 1\
                    when away_team_id = f.id and\
                    away_score > home_score then 1 else 0 end) as w,\
                    sum(case when home_team_id = f.id and\
                    home_score < away_score then 1\
                    when away_team_id = f.id and\
                    away_score < home_score then 1 else 0 end) as l\
                    from games g, franchises f where week <= (%s)\
                    and (home_team_id = f.id or away_team_id = f.id)\
                    group by nickname;", (w,) )
            standings = { line[0]: float(line[1])/(float(line[1])+float(line[2])) for line in cursor.fetchall() }

            #print w, standings
            # sort by standings
            fa.sort( key=lambda v: standings[v] )
            #print fa

    status = {}
    cursor.execute( "select ibl, sum(status) as box, sum(scores) as results\
            from sched2014 s, teams2014 t where week <= (%s) and home = code\
            group by ibl;", (week,) )
    for ibl, box, result in cursor.fetchall():
        status[ibl] = ( box, result )

    #print status
    # sort teams who are up to date ahead of those who are not
    fa.sort( key=late )
    #print fa

    if is_cgi:
        print "<br>",
    print "FA signing priority for week %d" % (week + 1)
    if is_cgi:
        print "<br>",
    print "(highest to lowest)"
    for team in fa:
        if is_cgi:
            print "<br>",
        print team

    if is_cgi:
        print "</body></html>"


if __name__ == "__main__":
    main()

