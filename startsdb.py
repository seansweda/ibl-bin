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

def main( starts = {}, module = False, report_week = 27 ):
    do_json = False
    is_cgi = False
    if not module and 'GATEWAY_INTERFACE' in os.environ:
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

    if is_cgi:
        if form.has_key('week'):
            report_week = int(form.getfirst('week'))
    elif not module:
        for (opt, arg) in opts:
            if opt == '-i':
                report_week = 0
            elif opt == '-w':
                report_week = arg
            elif opt == '-y':
                DB.starts = 'starts' + arg
                DB.inj = 'inj' + arg

    sql = "select mlb, trim(name), sum(g), sum(p), sum(c), sum(\"1b\"), \
            sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf), sum(rf) \
            from %s where week is null or week <= %i \
            group by mlb, name order by mlb asc, name asc;" \
            % ( DB.starts, int(report_week) )

    player = {}
    injreport.main( player, module=True, report_week = 1 )

    if not module and not is_cgi:
        print "MLB Name             GP  SP   C  1B  2B  3B  SS  LF  CF  RF INJ"

    cursor.execute(sql)
    for line in cursor.fetchall():
        tig_name = line[0].rstrip() + " " + line[1].rstrip()
        starts[tig_name] = line[2:]

    for tig_name in sorted(starts):
        (gp, p, c, b1, b2, b3, ss, lf, cf, rf) = starts[tig_name]
        if is_cgi:
            fmtstr = '"%-18s", %i, %i, %i, %i, %i, %i, %i, %i, %i, %i,'
        else:
            fmtstr = "%-18s %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i"
        if not module:
            print fmtstr % ( tig_name, gp, p, c, b1, b2, b3, ss, lf, cf, rf ),

        if is_cgi:
            fmtstr = "%i"
        else:
            fmtstr = "%3i"
        if not module:
            if player.has_key(tig_name):
                print fmtstr % \
                        int(injreport.injdays( player[tig_name], report_week ))
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

    main()

