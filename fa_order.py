#!/usr/bin/python

import os
import sys
import psycopg2
import yaml

import DB

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

    boxes = 0
    results = 1

    def late(team):
        # array is (boxes, results)
        # teams on probation pick last
        if team in y['probation']:
            return 2
        # teams under caretaker control are exempt from late penalty
        if team in y['exempt']:
            return 0
        # results or boxes must be current
        if status[team][results] < week and status[team][boxes] < week:
            return 1
        # boxes must be no more than 1 week behind
        if week > 1:
            if status[team][boxes] < week - 1:
                return 1
        #  return 0, team has nothing outstanding
        return 0

    week = 0
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
        # need to have more than 2 series reported to set week
        for week, num in cursor.fetchall():
            if num > 8:
                break

    # start with last year
    # lastyear should be ordered to break ties
    fa = []
    lastyear = {}

    try:
        f = open( DB.bin_dir() + '/data/fa.yml', 'rU' )
    except IOError, err:
        print str(err)
        sys.exit(1)

    y = yaml.safe_load(f)

    if y.has_key('lastyear'):
        for rec in y['lastyear']:
            fa.append( rec[0] )
            lastyear[rec[0]] = float(rec[1])/(float(rec[1])+float(rec[2]))
    else:
        sys.exit(1)

    #print fa
    #print lastyear

    # initial sort by last year's standings
    fa.sort( key=lambda v: lastyear[v] )
    #print fa

    # we begin using current season standings as of week 3
    standings = {}
    if week >= 3:
        for w in range(2, week):
            sql = "select ibl,\
                    sum(case when home_team_id = fcode and\
                    home_score > away_score then 1\
                    when away_team_id = fcode and\
                    away_score > home_score then 1 else 0 end) as w,\
                    sum(case when home_team_id = fcode and\
                    home_score < away_score then 1\
                    when away_team_id = fcode and\
                    away_score < home_score then 1 else 0 end) as l\
                    from games, %s where week <= (%s)\
                    and (home_team_id = fcode or away_team_id = fcode )\
                    group by ibl;" % ( DB.teams, w )
            cursor.execute(sql)
            standings = { line[0]: float(line[1])/(float(line[1])+float(line[2])) for line in cursor.fetchall() }

            #print w, standings
            # sort by standings
            fa.sort( key=lambda v: standings[v] )
            #print fa

    status = {}
    for ibl in fa:
        status[ibl] = {}

    sql = "select ibl, sum(status) as box\
            from %s s, %s t where week <= %i and home = code\
            group by ibl;" %  ( DB.sched, DB.teams, int(week) )
    cursor.execute(sql)
    for ibl, box in cursor.fetchall():
        status[ibl][boxes] = box

    sql = "select ibl, sum(scores) as results\
            from %s s, %s t where week <= %i and home = code\
            group by ibl;" %  ( DB.sched, DB.teams, int(week) )
    cursor.execute(sql)
    for ibl, result in cursor.fetchall():
        status[ibl][results] = result

    #print status
    # sort teams who are up to date ahead of those who are not
    if week > 0:
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

