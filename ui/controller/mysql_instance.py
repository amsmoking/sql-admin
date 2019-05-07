#coding=utf-8

from common import *
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../')
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from agileutil.db import DB
import time
import rpc.proxy as proxy
import logger.logger as log

class index(Admin):
    def handle(self):
        serverId = self.request('server_id')
        self.safeId(serverId)
        model = MysqlInstanceModel()
        rows = model.loadInstanceByServerId(serverId)
        self.data['rows'] = rows
        return self.render().my_ins_index(data = self.data)

'''
class test_conn(Admin):
    def handle(self):
        id = self.request('id')
        model = MysqlInstanceModel()
        row = model.load(id)
        server_info = MysqlServerModel().load(row['server_id'])
        hostname = server_info['hostname']
        ip = server_info['ip']
        remote_user = row['remote_user']
        remote_pwd = row['remote_pwd']
        port = int(row['port'])
        try:
            db = DB(ip, port, remote_user, remote_pwd, '')
            db.connect()
            time.sleep(1)
            db.close()
            return self.resp()
        except Exception, ex:
            return self.resp(errno=1, errmsg=str(ex))
'''

class test_conn(Admin):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        model = MysqlInstanceModel()
        row = model.load(id)
        server_info = MysqlServerModel().load(row['server_id'])
        hostname = server_info['hostname']
        ip = server_info['ip']
        remote_user = row['remote_user']
        remote_pwd = row['remote_pwd']
        port = int(row['port'])
        hostname_list = hostname.split('-')
        idc = hostname_list[0]
        err = proxy.test_conn(ip, port, remote_user, remote_pwd, idc)
        if err != None:
            return self.resp(errno=1, errmsg=err)
        else:
            return self.resp()

class test_privilege(Admin):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        model = MysqlInstanceModel()
        row = model.load(id)
        server_info = MysqlServerModel().load(row['server_id'])
        print row
        hostname = server_info['hostname']
        ip = server_info['ip']
        remote_user = row['remote_user']
        remote_pwd = row['remote_pwd']
        port = int(row['port'])
        hostname_list = hostname.split('-')
        idc = hostname_list[0]
        is_has_priv, lack_priv, has_priv, err = proxy.test_privilege(ip, port, remote_user, remote_pwd, '', ip, idc, is_grant = True)
        if err != None:
            log.error("first get privilege error:" + err)
            is_has_priv, lack_priv, has_priv, err = proxy.test_privilege(ip, port, remote_user, remote_pwd, '', ip, idc)
            if err != None:
                log.error("second get privilege error:" + err)
                if 'SELECT command denied to user' in err:
                    return self.resp(errno=1, errmsg='请先授予 SELECT 权限')
                return self.resp(errno=1, errmsg=err)
        if is_has_priv:
            is_has_priv = 1
        else:
            is_has_priv = 0
        for i in xrange(len(lack_priv)):
            lack_priv[i] = lack_priv[i].replace('_priv', '')
        for i in xrange(len(has_priv)):
            has_priv[i] = has_priv[i].replace('_priv', '')
        ret = {
            'is_has_priv' : is_has_priv,
            'lack_priv' : ', '.join(lack_priv),
            'has_priv' : ', '.join(has_priv),
        }
        return self.resp(data=ret)

class set_slave_info(Admin):
    def handle(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        slave_ip = self.request('slave_ip')
        slave_port = self.request('slave_port')
        if ins_id == '':
            return self.resp(errno=1, errmsg='ins_id is required')
        #if slave_ip == '':
        #    return self.resp(errno=2, errmsg='IP必填')
        if slave_ip != '':
            if self.isInvalidIp(slave_ip) == False:
                return self.resp(errno=3, errmsg='IP格式非法')
        if slave_port != '': 
            try:
                slave_port = int(slave_port)
            except:
                return self.resp(errno=4, errmsg='端口:0-65535')
            if slave_port >= 0 and slave_port <= 65535:
                pass
            else:
                return self.resp(errno=5, errmsg='端口:0-65535')
        if slave_port == '': slave_port = -1
        insModel = MysqlInstanceModel()
        insModel.setSlaveInfo(ins_id, slave_ip, slave_port)
        return self.resp()

class set_time_range(Admin):
    def handle(self):
        ins_id = self.req('ins_id')
        self.safeId(ins_id)
        time_range = self.req('time_range')
        if time_range == '': time_range = '-'
        allow_begin_time, allow_end_time = [item.strip() for item in  time_range.split('-')]
        MysqlInstanceModel().setTimeRange(ins_id, allow_begin_time, allow_end_time)
        return self.resp()