#!/usr/bin/python

from __future__ import (print_function, unicode_literals)

import os
import sys
import getopt
import psycopg2

import DB

def usage():
    print("usage: %s [-w week]" % sys.argv[0])
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

# schedule
DAYS_OFF = ( 4, 8 )
LAST = 11
ASB = 15

# sql table injury codes
injured = 0
no_dtd = 1
suspended = 2
adjustment = 3
arm_trouble = 4

# display codes (bitwise)
ok  =  0
off =  1
inj =  2
dtd =  4
sus =  8
adj = 16
arm = 32

def injdays( player, stop, type = inj ):
    total = 0
    for week in list(player.keys()):
        if week <= stop:
            for series in list(player[week].keys()):
                for x in player[week][series]:
                    if ( x & (type + sus)) > 0:
                        total += 1
    return total

def offday( week ):
    offweeks = DAYS_OFF
    return offweeks.count( week )

def allstar( week ):
    if week == ASB:
        return True
    else:
        return False

def get_series( player, name, week, loc ):
    if week in player[name]:
        if loc in player[name][week]:
            return player[name][week][loc]
        else:
            player[name][week][loc] = {}
    else:
        player[name][week] = {}
        player[name][week][loc] = {}

    if week == 28:
        obj = []
        for x in range(40):
            obj.append(0)
    else:
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
    for loc in list(week.keys()):
        found[loc] = 0
        for x in week[loc]:
            if x & code == code:
                found[loc] += 1
    return list(found.items())

def update( days, code, length, day = 1 ):
    served = 0
    for x in range( day - 1, len(days) ):
        if code == injured:
            if length == 1 and days[x] & off == 0:
                if days[x] & dtd == 0:
                    days[x] += dtd
                length -= 1
                served += 1
            elif days[x] & inj == 0:
                if length > 1:
                    days[x] += inj
                    length -= 1
                    served += 1
        if code == no_dtd:
            if days[x] & inj == 0:
                if length > 0:
                    days[x] += inj
                    length -= 1
                    served += 1
        if code == arm_trouble:
            if days[x] & arm == 0:
                if length > 0:
                    days[x] += arm
                    length -= 1
                    served += 1
        if code == suspended:
            if days[x] & (sus + off) == 0:
                if length > 0:
                    days[x] += sus
                    length -= 1
                    served += 1
        if code == adjustment:
            if length > 0:
                if days[x] & adj == 0:
                    days[x] += adj
                length -= 1
                served += 1

    return served

def dcode( days ):
    output = "["
    dc = { off:'off', inj:'inj', dtd:'dtd', sus:'sus', adj:'adj', arm:'arm' }
    for x in days:
        if x == ok:
            output += "( OK  )"
        else:
            output += "( "
            for val in list(dc.keys()):
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
    elif code == arm_trouble:
        return arm
    else:
        # default is injury
        return inj

def space ( tigname ):
    if tigname[2] == ' ':
        return tigname[0:2] + ' ' + tigname[2:]
    else:
        return tigname

def main( player = {}, module = False, report_week = 0 ):
    do_json = False
    is_cgi = False
    if not module and 'GATEWAY_INTERFACE' in os.environ:
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
            if 'notitle' not in form:
                print("<html><head><title>IBL Injury Report</title></head><body>")
            #dumpenv(form)

    db = DB.connect()
    cursor = db.cursor()

    # unset for actives only
    do_all = 1

    if is_cgi:
        if 'week' in form:
            report_week = int(form.getfirst('week'))
        if 'active' in form:
            do_all = 0
    elif not module:
        for (opt, arg) in opts:
            if opt == '-a':
                do_all = 0;
            elif opt == '-w':
                report_week = int(arg)
            else:
                print("bad option:", opt)
                usage()

    if report_week == 0:
    # no user supplied week, use latest week without all inj reported
        sql = "select week, count(*) from %s where inj = 1\
                group by week order by week desc;" % DB.sched
        cursor.execute(sql)
        for week, num in cursor.fetchall():
            if num == 24:
                report_week = week + 1
                break

    if is_cgi and not module:
        print("<table>")

    sql = "select week, home, away, day, type, ibl, ibl_team, status, \
             i.tig_name, length, dtd, description from %s i \
             left outer join rosters t on i.tig_name = t.tig_name\
             order by ibl_team, i.tig_name, week;" % DB.inj
    cursor.execute(sql)
    for injury in cursor.fetchall():
        week, home, away, day, code, inj_team, ibl, active, \
                name, length, failed, desc = injury
        ##print injury
        name = name.rstrip()

        if active != 1:
            active = 0

        if name not in player:
            player[name] = {}

        if week == 28:
            loc_q = [ 'playoffs' ]
        elif inj_team == home:
            loc_q = [ 'home', 'away' ]
        else:
            loc_q = [ 'away', 'home' ]

        reported_day = day
        reported_week = week
        reported_loc = loc_q[0]
        reported_length = length
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
            # dtd expires during ASB
            if code == injured and length <= 3:
                code = no_dtd
                length -= 1
            loc = 'ASB'
            if week in player[name] and \
                    loc in player[name][week]:
                series = player[name][week][loc]
            else:
                series = [ 1, 1, 1 ]
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            ##print "week %2i %s: %i served (%3i) %s" % \
            ##    (week, loc, served, length, dcode(player[name][week][loc]))

        while length > 0 and week < LAST:
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
                # dtd expires during ASB
                if code == injured and length <= 3:
                    code = no_dtd
                    length -= 1
                loc = 'ASB'
                if week in player[name] and \
                        loc in player[name][week]:
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
            if week == LAST:
                week += 1
            loc = 'playoffs'
            series = get_series( player, name, week, loc )
            served = update( series, code, length )
            length -= served
            player[name][week][loc] = series
            ##print "week %2i %s: %i served (%3i) %s" % \
            ##    (week, loc, served, length, dcode(player[name][week][loc]))

        if not module and week >= report_week:
            if not ibl:
                ibl = inj_team
            output = "%s %s " % (ibl, space(name) )

            if code == suspended:
                output += "suspended for %i game" % int(reported_length)
            elif code == adjustment:
                output += "adjustment for %i day" % int(reported_length)
            elif code == arm_trouble:
                output += "cannot pitch for %i day" % int(reported_length)
            else:
                # default is injury
                output += "out for %i day" % int(reported_length)

            if reported_length != 1:
                output += "s"
            output += ", "

            if reported_length > 1:
                output += "from "
            output += "week %s (%s day %s)" \
                    % ( reported_week, reported_loc, reported_day )

            if length > 0:
                output += " through end of season"
            else:
                days_out = totals( player[name][week], kind(code) )
                days_out.sort( key = lambda s: s[1], reverse=True )
                days_out.sort( key = lambda s: s[0] == 'ASB' )

                week_tot = 0
                for x in days_out:
                    week_tot += x[1]

                if week_tot == 0:
                    # player available start of week, check previous
                    thru_week = week - 1
                    if thru_week not in player[name]:
                        player[name][thru_week] = {}
                    days_out = totals( player[name][thru_week], kind(code) )
                    days_out.sort( key = lambda s: s[1], reverse=True )
                    days_out.sort( key = lambda s: s[0] == 'ASB' )

                elif reported_length > 0:
                    thru_week = week

                if reported_length > 1:
                    output += " through week %i (" % thru_week

                    if reported_week == thru_week:
                        # ends same week it starts (check for ASB days)
                        days_out.sort( key = lambda s: s[1], reverse=True )
                        if days_out[0][0] == 'ASB' and days_out[0][1] > 0:
                            output += "%s day %i)" % ( 'ASB', days_out[0][1] )
                        else:
                            output += "%s day %i)" % ( reported_loc, \
                                    reported_day + reported_length - 1 )

                    else:
                        # ends in future week
                        for x in days_out:
                            output += "%i %s, " % ( x[1], x[0] )
                        output = output[:-2] + ")"

                if code == injured:
                    output += ", DTD (+%i) %s day %i" % \
                            (failed, loc, search(series, dtd))
                    if thru_week != week:
                        output += " week %i" % week

            if do_all or active:
                if is_cgi:
                    print('<tr><td>%s</td><td>"%s"</td></tr>' % \
                            ( output + '.', desc ))
                else:
                    print('%-80s\t"%s"' % ( output + '.', desc ))
            # END if report_week

        # END injury loop

    if is_cgi and not module:
        print("</table>")

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'aw:')
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    main()

