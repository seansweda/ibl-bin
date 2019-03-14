#!/usr/bin/python
# -t <team>: usage for specific team
# -g: per game output
# -r: rates output
# -B: batters only
# -P: pitchers only
# -A: rostered players only

import os
import csv
import sys
import psycopg2
import getopt
import time

import DB
import injreport

INJ = {}
BFP = {}
MLB_B = {}
MLB_P = {}
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
    if IBL_G.has_key(ibl) and IBL_G[ibl]:
        return float( IBL_G[ibl] )
    else:
        return 0.0

def injdays ( name, role ):
    if INJ.has_key(name):
        if role == batter:
            return injreport.injdays( INJ[name], 27 )
        elif role == pitcher:
            # two-way players use "arm" injury for pitching usage credit
            if MLB_B.has_key(name):
                return injreport.injdays( INJ[name], 27,
                        injreport.arm + injreport.inj )
            else:
                return injreport.injdays( INJ[name], 27 )

    # no match, return 0
    return 0

def r_usage( name, role, g, do_o = False ):
    if role == pitcher:
        U = IBL_P
        M = MLB_P
    elif role == batter:
        U = IBL_B
        M = MLB_B
    else:
        return ''

    ibl_U = 0
    mlb_U = 0
    if U.has_key(name):
        ibl_U = U[name]
    if M.has_key(name):
        mlb_U = M[name]

    inj = injdays( name, role )
    credit = int( 1 + mlb_U / 162 ) * inj

    if do_o:
        U_75 = int ( mlb_U * 4 / 3 )
        U_75 -= ibl_U

        U_133 = int( mlb_U * 3 / 2 )
        U_133 -= ibl_U
    else:
        U_75 = mlb_U * 3 / 4
        if U_75 != int ( U_75 ):
            U_75 = int ( U_75 ) + 1
        U_75 -= ( ibl_U + credit )

        U_133 = int ( mlb_U * 4 / 3 )
        U_133 -= ibl_U

    if g == 0:
        rate = 0
        injrate = 0
    else:
        rate = ( ibl_U * 162 / g ) / mlb_U * 100
        injrate = ( ibl_U * 162 / g + credit ) / mlb_U * 100

    output = "%-18s" % injreport.space(name)
    output += "%4i " % U_75
    if g >= 162 or U_75 <= 0:
        output += "%6s %6s" % ( '-', '-' )
    else:
        output += "%6.1f %6.1f" \
            % ( U_75 / (162 - g), min( U_75 / (162.0 - g) * 6.0, U_75 ) )

    output += "   %4i " % U_133
    if g >= 162 or U_133 <= 0:
        output += "%6s %6s" % ( '-', '-' )
    else:
        output += "%6.1f %6.1f" \
            % ( U_133 / (162 - g), min( U_133 / (162.0 - g) * 6.0, U_133 ) )

    output += "  %6.1f%% %6.1f%%" % ( rate, injrate )

    return output

def g_usage( name, role, g, do_o = False ):
    if role == pitcher:
        U = IBL_P
        M = MLB_P
    elif role == batter:
        U = IBL_B
        M = MLB_B
    else:
        return ''

    ibl_U = 0
    mlb_U = 0
    if U.has_key(name):
        ibl_U = U[name]
    if M.has_key(name):
        mlb_U = M[name]

    inj = injdays( name, role )
    credit = int( 1 + mlb_U / 162 ) * inj

    if do_o:
        U_75 = int ( mlb_U * 4 / 3 )
        U_75 -= ibl_U

        U_133 = int( mlb_U * 3 / 2 )
        U_133 -= ibl_U
    else:
        U_75 = mlb_U * 3 / 4
        if U_75 != int ( U_75 ):
            U_75 = int ( U_75 ) + 1
        U_75 -= ( ibl_U + credit )

        U_133 = int ( mlb_U * 4 / 3 )
        U_133 -= ibl_U

    g75 = []
    g133 = []
    if role == pitcher:
        fat_SP = BFP[name][0]
        fat_RP = BFP[name][1]
        rest1 = BFP[name][2][1]
        if U_75 <= 0:
            g75 += [ 0, 0, 0, 0 ]
        else:
            if fat_SP > 0:
                g75.append( U_75 / fat_SP )
                g75.append( U_75 / 24.0 )
            else:
                g75 += [ 0, 0 ]
            if fat_RP > 0:
                g75.append( U_75 / fat_RP )
            else:
                g75.append( 0 )
            if rest1 > 0:
                g75.append( U_75 / rest1 )
            else:
                g75.append( 0 )
        if U_133 <= 0:
            g133 += [ 0, 0, 0, 0 ]
        else:
            if fat_SP > 0:
                g133.append( U_133 / fat_SP )
                g133.append( U_133 / 24.0 )
            else:
                g133 += [ 0, 0 ]
            if fat_RP > 0:
                g133.append( U_133 / fat_RP )
            else:
                g133.append( 0 )
            if rest1 > 0:
                g133.append( U_133 / rest1 )
            else:
                g133.append( 0 )

    elif role == batter:
        if U_75 <= 0:
            g75 += [ 0, 0, 0, 0 ]
        else:
            for p in range(2,6):
                g75.append( U_75 / float(p) )
        if U_133 <= 0:
            g133 += [ 0, 0, 0, 0 ]
        else:
            for p in range(2,6):
                g133.append( U_133 / float(p) )

    output = "%-18s" % injreport.space(name)
    output += "%4i " % U_75
    g75.reverse()
    while len(g75):
        output += " %5.0f" % round( g75.pop(), 0 )
    output += "   %4i" % U_133
    g133.reverse()
    while len(g133):
        output += " %5i" % int( g133.pop() )

    return output

def std_usage( name, role, g ):
    if role == pitcher:
        U = IBL_P
        M = MLB_P
    elif role == batter:
        U = IBL_B
        M = MLB_B
    else:
        return ''

    ibl_U = 0
    mlb_U = 0
    if U.has_key(name):
        ibl_U = U[name]
    if M.has_key(name):
        mlb_U = M[name]

    inj = injdays( name, role )
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
            ( injreport.space(name), mlb_U, ibl_U, inj, credit, \
            round( U_75 - ibl_U - credit, 1 ), \
            int( (U_133 - ibl_U) * 10 ) / 10.0, \
            int( (U_150 - ibl_U) * 10 ) / 10.0, rate, injrate )
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

    do_team = ''
    sql_team = ''
    do_g = False
    do_r = False
    do_o = False
    do_bat = True
    do_pit = True

    if is_cgi:
        if form.has_key('team'):
            do_team = form.getfirst('team').upper()
        if form.has_key('batters'):
            do_pit = False
        if form.has_key('pitchers'):
            do_bat = False
    else:
        for (opt, arg) in opts:
            if opt == '-t':
                do_team = arg.upper()
            elif opt == '-A':
                sql_team = " and ibl_team != 'FA'"
            elif opt == '-B':
                do_pit = False
            elif opt == '-P':
                do_bat = False
            elif opt == '-g':
                do_g = True
            elif opt == '-r':
                do_r = True
            elif opt == '-o':
                do_o = True

    if len( do_team ) > 0 and len( sql_team ) == 0:
        sql_team = " and ibl_team = '%s'" % do_team

    mlb_file = cardpath() + '/usage_bf.txt'
    if not os.path.isfile(mlb_file):
        print mlb_file + " not found"
        sys.exit(1)
    with open( mlb_file, 'rU' ) as s:
        for line in csv.reader(s):
            MLB_P[line[0].rstrip()] = float(line[1])

    mlb_file = cardpath() + '/usage_pa.txt'
    if not os.path.isfile(mlb_file):
        print mlb_file + " not found"
        sys.exit(1)
    with open( mlb_file, 'rU' ) as s:
        for line in csv.reader(s):
            MLB_B[line[0].rstrip()] = float(line[1])

    bfp_file = cardpath() + '/' + 'bfp.txt'
    if not os.path.isfile(bfp_file):
        print bfp_file + " not found"
        sys.exit(1)

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

    injreport.main( INJ, module=True )

    sql = "select mlb, name, sum(vl + vr)\
            from %s group by mlb, name order by mlb, name;" % DB.usage
    cursor.execute(sql)
    for mlb, name, u in cursor.fetchall():
        tig_name = mlb.rstrip() + " " + name.rstrip()
        IBL_B[tig_name] = float(u)

    sql = "select mlb, name, sum(bf)\
        from %s group by mlb, name order by mlb, name;" % DB.usage
    cursor.execute(sql)
    for mlb, name, u in cursor.fetchall():
        tig_name = mlb.rstrip() + " " + name.rstrip()
        IBL_P[tig_name] = float(u)

    sql = "select ibl, sum(gs) from %s group by ibl;" % DB.pit
    cursor.execute(sql)
    for ibl, g in cursor.fetchall():
        IBL_G[ibl.rstrip()] = float(g)
    if IBL_G.values():
        IBL_G['FA'] = max( IBL_G.values() )
    else:
        IBL_G['FA'] = 0

    if is_cgi:
        print "<pre>"

    if do_pit:
        if do_g:
            if do_o:
                print "PITCHERS          133%   SP/f SP/24  RP/f RP/1d   150%  SP/f SP/24  RP/f RP/1d"
            else:
                print "PITCHERS           75%   SP/f SP/24  RP/f RP/1d   133%  SP/f SP/24  RP/f RP/1d"
        elif do_r:
            if do_o:
                print "PITCHERS          133%  per/g  per/w   150%  per/g  per/w     RATE    +INJ"
            else:
                print "PITCHERS           75%  per/g  per/w   133%  per/g  per/w     RATE    +INJ"
        else:
            print "PITCHERS            MLB  IBL  INJ CRED     75%    133%    150%    RATE    +INJ"

        sql = "select ibl_team, r.tig_name from rosters r, players p where r.tig_name = p.tig_name and is_pitcher = 'Y'"
        sql += sql_team
        sql += " order by tig_name;"
        cursor.execute(sql)
        for ibl, tig_name, in cursor.fetchall():
            tig_name = tig_name.rstrip()
            ibl = ibl.rstrip()
            if MLB_P.has_key(tig_name):
                if do_g:
                    print g_usage( tig_name, pitcher, gp(ibl), do_o )
                elif do_r:
                    print r_usage( tig_name, pitcher, gp(ibl), do_o )
                else:
                    print std_usage( tig_name, pitcher, gp(ibl) )

    if do_bat and do_pit:
        print

    if do_bat:
        if do_g:
            if do_o:
                print "BATTERS           133%    2/g   3/g   4/g   5/g   153%   2/g   3/g   4/g   5/g"
            else:
                print "BATTERS            75%    2/g   3/g   4/g   5/g   133%   2/g   3/g   4/g   5/g"
        elif do_r:
            if do_o:
                print "BATTERS           133%  per/g  per/w   150%  per/g  per/w     RATE    +INJ"
            else:
                print "BATTERS            75%  per/g  per/w   133%  per/g  per/w     RATE    +INJ"
        else:
            print "BATTERS             MLB  IBL  INJ CRED     75%    133%    150%    RATE    +INJ"

        sql = "select ibl_team, r.tig_name from rosters r, players p where r.tig_name = p.tig_name and is_batter = 'Y'"
        sql += sql_team
        sql += " order by tig_name;"
        cursor.execute(sql)
        for ibl, tig_name, in cursor.fetchall():
            tig_name = tig_name.rstrip()
            ibl = ibl.rstrip()
            if MLB_B.has_key(tig_name):
                if do_g:
                    print g_usage( tig_name, batter, gp(ibl), do_o )
                elif do_r:
                    print r_usage( tig_name, batter, gp(ibl), do_o )
                else:
                    print std_usage( tig_name, batter, gp(ibl) )

    if is_cgi:
        print "</pre></body></html>"


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 't:groABP')
    except getopt.GetoptError, err:
        print str(err)
        usage()

    main()

