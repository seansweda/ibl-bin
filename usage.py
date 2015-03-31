#!/usr/bin/python
# -t <team>: usage for specific team

import os
import csv
import sys
import psycopg2
import getopt

sys.path.append('/home/ibl/bin')
import DB
import injreport

INJ = {}
MLB = {}
BFP = {}
IBL_B = {}
IBL_P = {}
IBL_G = {}

pitcher = 1
batter = 2

def usage():
    print "usage: %s [-t team]" % sys.argv[0]
    sys.exit(1)

def cardpath():
    if 'CARDPATH' in os.environ.keys():
        cardpath = os.environ.get('CARDPATH')
    else:
        cardpath = "/home/iblgame/" + time.strftime("%Y") + "/build"
    return cardpath

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

def gp ( ibl ):
    if IBL_G.has_key(ibl):
        return IBL_G[ibl]
    else:
        return 0

def std_usage( name, role, g ):
    if role == pitcher:
        U = IBL_P
    elif role == batter:
        U = IBL_B
    else:
        return ''

    ibl_U = 0
    if U.has_key(name):
        ibl_U = U[name]
    mlb_U = MLB[name]

    inj = 0
    if INJ.has_key(name):
        inj = injreport.injdays( INJ[name], 27 )
    credit = int( 1 + mlb_U / 162 ) * inj

    U_75 = mlb_U * 3 / 4
    U_133 = mlb_U * 4 / 3
    U_150 = mlb_U * 3 / 2

    if g == 0:
        rate = 0
        injrate = 0
    else:
        rate = ( ibl_U * 162 / g ) / mlb_U * 100
        injrate = ( ibl_U * 162 / g + credit ) / mlb_U * 100

    output = "%-18s %4.0f %4.0f %4i %4i %7.1f %7.1f %7.1f %6.1f%% %6.1f%%" %\
            ( name, mlb_U, ibl_U, inj, credit, \
            U_75 - ibl_U - credit, U_133 - ibl_U, U_150 - ibl_U, rate, injrate )
    return output

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
            print "<html><head><title>Usage Report</title></head><body>"
            #dumpenv(form)

    try:
        db = psycopg2.connect("dbname=ibl_stats user=ibl")
    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)
    cursor = db.cursor()

    do_team = 'ALL'
    if not is_cgi:
        for (opt, arg) in opts:
            if opt == '-t':
                do_team = arg.upper()

    mlb_file = cardpath() + '/' + 'usage.txt'
    if not os.path.isfile(mlb_file):
        print mlb_file + " not found"
        sys.exit(1)
    
    bfp_file = cardpath() + '/' + 'bfp.txt'
    if not os.path.isfile(bfp_file):
        print bfp_file + " not found"
        sys.exit(1)

    injreport.main( INJ, quiet=True, report_week = 1 )

    with open( mlb_file, 'rU' ) as s:
        for line in csv.reader(s):
            MLB[line[0].rstrip()] = float(line[1])

    with open( bfp_file, 'rU' ) as s:
        for line in csv.reader(s):
            sp = line[1].strip()
            rp = line[2].strip()
            rest = line[3].strip()
            BFP[line[0].rstrip()] = (sp, rp, rest.split('/') )

#    sql = []
#    sql.append( "select mlb, name, sum(ab + bb)\
#            from %s group by mlb, name order by mlb, name;" % DB.bat )
#    sql.append( "select mlb, name, sum(ip + h + bb)\
#            from %s group by mlb, name order by mlb, name;" % DB.pit )
#    sql.reverse()

    sql = "select mlb, name, sum(ab + bb)\
            from %s group by mlb, name order by mlb, name;" % DB.bat
    cursor.execute(sql)
    for mlb, name, u in cursor.fetchall():
        tig_name = mlb.rstrip() + " " + name.rstrip()
        IBL_B[tig_name] = float(u)

    sql = "select mlb, name, sum(ip + h + bb)\
            from %s group by mlb, name order by mlb, name;" % DB.pit
    cursor.execute(sql)
    for mlb, name, u in cursor.fetchall():
        tig_name = mlb.rstrip() + " " + name.rstrip()
        IBL_P[tig_name] = float(u)

    sql = "select ibl, sum(gs) from %s group by ibl;" % DB.pit
    cursor.execute(sql)
    for ibl, g in cursor.fetchall():
        IBL_G[ibl.rstrip()] = float(g)
    IBL_G['FA'] = max( IBL_G.values() )

    print "BATTERS             MLB  IBL  INJ CRED     75%    133%    150%    RATE    +INJ"
    sql = "select ibl_team, tig_name from teams where item_type = %s" % batter
    if do_team != 'ALL':
        sql += " and ibl_team = '%s'" % do_team
    sql += " order by tig_name;"
    cursor.execute(sql)
    for ibl, name, in cursor.fetchall():
        tig_name = name.rstrip()
        if MLB.has_key(tig_name):
            print std_usage( tig_name, batter, gp(ibl) )

    print
    print "PITCHERS            MLB  IBL  INJ CRED     75%    133%    150%    RATE    +INJ"
    sql = "select ibl_team, tig_name from teams where item_type = %s" % pitcher
    if do_team != 'ALL':
        sql += " and ibl_team = '%s'" % do_team
    sql += " order by tig_name;"
    cursor.execute(sql)
    for ibl, name, in cursor.fetchall():
        tig_name = name.rstrip()
        if MLB.has_key(tig_name):
            print std_usage( tig_name, pitcher, gp(ibl) )


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    main()

