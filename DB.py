#!/usr/bin/python

import os
import sys
import psycopg2

# tables for current season
starts = 'starts2015'
bat    = 'bat2015'
pit    = 'pit2015'
teams  = 'teams2015'
sched  = 'sched2015'
extra  = 'extra2015'
inj    = 'inj2015'

def connect():
    name='ibl_stats'
    user='ibl'

    try:
        import DBpasswd
        host = 'host=' + DBpasswd.host
        pwd = 'password=' + DBpasswd.pwd
    except ImportError:
        host=''
        pwd=''

    if 'IBL_DB' in os.environ.keys():
        name = os.environ.get('IBL_DB')
    if 'IBL_DB_USER' in os.environ.keys():
        user = os.environ.get('IBL_DB_USER')
    if 'IBL_DB_HOST' in os.environ.keys():
        host = 'host=' + os.environ.get('IBL_DB_HOST')
    if 'IBL_DB_PWD' in os.environ.keys():
        pwd = 'password=' + os.environ.get('IBL_DB_PWD')

    connstr = "dbname=%s user=%s %s %s" %\
            ( name, user, host, pwd )
    try:
        db = psycopg2.connect(connstr)
        return db

    except psycopg2.DatabaseError, err:
        print str(err)
        sys.exit(1)

