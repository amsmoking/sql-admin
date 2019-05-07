#coding=utf-8

import sys
sys.path.append('../')
import db.mysql as mysql_db
import pymysql

class CommonModel:

    def __init__(self):
        self.tableName = ''
        #columns
        self.id = 0

    def query(self, sql):
        rows = mysql_db.query(sql)
        if rows == None or len(rows) == 0:
            return []
        return rows
    
    def escapeString(self, string):
        return pymysql.escape_string(string) 

    def update(self, sql):
        return mysql_db.update(sql)
    
    def load(self, id):
        sql = "select * from %s where id=%s" % (self.tableName, id)
        rows = self.query(sql)
        if rows == None or len(rows) == 0:
            return None
        row = rows[0]
        return row

    def delete(self, id):
        sql = "delete from %s where id=%s" % (self.tableName, id)
        return self.update(sql)

    def rows(self):
        sql = "select * from %s" % self.tableName
        items = self.query(sql)
        if items == None or len(items) == 0:
            return []
        return items

    def isColumnExists(self, where):
        sql = "select count(*) as cnt from %s %s" % (self.tableName, where)
        print "sql", sql
        rows = self.query(sql)
        print "rows", rows
        if rows == None or len(rows) == 0:
            return False
        row = rows[0]
        cnt = row['cnt']
        if cnt <= 0:
            return False
        else:
            return True

    def lastrowid(self):
        return mysql_db.lastrowid()

    def count(self):
        sql = "select count(*) as cnt from `%s`" % (self.tableName)
        rows = self.query(sql)
        row = rows[0]
        cnt = row['cnt']
        return cnt
