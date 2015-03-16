#!/usr/bin/python

import os
import csv
import sys
import psycopg2

sys.path.append('/home/ibl/bin')
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

def search( days, code ):
    found = -1
    for x in range( len(days) ):
        if days[x] & code == code:
            found = x

    return found + 1

def totals( week, code ):
    found = {}
    for loc in week.keys():
        found[loc] = 0
        for x in week[loc]:
            if x & code == code:
                found[loc] += 1
    return found.items()

def update( days, code, length, day = 1 ):
    served = 0
    for x in range( day - 1, len(days) ):
        if code == injured:
            if days[x] & inj != inj:
                if length > 1:
                    days[x] += inj
                    length -= 1
                    served += 1
                elif length == 1:
                    days[x] += dtd
                    length -= 1
                    served += 1
        if code == no_dtd:
            if days[x] & inj != inj:
                if length > 0:
                    days[x] += inj
                    length -= 1
                    served += 1
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

def kind ( code ):
    if code == suspended:
        return sus
    elif code == adjustment:
        return adj
    else:
        # default is injury
        return inj

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

    report_week = 1
    if len(sys.argv) > 1:
        report_week = int(sys.argv[1])
    elif is_cgi and form.has_key('week'):
        report_week = int(form.getfirst('week'))
    else:
        # no user input so we'll find latest week with all results
        sql = "select week, count(*) from %s where status = 1\
                group by week order by week desc;" % DB.sched
        cursor.execute(sql)
        for report_week, num in cursor.fetchall():
            if num == 24:
                break

    player = {}
    sql = "select * from %s order by tig_name, week;" % DB.inj
    cursor.execute(sql)
    for injury in cursor.fetchall():
        week, home, away, day, code, ibl, name, length, failed, desc = injury
        ##print injury

        if not player.has_key(name):
            player[name] = {}

        if ibl == home:
            loc_q = [ 'home', 'away' ]
        else:
            loc_q = [ 'away', 'home' ]

        orig_length = length
        # add 1 for dtd
        if code == injured:
            length += 1

        served = 0
        loc = loc_q[0]
        series = get_series( player, name, week, loc )
        # when day > series length inj time assessed next series
        if day <= len(series):
            served = update( series, code, length, day )
            length -= served
        player[name][week][loc] = series
        ##print "week %2i %s: %i served (%3i) %s" % \
        ##    (week, loc, served, length, dcode(player[name][week][loc]))

        if length > 0 and allstar( week ) and code != suspended:
            loc = 'ASB'
            if player[name].has_key(week) and \
                    player[name][week].has_key(loc):
                series = player[name][week][loc]
            else:
                series = [ 1, 1, 1 ]
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            ##print "week %2i %s: %i served (%3i) %s" % \
            ##    (week, loc, served, length, dcode(player[name][week][loc]))

        while length > 0 and week < 27:
            loc = loc_q[0]
            week += 1
            series = get_series( player, name, week, loc )
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            ##print "week %2i %s: %i served (%3i) %s" % \
            ##    (week, loc, served, length, dcode(player[name][week][loc]))

            if length == 0:
                break
            loc_q.reverse()
            loc = loc_q[0]
            series = get_series( player, name, week, loc )
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            ##print "week %2i %s: %i served (%3i) %s" % \
            ##    (week, loc, served, length, dcode(player[name][week][loc]))

            if length > 0 and allstar( week ) and code != suspended:
                loc = 'ASB'
                if player[name].has_key(week) and \
                        player[name][week].has_key(loc):
                    series = player[name][week][loc]
                else:
                    series = [ 1, 1, 1 ]
                served = update( series, code, length )
                length -= served
                player[name][week][loc] = series
                ##print "week %2i %s: %i served (%3i) %s" % \
                ##    (week, loc, served, length, dcode(player[name][week][loc]))

            # END while length loop

        if length > 0:
            # post-season
            week += 1
            series = []
            loc = 'playoffs'
            for x in range(40):
                series.append(1)
            served = update( series, code, length )
            length -= served
            player[name][week] = { loc: series }
            ##print "week %2i %s: %i served (%3i) %s" % \
            ##    (week, loc, served, length, dcode(player[name][week][loc]))

        if week >= report_week:
            output = "%s " % name.rstrip()

            if code == suspended:
                output += "suspended for %i game" % int(orig_length)
            elif code == adjustment:
                output += "adjustment for %i day" % int(orig_length)
            else:
                # default is injury
                output += "out for %i day" % int(orig_length)
            if orig_length > 1:
                output += "s"

            if length > 0:
                output += ", out for season"
            else:
                days_out = totals( player[name][week], kind(code) )
                days_out.sort( key = lambda s: s[1], reverse=True )
                days_out.sort( key = lambda s: s[0] == 'ASB' )

                week_tot = 0
                for x in days_out:
                    week_tot += x[1]

                if week_tot > 0:
                    # week has affected days
                    output += " through week %i (" % week
                    for x in days_out:
                        output += "%i %s, " % ( x[1], x[0] )
                    output = output[:-2] + ")"
                    if code == injured:
                        output += ", DTD(%i) %s day %i" % \
                                (failed, loc, search(series, dtd))
                else:
                    # otherwise, check previous week
                    if not player[name].has_key(week - 1):
                        player[name][week - 1] = {}
                    days_out = totals( player[name][week - 1], kind(code) )
                    days_out.sort( key = lambda s: s[1], reverse=True )
                    days_out.sort( key = lambda s: s[0] == 'ASB' )

                    week_tot = 0
                    for x in days_out:
                        week_tot += x[1]

                    if week_tot > 0:
                        output += " through week %i (" % (int(week) - 1)
                        for x in days_out:
                            output += "%i %s, " % ( x[1], x[0] )
                        output = output[:-2] + ")"
                    if code == injured:
                        #if len(output) - 1 >  len(name.rstrip()):
                        #    output += ", "
                        output += ", DTD(%i) %s day %i week %i" % \
                                (failed, loc, search(series, dtd), week)

            print '%-80s\t"%s"' % ( output + '.', desc )
            # END if report_week

        # END injury loop

if __name__ == "__main__":
    main()

