#!/usr/bin/python
# -t <team>: usage for specific team
# -g: per game output
# -r: rates output
# -B: batters only
# -P: pitchers only

import os
import csv
import sys
import psycopg2
import getopt
import time

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
    if 'IBL_CARDPATH' in os.environ.keys():
        cardpath = os.environ.get('IBL_CARDPATH')
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
        return float( IBL_G[ibl] )
    else:
        return 0.0

def r_usage( name, role, g ):
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
    U_75 = int( U_75 - ibl_U - credit + 1 )

    U_133 = mlb_U * 4 / 3
    U_133 = int( U_133 - ibl_U )

    if g == 0:
        rate = 0
        injrate = 0
    else:
        rate = ( ibl_U * 162 / g ) / mlb_U * 100
        injrate = ( ibl_U * 162 / g + credit ) / mlb_U * 100

    output = "%-18s" % name
    output += "%4i %6.1f %6.1f" \
            % ( U_75, U_75 / (162 - g), U_75 / (162.0 - g) * 6.0 )
    output += "   %4i %6.1f %6.1f" \
            % ( U_133, U_133 / (162 - g), U_133 / (162.0 - g) * 6.0 )

    output += "  %6.1f%% %6.1f%%" % ( rate, injrate )

    return output

def g_usage( name, role, g ):
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
    U_75 = int( U_75 - ibl_U - credit + 1 )

    U_133 = mlb_U * 4 / 3
    U_133 = int( U_133 - ibl_U )

    u75 = []
    u133 = []
    if role == pitcher:
        fat_SP = BFP[name][0]
        if fat_SP > 0:
            u75.append( U_75 / fat_SP )
            u75.append( U_75 / 24.0 )
            u133.append( U_133 / fat_SP )
            u133.append( U_133 / 24.0 )
        else:
            u75 += [ 0, 0 ]
            u133 += [ 0, 0 ]
        fat_RP = BFP[name][1]
        if fat_RP > 0:
            u75.append( U_75 / fat_RP )
            u133.append( U_133 / fat_RP )
        else:
            u75.append( 0 )
            u133.append( 0 )
        rest1 = BFP[name][2][1]
        if rest1 > 0:
            u75.append( U_75 / rest1 )
            u133.append( U_133 / rest1 )
        else:
            u75.append( 0 )
            u133.append( 0 )

    elif role == batter:
        for p in range(2,6):
            u75.append( U_75 / float(p) )
        for p in range(2,6):
            u133.append( U_133 / float(p) )

    output = "%-18s" % name
    output += "%4i " % U_75
    u75.reverse()
    while len(u75):
        output += " %5.0f" % round( u75.pop(), 0 )
    output += "   %4i" % U_133
    u133.reverse()
    while len(u133):
        output += " %5i" % int( u133.pop() )

    return output

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

    db = DB.connect()
    cursor = db.cursor()

    do_team = 'ALL'
    do_g = False
    do_r = False
    do_bat = True
    do_pit = True

    if is_cgi:
        if form.has_key('team'):
            do_team = form.getfirst('team').upper()
    else:
        for (opt, arg) in opts:
            if opt == '-t':
                do_team = arg.upper()
            elif opt == '-B':
                do_pit = False
            elif opt == '-P':
                do_bat = False
            elif opt == '-g':
                do_g = True
            elif opt == '-r':
                do_r = True

    mlb_file = cardpath() + '/' + 'usage.txt'
    if not os.path.isfile(mlb_file):
        print mlb_file + " not found"
        sys.exit(1)
    
    bfp_file = cardpath() + '/' + 'bfp.txt'
    if not os.path.isfile(bfp_file):
        print bfp_file + " not found"
        sys.exit(1)

    with open( mlb_file, 'rU' ) as s:
        for line in csv.reader(s):
            MLB[line[0].rstrip()] = float(line[1])

    with open( bfp_file, 'rU' ) as s:
        for line in csv.reader(s):
            sp = line[1].strip()
            if sp.isdigit():
                sp = float( sp )
            else:
                sp = float( 0 )
            rp = line[2].strip()
            if rp.isdigit():
                rp = float( rp )
            else:
                rp = float( 0 )
            rest = []
            for x in line[3].split('/'):
                val = x.strip()
                if val.isdigit():
                    rest.append( float(val) )
                else:
                    rest.append( float(0) )
            BFP[line[0].rstrip()] = (sp, rp, rest )

    injreport.main( INJ, module=True, report_week = 1 )

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

    if is_cgi:
        print "<pre>"

    if do_pit:
        if do_g:
            print "PITCHERS           75%   SP/f SP/24  RP/f RP/1d   133%  SP/f SP/24  RP/f RP/1d"
        elif do_r:
            print "PITCHERS           75%  per/g  per/w   133%  per/g  per/w     RATE    +INJ"
        else:
            print "PITCHERS            MLB  IBL  INJ CRED     75%    133%    150%    RATE    +INJ"

        sql = "select ibl_team, tig_name from teams where item_type = %s" % pitcher
        if do_team != 'ALL':
            sql += " and ibl_team = '%s'" % do_team
        sql += " order by tig_name;"
        cursor.execute(sql)
        for ibl, name, in cursor.fetchall():
            tig_name = name.rstrip()
            if MLB.has_key(tig_name):
                if do_g:
                    print g_usage( tig_name, pitcher, gp(ibl) )
                elif do_r:
                    print r_usage( tig_name, pitcher, gp(ibl) )
                else:
                    print std_usage( tig_name, pitcher, gp(ibl) )

    if do_bat and do_pit:
        print

    if do_bat:
        if do_g:
            print "BATTERS            75%    2/g   3/g   4/g   5/g   133%   2/g   3/g   4/g   5/g"
        elif do_r:
            print "BATTERS            75%  per/g  per/w   133%  per/g  per/w     RATE    +INJ"
        else:
            print "BATTERS             MLB  IBL  INJ CRED     75%    133%    150%    RATE    +INJ"

        sql = "select ibl_team, tig_name from teams where item_type = %s" % batter
        if do_team != 'ALL':
            sql += " and ibl_team = '%s'" % do_team
        sql += " order by tig_name;"
        cursor.execute(sql)
        for ibl, name, in cursor.fetchall():
            tig_name = name.rstrip()
            if MLB.has_key(tig_name):
                if do_g:
                    print g_usage( tig_name, batter, gp(ibl) )
                elif do_r:
                    print r_usage( tig_name, batter, gp(ibl) )
                else:
                    print std_usage( tig_name, batter, gp(ibl) )

    if is_cgi:
        print "</pre></body></html>"


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:grBP')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    main()

