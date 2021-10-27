#!/usr/bin/env python

from __future__ import (print_function, unicode_literals)

import sys
import re
import getopt

import psycopg2
import DB

try:
    (opts, args) = getopt.getopt(sys.argv[1:], 'd')
except getopt.GetoptError as err:
    print(str(err))

debug = 0
for (opt, arg) in opts:
    if opt == '-d':
        debug = 1

week = 0
home = 0
away = 0

h_next = ''
a_next = ''
admin = False

grs = sys.stdin.read()

match = re.search(r'(^|\n)\s*WEEK\s+([0-9]+)', grs, flags=re.IGNORECASE)
if match:
    week = match.group(2)

match = re.search(r'(^|\n)\s*HOME\s+([A-Z]+)', grs, flags=re.IGNORECASE)
if match:
    home = match.group(2)

match = re.search(r'(^|\n)\s*AWAY\s+([A-Z]+)', grs, flags=re.IGNORECASE)
if match:
    away = match.group(2)

match = re.search(r'(^|\n)\s*ADMIN\s+\w+', grs)
if match:
    admin = True

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
    try:
        ( s, c ) = cursor.fetchone()
        if not s:
            h_next = team[c]
    except:
        pass

    sql = "select scores, home from %s \
            where week = %i and away = '%s';"\
            % ( DB.sched, int(week) + 1, code[away] )
    cursor.execute(sql)
    try:
        ( s, c ) = cursor.fetchone()
        if not s:
            a_next = team[c]
    except:
        pass

    if debug:
        print("WEEK %s" % week)
        print("HOME %s next: %s" % ( home, h_next ))
        print("AWAY %s next: %s" % ( away, a_next ))

    if not admin:
        print(home, away, h_next, a_next)

