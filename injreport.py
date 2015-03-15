#!/usr/bin/python

import os
import csv
import sys
import psycopg2

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

def flip( site ):
    if site == 'home':
        return 'away'
    else:
        return 'home'

def offday( week ):
    offweeks = ( 2, 5, 8, 10, 13, 18, 21, 24 )
    return offweeks.count( week )

def allstar( week ):
    if week == 15:
        return True
    else:
        return False

def get_series( player, name, week, loc ):
    if player[name].has_key(week):
        if player[name][week].has_key(loc):
            return player[name][week][loc]
        else:
            player[name][week][loc] = {}
    else:
        player[name][week] = {}
        player[name][week][loc] = {}

    obj = [ 0, 0, 0 ]
    for x in range( offday(week) ):
        obj.append(1)
    return obj

def update( days, code, length ):
    served = 0
    for x in range( len(days) ):
        if code == injured or code == no_dtd:
            if days[x] & inj != inj:
                if length > 0:
                    days[x] += inj
                    length -= 1
                    served += 1
                elif length == 0 and code == injured:
                    days[x] += dtd
                    length -= 1
        if code == suspended:
            if days[x] & sus != sus and days[x] & off != off:
                if length > 0:
                    days[x] += sus
                    length -= 1
                    served += 1
        if code == adjustment:
            if length > 0:
                days[x] += adj
                length -= 1
                served += 1

    return served

def dcode( days ):
    output = "["
    dc = { off:'off', inj:'inj', dtd:'dtd', sus:'sus', adj:'adj' }
    for x in days:
        if x == ok:
            output += "( OK  )"
        else:
            output += "( "
            for val in dc.keys():
                if x & val != 0:
                    output += dc[val]
                    output += " "
            output += ")"
    output += "]"
    return output

# sql table injury codes
injured = 0
no_dtd = 1
suspended = 2
adjustment = 3

# display codes (bitwise)
ok  =  0
off =  1
inj =  2
dtd =  4
sus =  8
adj = 16

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
    sql = "select * from %s order by week, tig_name" % DB.inj
    cursor.execute(sql)
    for injury in cursor.fetchall():
        week, home, away, day, code, ibl, name, length, dtd, desc = injury

        if not player.has_key(name):
            player[name] = {}

        print injury

        served = 3 - day + 1
        if code != suspended:
            served += offday( week )
        length -= served

        if ibl == home:
            loc = 'home'
        else:
            loc = 'away'
        print "week %2i %s: %i served (%3i)" % (week, loc, served, length)

        while length > 0 and week < 27:
            week += 1

            series = get_series( player, name, week, loc )
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            print "week %2i %s: %i served (%3i) %s" % \
                    (week, loc, served, length, dcode(player[name][week][loc]))

            if length == 0:
                break
            loc = flip( loc )

            series = get_series( player, name, week, loc )
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            print "week %2i %s: %i served (%3i) %s" % \
                    (week, loc, served, length, dcode(player[name][week][loc]))

            if allstar( week ) and code != suspended:
                if player[name].has_key(week) and \
                        player[name][week].has_key('ASB'):
                    series = player[name][week]['ASB']
                else:
                    series = [ 1, 1, 1 ]
                served = update( series, code, length )
                length -= served
                player[name][week]['ASB'] = series
                print "week %2i %s: %i served (%3i) %s" % \
                    (week, 'ASB ', served, length, dcode(player[name][week]['ASB']))

        if length > 0:
            # post-season
            series = []
            for x in range(40):
                series.append(1)
            served = update( series, code, length )
            length -= served
            player[name][week]['post'] = series
            print "week %2i %s: %i served (%3i) %s" % \
                (week, 'post', served, length, dcode(player[name][week]['post']))

        print player
        print

if __name__ == "__main__":
    main()

