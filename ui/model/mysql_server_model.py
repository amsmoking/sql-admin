#coding=utf-8

from common_model import *
import agileutil.date as dt

class MysqlServerModel(CommonModel):

    def __init__(self):
        CommonModel.__init__(self)
        self.tableName = 'mysql_server'
        #columons
        self.hostname = ''
        self.ip = ''
        self.isp = ''
        self.create_time = ''
        self.remark = ''

    def save(self):
        if self.id == 0:
            #create
            self.create_time = dt.current_time()
            sql = "insert into %s(hostname, ip, isp, create_time, remark) values('%s', '%s', '%s', '%s', '%s')" % (
                self.tableName, self.hostname, self.ip, self.isp, self.create_time, self.remark)
        else:
            #update
            sql = "update %s set hostname='%s', ip='%s', isp='%s', remark='%s' where id=%s" % (
                self.tableName, self.hostname, self.ip, self.isp, self.remark, self.id)
        return self.update(sql)

    def isHostnameExist(self):
        return self.isColumnExists("where hostname='%s'" % self.hostname)

    def isIpExist(self):
        return self.isColumnExists("where ip='%s'" % self.ip)

    def loadInstances(self):
        sql = "select * from mysql_instance where server_id=%s" % self.id
        rows = self.query(sql)
        if rows == None or len(rows) == 0:
            return []
        return rows

    def delete(self, id):
        '''
        同时删除拥有的mysql实例，实例对应的数据库
        '''
        insList = self.loadInstances()
        insIdList = [ str(ins['id']) for ins in insList]
        sql = "delete from mysql_server where id=%s" % id
        self.update(sql)
        sql = "delete from mysql_instance where server_id=%s" % id
        self.update(sql)
        if len(insIdList) > 0:
            sql = "delete from mysql_ins_db where ins_id in (%s)" % ','.join(insIdList)
            self.update(sql)
        return True

    def loadServerByIpList(self, sel_ip_list):
        if sel_ip_list == None or len(sel_ip_list) == 0: return []
        sql = "select * from mysql_server where ip in (%s)" % ','.join([ "'" + ip + "'" for ip in sel_ip_list ])
        return self.query(sql)

    def loadByIdList(self, id_list = []):
        if id_list == None or len(id_list) == 0: return []
        sql = "select * from mysql_server where id in (%s)" % ','.join([str(id) for id in id_list])
        print self.query(sql)
        return self.query(sql)