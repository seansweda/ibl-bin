#!/usr/bin/python

import sys
import re
import getopt

import psycopg2
import DB

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'd')
except getopt.GetoptError, err:
    print str(err)

debug = 0
for (opt, arg) in opts:
    if opt == '-d':
        debug = 1

week = 0
home = 0
away = 0
redo = 0

h_next = ''
a_next = ''

grs = sys.stdin.read()

match = re.search(r'(^|\n)WEEK\s+([0-9]+)', grs)
if match:
    week = match.group(2)

match = re.search(r'(^|\n)HOME\s+([A-Z]+)', grs)
if match:
    home = match.group(2)

match = re.search(r'(^|\n)AWAY\s+([A-Z]+)', grs)
if match:
    away = match.group(2)

match = re.search(r'(^|\n)REDO', grs)
if match:
    redo = match.group()

if week and home and away:
    db = DB.connect()
    cursor = db.cursor()

    code = {}
    team = {}
    sql = "select ibl, code from %s;" % ( DB.teams )
    cursor.execute(sql)

    for ibl, c in cursor.fetchall():
        code[ibl] = c
        team[c] = ibl

    sql = "select scores, away from %s \
            where week = %i and home = '%s';"\
            % ( DB.sched, int(week) + 1, code[home] )
    cursor.execute(sql)
    ( s, c ) = cursor.fetchone()
    if not s:
        h_next = team[c]

    sql = "select scores, home from %s \
            where week = %i and away = '%s';"\
            % ( DB.sched, int(week) + 1, code[away] )
    cursor.execute(sql)
    ( s, c ) = cursor.fetchone()
    if not s:
        a_next = team[c]

    sql = "select status from %s\
            where week = %i and home = '%s' and away = '%s';"\
            % ( DB.sched, int(week), code[home], code[away] )
    cursor.execute(sql)
    ( s, ) = cursor.fetchone()

    if debug:
        print "WEEK %s" % week
        print "HOME %s next: %s" % ( home, h_next )
        print "AWAY %s next: %s" % ( away, a_next )
        if redo:
            print "REDO"

    if not s or redo:
        print home,
        print away,

    print h_next,
    print a_next,
    print

