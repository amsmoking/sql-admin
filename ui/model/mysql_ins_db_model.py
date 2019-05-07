#coding=utf-8

from common_model import *
import agileutil.date as dt

class MysqlInsDbModel(CommonModel):

    def __init__(self):
        CommonModel.__init__(self)
        self.tableName = 'mysql_ins_db'
        self.insId = 0
        self.dbName = ''
        self.doc = ''
        self.create_time = dt.current_time()

    def save(self):
        if self.id == 0:
            #create
            sql = "insert into %s(ins_id, db_name, doc, create_time) values(%s, '%s', '%s', '%s')" % (
                self.tableName, self.insId, self.dbName, self.escapeString(self.doc), dt.current_time())
        else:
            #update
            sql = "update %s set db_name='%s', doc='%s', ins_id=%s where id=%s" % (
                self.tableName, self.dbName, self.escapeString(self.doc), self.insId ,self.id)
        return self.update(sql)

    def isExists(self, ins_id, db_name):
        sql = "select * from mysql_ins_db where ins_id=%s and db_name='%s'" % (ins_id, db_name)
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return False
        else: return True

    def getInsDbByInsIdList(self, insIdList):
        sql = 'select * from mysql_ins_db where ins_id in (%s)' % ( ','.join([str(insId) for insId in insIdList]) )
        rows = self.query(sql)
        if rows == None or len(rows) == 0: rows = []
        return rows