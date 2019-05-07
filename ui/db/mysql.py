#coding=utf-8

from agileutil.db import DB
from decouple import config

mysql_db = DB(
    config('DB_HOST'),
    int(config('DB_PORT')),
    config('DB_USER'),
    config('DB_PWD'),
    config('DB_NAME'),
    #ispersist = True,
    #is_mutex = True
)

def query(sql):
    return mysql_db.query(sql)

def update(sql):
    return mysql_db.update(sql)

def lastrowid():
    return mysql_db.lastrowid()