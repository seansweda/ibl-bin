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

def injdays( player, stop ):
    total = 0
    for week in player.keys():
        if week <= stop:
            for series in player[week].keys():
                for x in player[week][series]:
                    if ( x & (injreport.inj + injreport.sus)) > 0:
                        total += 1
    return total

def main( week ):
    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)
    cursor = db.cursor()

    sql = "select mlb, trim(name), sum(g), sum(p), sum(c), sum(\"1b\"), \
            sum(\"2b\"), sum(\"3b\"), sum(ss), sum(lf), sum(cf), sum(rf) \
            from %s where week is null or week <= %i \
            group by mlb, name order by mlb asc, name asc;" \
            % ( DB.starts, int(week) )

    player = {}
    injreport.main( player, quiet=True, report_week = 1 )

    print "MLB Name             GP  SP   C  1B  2B  3B  SS  LF  CF  RF INJ"

    cursor.execute(sql)
    for mlb, name, gp, p, c, b1, b2, b3, ss, lf, cf, rf in cursor.fetchall():
        print "%-3s %-15s %3i %3i %3i %3i %3i %3i %3i %3i %3i %3i" \
                % ( mlb, name, gp, p, c, b1, b2, b3, ss, lf, cf, rf ),

        tig_name = "%s %s" % ( mlb, name )
        if player.has_key(tig_name):
            print "%3i" % int( injdays( player[tig_name], week ) )
        else:
            print "%3i" % 0

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

