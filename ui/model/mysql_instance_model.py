#coding=utf-8

from common_model import *
import agileutil.date as dt

class MysqlInstanceModel(CommonModel):

    def __init__(self):
        CommonModel.__init__(self)
        self.tableName = 'mysql_instance'
        #columons
        self.serverId = 0
        self.port = 3306
        self.rootPwd = ''
        self.remoteUser = ''
        self.remotePwd = ''
        self.createTime = ''
        self.remark = ''
        self.puller_status = ''
        self.puller_errmsg = ''

    def save(self):
        if self.id == 0:
            #create
            self.createTime = dt.current_time()
            sql = "insert into %s(server_id, port, root_pwd, create_time, remark, remote_user, remote_pwd) values('%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
                self.tableName, self.serverId, self.port, self.rootPwd, self.createTime, self.remark, self.remoteUser, self.remotePwd)
        else:
            #update
            sql = "update %s set server_id='%s', port='%s', root_pwd='%s', remark='%s', remote_user='%s', remote_pwd='%s' where id=%s" % (
                self.tableName, self.serverId, self.port, self.rootPwd, self.remark, self.remoteUser, self.remotePwd, self.id)
        return self.update(sql)

    def isInstanceExist(self, serverId, port):
        sql = "select count(*) as cnt from mysql_instance where server_id=%s and port=%s" % (serverId, port)
        rows = self.query(sql)
        if rows == None or len(rows) == 0:
            return False
        row = rows[0]
        cnt = row['cnt']
        if cnt <= 0: 
            return False
        return True

    def loadInstanceByServerId(self, serverId):
        sql = "select * from %s where server_id=%s" % (self.tableName, serverId)
        print sql
        rows = self.query(sql)
        if rows == None or len(rows) == 0:
            return []
        return rows

    def delInstancesByServerId(self, serverId):
        sql = "delete from mysql_instance where server_id=%s" % serverId
        print sql
        return self.update(sql)

    def loadDbsByInsId(self, insId):
        sql = "select * from mysql_ins_db where ins_id=%s" % insId
        return self.query(sql)

    def delDbsByInsId(self, insId, toDelDbList):
        sql = "delete from mysql_ins_db where ins_id=%s and db_name in (%s)" % (
            insId, ",".join([ "'" + db_name + "'" for db_name in toDelDbList ]) )
        return self.update(sql) 

    def updatePullerStatus(self):
        sql = "update %s set puller_status='%s', puller_errmsg='%s' where id=%s" % (
            self.tableName, self.puller_status, self.escapeString(self.puller_errmsg), self.id)
        return self.update(sql)

    def setSlaveInfo(self, id, slave_ip, slave_port):
        sql = "update %s set slave_ip='%s', slave_port=%s where id=%s" % (
            self.tableName, slave_ip, slave_port, id
        )
        return self.update(sql)

    def setTimeRange(self, id, allow_begin_time, allow_end_time):
        sql = "update %s set allow_begin_time='%s', allow_end_time='%s' where id=%s " % (
            self.tableName, allow_begin_time, allow_end_time, id
        )
        return self.update(sql)