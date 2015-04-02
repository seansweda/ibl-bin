#!/usr/bin/python
#
# flags
# -i: initial starts/limits
# -w: week
# -y: override year

import os
import sys
import getopt

import psycopg2

sys.path.append('/home/ibl/bin')
import DB
import injreport

def usage():
    print "usage: %s [-i] [-w week] [-y year]" % sys.argv[0]
    sys.exit(1)

def main( week ):
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
            print "Content-Type: text/csv"
            print
            #dumpenv(form)

    db = DB.connect()
    cursor = db.cursor()

    if is_cgi and form.has_key('week'):
        week = int(form.getfirst('week'))
    sql = "select mlb, trim(name), sum(g), sum(p), sum(c), sum(\"1b\"), \
            sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf), sum(rf) \
            from %s where week is null or week <= %i \
            group by mlb, name order by mlb asc, name asc;" \
            % ( DB.starts, int(week) )

    player = {}
    injreport.main( player, quiet=True, report_week = 1 )

    if not is_cgi:
        print "MLB Name             GP  SP   C  1B  2B  3B  SS  LF  CF  RF INJ"

    cursor.execute(sql)
    for mlb, name, gp, p, c, b1, b2, b3, ss, lf, cf, rf in cursor.fetchall():
        if is_cgi:
            fmtstr = '"%-3s %-s", %i, %i, %i, %i, %i, %i, %i, %i, %i, %i,'
        else:
            fmtstr = "%-3s %-15s %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i"
        print fmtstr % ( mlb, name, gp, p, c, b1, b2, b3, ss, lf, cf, rf ),

        tig_name = "%s %s" % ( mlb, name )
        if is_cgi:
            fmtstr = "%i"
        else:
            fmtstr = "%3i"
        if player.has_key(tig_name):
            print fmtstr % int( injreport.injdays( player[tig_name], week ) )
        else:
            print fmtstr % 0

    db.close()
    ##print player

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'w:y:i')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    week = 27
    for (opt, arg) in opts:
        if opt == '-i':
            week = 0
        elif opt == '-w':
            week = arg
        elif opt == '-y':
            DB.starts = 'starts' + arg
            DB.inj = 'inj' + arg

    main( week )

