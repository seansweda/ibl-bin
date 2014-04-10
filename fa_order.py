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

    def late(team):
        # tuple is (boxes, results)
        # catch odd case where boxes are current but scores broken
        if status[team][0] == week:
            return 0
        # results must be current
        if status[team][1] != week:
            return 1
        # boxes must be no more than 1 week behind
        if status[team][0] < week - 1:
            return 1
        #  return 0, team has nothing outstanding
        return 0

    if len(sys.argv) > 1:
        # user inputs FA signing week (not results week), so subtract 1
        week = int(sys.argv[1]) - 1
    elif is_cgi and form.has_key('week'):
        # user inputs FA signing week (not results week), so subtract 1
        week = int(form.getfirst('week')) - 1
    else:
        # no user input so we'll find latest week with reported results
        cursor.execute("select week, count(*) from games\
                group by week order by week desc;");
        # need to have more than 1 series reported to set week
        for week, num in cursor.fetchall():
            if num > 5:
                break

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

    if do_json:
        print json.dumps({ "week": (week + 1), "teams": fa })
    else:
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

