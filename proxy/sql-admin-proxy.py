#coding=utf-8

import re
import sys
import time
import pickle
from agileutil.db import DB
from decouple import config
from rpyc import Service  
from rpyc.utils.server import ThreadedServer
from agileutil.log import Log

log = Log(config('LOG_FILE'))


def test_conn(host, port, user, pwd):
    '''
    测试连接
    连接正常返回None
    否则返回错误信息
    '''
    try:
        db = DB(host, port, user, pwd, '')
        db.connect()
        time.sleep(0.2)
        db.close()
    except Exception, ex:
        return str(ex)
    return None

def test_privilege(host, port, user, pwd, dbname, onIp, is_grant = False):
    '''
    测试权限, super, process, replication slave
    具有这几个权限返回True, [] ,拥有的权限列表, None
    否则返回False, 缺少的权限, 拥有的权限列表, None
    出错返回False, [] ,[], 错误信息
    '''
    
    super_pirv = 'Super_priv'
    process_priv = 'Process_priv'
    repl_slav_priv = 'Repl_slave_priv'
    
    if onIp != '%':
        p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
        if not p.match(onIp): return False, [], [], "param onIp is invalid format"
    try:
        db = DB(host, port, user, pwd, '', ispersist=True)
        if is_grant:
            sql = "grant select on *.* to '%s'@'%s' identified by '%s' with grant option" % (user, onIp, pwd)
            db.update(sql)
            sql = "flush privileges"
            db.update(sql)
        '''
        sql = "select * from mysql.db where user='%s' and Db='%s' and Host='%s'" % (user, dbname, onIp)
        if dbname == '':
            sql = "select * from mysql.db where user='%s' and Host='%s'" % (user, onIp)
        '''
        sql = "select * from mysql.user where user='%s'" % (user)
        log.info("ready exec sql:" + sql)
        rows = db.query(sql)
        log.info('rows:' + str(rows))
        db.close()
        if rows == None or len(rows) == 0:
            return False, [process_priv, super_pirv, repl_slav_priv], [], None
        privileges = []
        row = rows[0]
        for k,v in row.items():
            if 'priv' in k:
                if v == 'Y':
                    privileges.append(k)
        log.info('all privileges:' + str(privileges))
        if process_priv in privileges and super_pirv in privileges and repl_slav_priv in privileges:
            return True, [], privileges, None
        else:
            lack_privileges = []
            if super_pirv not in privileges:
                lack_privileges.append(super_pirv)
            if process_priv not in privileges:
                lack_privileges.append(process_priv)
            if repl_slav_priv not in privileges:
                lack_privileges.append(repl_slav_priv)
            return False, lack_privileges, privileges, None
    except Exception, ex:
        return False, [], [], str(ex)

class ProxyService(Service):

    def exposed_test_conn(self, host, port, user, pwd):
        return test_conn(host, port, user, pwd)

    def exposed_test_privilege(self, host, port, user, pwd, dbname, onIp, is_grant=False):
        res =  test_privilege(host, port, user, pwd, dbname, onIp, is_grant)
        log.info("ret:" + str(res))
        ret = pickle.dumps(res)
        return ret        

port = int(config('PORT'))
if len(sys.argv) == 2: port = int(sys.argv[1])
st = ThreadedServer(ProxyService, port=port, auto_register=False)  
st.start()