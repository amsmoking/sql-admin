#coding=utf-8

from common_model import *
import agileutil.date as dt

class DeptServerModel(CommonModel):

    def __init__(self):
        self.tableName = 'dept_server'
        self.deptId = 0
        self.serverId = 0
        self.createTime = dt.current_time()

    def getAllowServerIdsByDeptId(self, dept_id):
        sql = "select server_id from dept_server where dept_id=%s" % dept_id
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return []
        return [ row['server_id'] for row in rows ]
    
    def getServerByDeptId(self, dept_id):
        sql = "select * from dept_server where dept_id=%s" % dept_id
        rows = self.query(sql)
        if rows == None or len(rows) == 0:
            has_select_list = []
            sql = 'select * from mysql_server'
            rest_server_list = self.query(sql)
            return has_select_list, rest_server_list
        server_id_list = [str(row['server_id']) for row in rows]
        sql = 'select * from mysql_server where id in (%s)' % ','.join(server_id_list)
        has_select_list = self.query(sql)
        sql = 'select * from mysql_server where id not in (%s)' % ','.join(server_id_list)
        rest_server_list = self.query(sql)
        return has_select_list, rest_server_list

    def addDeptIdServerIds(self, dept_id, server_id_list):
        if server_id_list == None or len(server_id_list) == 0: return False
        sql = "insert into dept_server(dept_id, server_id) values"
        tmp_list = []
        for id in server_id_list:
            tmp_list.append("(%s, %s)" % (dept_id, id))
        tmp = ','.join(tmp_list)
        sql = sql + tmp
        print "sql", sql
        return self.update(sql)

    def delDeptIdServerIds(self, dept_id, server_id_list):
        if server_id_list == None or len(server_id_list) == 0: return False
        tmp_sql = ','.join([str(id) for id in server_id_list])
        sql = "delete from dept_server where dept_id=%s and server_id in (%s)" % (
            dept_id, tmp_sql
        )
        return self.update(sql)