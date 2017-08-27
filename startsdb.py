#!/usr/bin/python
#
# flags
# -i: initial starts/limits
# -w: week
# -y: override year
# -t: team
# -a: list actives

import os
import sys
import getopt

import psycopg2

import DB
import injreport

def usage():
    print "usage: %s [-i] [-w week] [-y year] [-t team]" % sys.argv[0]
    sys.exit(1)

def output( name, starts, inj, is_cgi ):
    (gp, p, c, b1, b2, b3, ss, lf, cf, rf) = starts
    if is_cgi:
        fmt = '"%-18s", %i, %i, %i, %i, %i, %i, %i, %i, %i, %i, %i'
    else:
        fmt = "%-18s %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i"

    return fmt % ( injreport.space(name), \
            gp, p, c, b1, b2, b3, ss, lf, cf, rf, inj )

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

    do_active = 0
    team = ''
    if is_cgi:
        if form.has_key('week'):
            report_week = int(form.getfirst('week'))
    elif not module:
        for (opt, arg) in opts:
            if opt == '-i':
                report_week = 0
            if opt == '-a':
                do_active = 1
            elif opt == '-t':
                team = arg
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

    inj = {}
    injreport.main( inj, module=True )

    cursor.execute(sql)
    for line in cursor.fetchall():
        tig_name = line[0].rstrip() + " " + line[1].rstrip()
        starts[tig_name] = line[2:]

    if not module:
        if len( team ) > 0:
            if not is_cgi:
                for spc in range(0, do_active):
                    sys.stdout.write(' ')
                print "MLB Name            GP  SP   C  1B  2B  3B  SS  LF  CF  RF INJ"
            sql = "select tig_name, status from teams where ibl_team = '%s' \
                    and item_type > 0 order by item_type, tig_name;" \
                    % team.upper()
            cursor.execute(sql)
            for tig_name, status in cursor.fetchall():
                tig_name = tig_name.rstrip()
                if inj.has_key(tig_name):
                    days = int(injreport.injdays( inj[tig_name], report_week ))
                else:
                    days = 0
                if starts.has_key(tig_name):
                    if do_active:
                        if status == 1:
                            sys.stdout.write(' ')
                        else:
                            sys.stdout.write('*')
                    print output( tig_name, starts[tig_name], days, is_cgi )
        else:
            if not is_cgi:
                print "MLB Name            GP  SP   C  1B  2B  3B  SS  LF  CF  RF INJ"
            for tig_name in sorted(starts):
                if inj.has_key(tig_name):
                    days = int(injreport.injdays( inj[tig_name], report_week ))
                else:
                    days = 0
                print output( tig_name, starts[tig_name], days, is_cgi )

    db.close()

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:w:y:ai')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    main()

