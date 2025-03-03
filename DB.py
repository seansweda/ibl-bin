#!/usr/bin/env python

import os
import sys
import psycopg2

# tables for current season
starts = 'starts2025'
bat    = 'bat2025'
pit    = 'pit2025'
teams  = 'teams2025'
sched  = 'sched2025'
extra  = 'extra2025'
inj    = 'inj2025'
usage  = 'usage2025'


def bin_dir():
    return os.path.dirname( os.path.realpath(__file__) )

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

    if 'IBL_DB' in list(os.environ.keys()):
        name = os.environ.get('IBL_DB')
    if 'IBL_DB_USER' in list(os.environ.keys()):
        user = os.environ.get('IBL_DB_USER')
    if 'IBL_DB_HOST' in list(os.environ.keys()):
        host = 'host=' + os.environ.get('IBL_DB_HOST')
    if 'IBL_DB_PWD' in list(os.environ.keys()):
        pwd = 'password=' + os.environ.get('IBL_DB_PWD')

    connstr = "dbname=%s user=%s %s %s" %\
            ( name, user, host, pwd )
    try:
        db = psycopg2.connect(connstr)
        db.set_client_encoding("utf-8")
        return db

    except psycopg2.DatabaseError as err:
        print(str(err))
        sys.exit(1)

