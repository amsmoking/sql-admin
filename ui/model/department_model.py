#coding=utf-8

from common_model import *
import agileutil.date as dt

class DepartmentModel(CommonModel):

    def __init__(self):
        self.tableName = 'department'
        self.zhName = ''
        self.enName = ''
        self.createTime = dt.current_time()

    def addEnDepartments(self, dept_list):
        if dept_list == None or len(dept_list) == 0: return False
        for en_name in dept_list:
            sql = "insert into department(zh_name, en_name) values('', '%s')" % en_name
            self.update(sql)
        return True

    def loadByEnName(self, en_name):
        sql = "select * from department where lower(en_name) = lower('%s')" % en_name
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return None
        return rows[0]
