#coding=utf-8

from common_model import *
import agileutil.date as dt

class UserModel(CommonModel):

    def __init__(self):
        self.tableName = 'user_info'
        self.domainName = ''
        self.mail = ''
        self.mobile = ''
        self.department = ''
        self.employNo = ''
        self.role = ''
        self.createTime = dt.current_time()

    def isUserExist(self, domainName):
        sql = "select count(domain_name) as cnt from %s where domain_name='%s'" % (self.tableName, domainName)
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return False
        row = rows[0]
        if row['cnt'] <= 0: return False
        else: return True

    def addUser(self):
        self.createTime = dt.current_time()
        sql = "insert into %s(domain_name, mail, mobile, department, employ_no, role, create_time)"\
        " values('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (self.tableName, self.domainName,self.mail, 
        self.mobile,self.department, self.employNo, self.role, self.createTime)
        return self.update(sql)

    def updateUserByDomainName(self, domainName):
        sql = "update %s set mobile='%s', department='%s', employ_no='%s',role='%s' where domain_name='%s'" % (
            self.tableName, self.mobile, self.department, self.employNo, self.role, domainName
        )
        return self.update(sql)

    def loadRoleByDomainName(self, domainName):
        sql = "select role from %s where domain_name='%s'" % (
            self.tableName,domainName)
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return ''
        row = rows[0]
        return row['role']

    def getAllAdminUsers(self):
        sql = "select * from %s where role='admin'" % self.tableName
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return []
        return rows