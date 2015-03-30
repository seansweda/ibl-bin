#!/usr/bin/python

import os
import csv
import sys
import psycopg2

sys.path.append('/home/ibl/bin')
import DB
import injreport

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

    mlb_file = cardpath() + '/' + 'usage.txt'
    if not os.path.isfile(mlb_file):
        print mlb_file + " not found"
        sys.exit(1)
    
    bfp_file = cardpath() + '/' + 'bfp.txt'
    if not os.path.isfile(bfp_file):
        print bfp_file + " not found"
        sys.exit(1)

    INJ = {}
    injreport.main( INJ, quiet=True, report_week = 1 )

    MLB = {}
    with open( mlb_file, 'rU' ) as s:
        for line in csv.reader(s):
            MLB[line[0].rstrip()] = line[1]

    BFP = {}
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
    IBL_B = {}
    cursor.execute(sql)
    for mlb, name, ibl in cursor.fetchall():
        tig_name = mlb.rstrip() + " " + name.rstrip()
        IBL_B[tig_name] = ibl

    sql = "select mlb, name, sum(ip + h + bb)\
            from %s group by mlb, name order by mlb, name;" % DB.pit
    IBL_P = {}
    cursor.execute(sql)
    for mlb, name, ibl in cursor.fetchall():
        tig_name = mlb.rstrip() + " " + name.rstrip()
        IBL_P[tig_name] = ibl

    print "BATTERS             MLB  IBL  INJ CRED     75%    133%    150%"
    cursor.execute( "select tig_name from players where is_batter='Y'\
            order by tig_name;" )
    for name, in cursor.fetchall():
        tig_name = name.rstrip()
        if MLB.has_key(tig_name):
            ibl_U = 0
            if IBL_B.has_key(tig_name):
                ibl_U = float( IBL_B[tig_name] )
            mlb_U = float( MLB[tig_name] )
            inj = 0
            if INJ.has_key(tig_name):
                inj = injreport.injdays( INJ[tig_name], 27 )
            credit = int( 1 + mlb_U / 162 ) * inj
            U_75 = mlb_U * 3 / 4
            U_133 = mlb_U * 4 / 3
            U_150 = mlb_U * 3 / 2
            print "%-18s %4.0f %4.0f %4i %4i %7.1f %7.1f %7.1f" %\
                    ( tig_name, mlb_U, ibl_U, inj, credit, \
                    U_75 - ibl_U - credit, U_133 - ibl_U, U_150 - ibl_U )

    print
    print "PITCHERS            MLB  IBL  INJ CRED     75%    133%    150%"
    cursor.execute( "select tig_name from players where is_pitcher='Y'\
            order by tig_name;" )
    for name, in cursor.fetchall():
        tig_name = name.rstrip()
        if MLB.has_key(tig_name):
            ibl_U = 0
            if IBL_P.has_key(tig_name):
                ibl_U = float( IBL_P[tig_name] )
            mlb_U = float( MLB[tig_name] )
            inj = 0
            if INJ.has_key(tig_name):
                inj = injreport.injdays( INJ[tig_name], 27 )
            credit = int( 1 + mlb_U / 162 ) * inj
            U_75 = mlb_U * 3 / 4
            U_133 = mlb_U * 4 / 3
            U_150 = mlb_U * 3 / 2
            print "%-18s %4.0f %4.0f %4i %4i %7.1f %7.1f %7.1f" %\
                    ( tig_name, mlb_U, ibl_U, inj, credit, \
                    U_75 - ibl_U - credit, U_133 - ibl_U, U_150 - ibl_U )


if __name__ == "__main__":
    main()

