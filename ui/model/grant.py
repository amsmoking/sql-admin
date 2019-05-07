#coding=utf-8

import time
from common_model import *
import agileutil.date as dt
import sys
sys.path.append('../')
from db.mysql import mysql_db
from agileutil.db import Orm, DB
from decouple import config
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_ins_db_model import MysqlInsDbModel
import requests
import demjson
import hashlib
import logger.logger as log  

class GrantModel(CommonModel):
    
    PRIVILEGE_READONLY = 1 #只读
    PRIVILEGE_READWRITE = 2 #读写
    PRIVILEGE_ALL = 3 #所有
    PRIVILEGE_SELF_DEFINE = 4 #自定义

    NODE_10_10_RANGE = 1 #10.10 10.11网段
    NODE_ROLLING = 2 #rolling节点
    NODE_SELF_DEFINE = 3 #自定义节点

    STATUS_TO_GRANT = 0 #等待审核
    STATUS_SUCCED = 1 #授权成功
    STATUS_FAILED = 2 #授权失败
    
    PASS_TYPE_AUTO_GEN = 1
    PASS_TYPE_SPEC = 2
    
    '''
    hide those privileges:

    process 
    show databases
    reload
    replication client
    replication slave
    SHUTDOWN
    proxy
    trigger
    '''

    privList = [
        "ALTER",
        "ALTER ROUTINE",
        "CREATE",
        "CREATE ROUTINE",
        #"CREATE TABLESPACE",
        "CREATE TEMPORARY TABLES",
        #"CREATE USER",
        "CREATE VIEW",
        "DELETE",
        "DROP",
        "EVENT",
        "EXECUTE",  
        #"FILE",
        "GRANT OPTION",
        "INDEX",
        "INSERT",
        "LOCK TABLES",
        #"PROCESS",
        #"PROXY",
        "REFERENCES",
        #"RELOAD",
        #"REPLICATION CLIENT",
        #"REPLICATION SLAVE",
        "SELECT",
        #"SHOW DATABASES",
        "SHOW VIEW",
        #"SHUTDOWN",
        #"SUPER",
        #"TRIGGER",
        "UPDATE",
        "USAGE",
    ]

    readOnlyPriv = [
        "SHOW VIEW",
        "SELECT",
        #"SHOW DATABASES",
        #"PROCESS"
    ]

    readWritePriv = [
        "SHOW VIEW",
        "SELECT",
        #"SHOW DATABASES",
        #"PROCESS",

        "UPDATE",
        "INSERT",
        "EXECUTE",
        "DELETE",
    ]

    allPriv = "ALL PRIVILEGES"

    def __init__(self):
        self.tableName = 'grant_apply'

    @classmethod
    def getLowerPrivList(cls):
        ret = []
        for priv in cls.privList:
            ret.append(priv.lower())
        return ret

    @classmethod
    def getUpperPrivList(cls):
        ret = []
        for priv in cls.privList:
            ret.append(priv.upper())
        return ret

    @classmethod
    def getLowerUpperPrivHash(cls):
        ret = {}
        for priv in cls.privList:
            lower = priv.lower()
            upper = priv.upper()
            ret[lower] = upper
        return ret
    
    @classmethod
    def getUpperLowerPrivHash(cls):
        ret = {}
        for priv in cls.privList:
            lower = priv.lower()
            upper = priv.upper()
            ret[upper] = lower
        return ret

    @classmethod
    def getReadOnlyLowerPrivList(cls):
        ret = []
        for priv in cls.readOnlyPriv:
            ret.append(priv.lower())
        return ret

    @classmethod
    def getReadOnlyUpperPrivList(cls):
        ret = []
        for priv in cls.readOnlyPriv:
            ret.append(priv.upper())
        return ret

    @classmethod
    def getReadWriteLowerPrivList(cls):
        ret = []
        for priv in cls.readWritePriv:
            ret.append(priv.lower())
        return ret

    @classmethod
    def getReadWriteUpperPrivList(cls):
        ret = []
        for priv in cls.readWritePriv:
            ret.append(priv.upper())
        return ret

    @classmethod
    def getAllLowerPrivList(cls):
        return cls.getLowerPrivList()

    @classmethod
    def getAllUpperPrivList(cls):
        return cls.getUpperPrivList()

    @classmethod
    def getRollingContainerMapList(cls):
        url = config('CONTAINERS_URL')
        r = requests.get(url)
        code = r.status_code
        output = r.text
        begin_pos = output.find('<tbody>', 0)
        end_pos = output.find('</tbody>', begin_pos)
        tbody = output[begin_pos:end_pos]
        lines = tbody.split('\n')
        trList = []
        tr = ''
        for line in lines:
            line = line.strip()
            if line == '<tr>':
                tr = ''
            elif line == '</tr>':
                trList.append(tr)
            else:
                tr = tr + line
        containerMapList = []
        for tr in trList:
            tdList = [ item.replace('<td>', '').replace('</td>', '') for item in tr.split('</td><td>') ]
            hostname, env, service_name, container_ip, container_id = tdList
            containerMapList.append({
                'hostname' : hostname,
                'env' : env,
                'service_name' : service_name,
                'container_ip' : container_ip,
                'container_id' : container_id
            })
        return containerMapList

    @classmethod
    def getRollingServiceList(cls):
        containerMapList = cls.getRollingContainerMapList()
        serviceNameList = [ cmap['service_name'] for cmap in containerMapList ]
        serviceNameList = list(set(serviceNameList))
        return serviceNameList

    @classmethod
    def getRollingServiceContainerMapListHash(cls):
        serviceMapHash = {}
        for containerMap in cls.getRollingContainerMapList():
            serviceName = containerMap['service_name']
            if not serviceMapHash.has_key(serviceName):
                serviceMapHash[serviceName] = []
            serviceMapHash[serviceName].append(containerMap)
        return serviceMapHash

    @classmethod
    def getRollingServiceEnvContainerMapListHash(cls):
        serviceMapHash = cls.getRollingServiceContainerMapListHash()
        newHash = {}
        for serviceName, containerMapList in serviceMapHash.items():
            if not newHash.has_key(serviceName):
                newHash[serviceName] = {}
            for containerMap in containerMapList:
                env = containerMap['env']
                if not newHash[serviceName].has_key(env):
                    newHash[serviceName][env] = []
                newHash[serviceName][env].append(containerMap)
        return newHash
    
    @classmethod
    def getRollNodesByServiceNameEnv(cls, serviceName, env):
        nodes = []
        serviceEnvContainerMapListHash = cls.getRollingServiceEnvContainerMapListHash()
        if not serviceEnvContainerMapListHash.has_key(serviceName):
            return nodes
        EnvContainerMapListHash = serviceEnvContainerMapListHash[serviceName]
        if not EnvContainerMapListHash.has_key(env):
            return nodes
        containerMapList = EnvContainerMapListHash[env]
        
        for m in containerMapList:
            container_ip = m['container_ip']
            nodes.append(container_ip)
        return nodes

    @classmethod
    def getAllRollNodesByServiceNameEnv(cls, serviceName):
        nodes = []
        sepNodes = cls.getRollNodesByServiceNameEnv(serviceName, 'sep')
        print('sep nodes', sepNodes)
        rcNodes = cls.getRollNodesByServiceNameEnv(serviceName, 'rc')
        print('rc nodes', rcNodes)
        releaseNodes = cls.getRollNodesByServiceNameEnv(serviceName, 'release')
        print('release nodes', releaseNodes)
        prodNodes = cls.getRollNodesByServiceNameEnv(serviceName, 'production')
        print('prod nodes', prodNodes)
        nodes.extend(sepNodes)
        nodes.extend(rcNodes)
        nodes.extend(releaseNodes)
        nodes.extend(prodNodes)
        return nodes

    def addGrantApply(self, dataMap):
        if isinstance(dataMap['priv_list'], list):
            dataMap['priv_list'] = ','.join(dataMap['priv_list'])
        if isinstance(dataMap['ips'], list):
            dataMap['ips'] = ','.join(dataMap['ips'])
        return Orm(mysql_db).table(self.tableName).data(dataMap).insert();

    def getPrivilegeZh(self, privilege):
        privilege_zh = ''
        if privilege == GrantModel.PRIVILEGE_READONLY:
            privilege_zh = u'只读'
        elif privilege == GrantModel.PRIVILEGE_READWRITE:
            privilege_zh = u'读写'
        elif privilege == GrantModel.PRIVILEGE_ALL:
            privilege_zh = u'所有'
        else:
            privilege_zh = u'自定义'
        return privilege_zh

    def getStatusZh(self, status):
        status_zh = ''
        if status == self.STATUS_TO_GRANT:
            status_zh = '待审核'
        if status == self.STATUS_SUCCED:
            status_zh = '授权成功'
        if status == self.STATUS_FAILED:
            status_zh = '授权失败'
        return status_zh

    def getNodeZh(self, nodeType):
        nodeZh = ''
        if nodeType == self.NODE_10_10_RANGE:
            nodeZh = u'10.10/10.11网段'
        elif nodeType == self.NODE_ROLLING:
            nodeZh = u'rolling节点'
        else:
            nodeZh = u'自定义'
        return nodeZh

    def getGrantOrderList(self):
        orderList = self.rows()
        serverList = MysqlServerModel().rows()
        idServerHash = {}
        for server in serverList:
            id = server['id']
            idServerHash[id] = server
        for order in orderList:
            server_id = order['server_id']
            if idServerHash.has_key(server_id):
                order['server'] = idServerHash[server_id]
            else:
                order['server'] = {} 
            status = order['status']
            order['status_zh'] = self.getStatusZh(status)
            privilege = order['privilege']
            order['privilege_zh'] = self.getPrivilegeZh(privilege)
            order['node_zh'] = self.getNodeZh(order['node_type'])
        return orderList    

    def loadGrantOrder(self, orderId):
        order = self.load(orderId)
        order['priv_list'] = order['priv_list'].split(',')
        order['ips'] = '\n'.join( order['ips'].split(',') )
        order['server'] = MysqlServerModel().load(order['server_id'])
        order['instance'] = MysqlInstanceModel().load(order['ins_id'])
        order['db'] = MysqlInsDbModel().load(order['ins_db_id'])
        return order

    def genPassword(self, orderId, dbName):
        src = str(orderId) + str(dbName)
        m2 = hashlib.md5()
        m2.update(src)
        return m2.hexdigest()

    def grant(self, order):
        dbHost = order['server']['ip']
        dbPort = int(order['instance']['port'])
        dbUser = order['instance']['remote_user']
        dbPwd = order['instance']['remote_pwd']
        dbName = order['db']['db_name']
        priv_list = order['priv_list']
        db = DB(dbHost, dbPort, dbUser, dbPwd, dbName, ispersist = True)
        passType = order['pass_type']
        specUser = order['spec_user']
        specPass = order['spec_pass']

        username = ''
        password = ''
        if passType == self.PASS_TYPE_AUTO_GEN:
            #生成用户名密码
            username = dbName.lower()
            password = self.genPassword(order['id'], dbName)
        elif passType == self.PASS_TYPE_SPEC:
            username = specUser
            password = specPass
        else:
            pass

        #开始授权
        priv_str = ','.join(priv_list)
        ips = [ item.strip() for item in order['ips'].split('\n') ]
        log.info("[grant] ready to grant, order_id:%s, db_host:%s, db_port:%s, db_user:%s, db_name:%s, priv_list:%s, ips:%s, gen username:%s, gen password:%s" % (
            order['id'], dbHost, dbPort, dbUser, dbName,str(priv_list),str(ips), username, password
        ))
        for ip in ips:
            sql = "grant %s on `%s`.* to '%s'@'%s' identified by '%s' with grant option" % (
                priv_str, dbName, username, ip, password
            )
            log.info("[grant] ready to exec sql: " + sql)
            db.update(sql)
            log.info("[grant] exec one sql")
        sql = "flush privileges"
        db.update(sql)
        log.info("[grant] flush privileges finish")
        GrantModel().setAccountInfo(order['id'], username, password)
        log.info("write account info to db succed")
        log.info("[grant] grant succed")

    def setStatus(self, order_id, status):
        return Orm(mysql_db).table(self.tableName).data({'status' : int(status)}).where('id', int(order_id)).update()

    def setAccountInfo(self, order_id, username, password):
        return Orm(mysql_db).table(self.tableName).data({
            'username' : username,
            'password' : password
        }).where('id', int(order_id)).update()

    def deleteOrder(self, order_id):
        return Orm(mysql_db).table(self.tableName).where('id', int(order_id)).delete()