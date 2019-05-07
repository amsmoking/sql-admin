#coding=utf-8

import re
import web
from agileutil.webpy_base import WebPyBase
from decouple import config
import pickle
import sqlparse
import sys
sys.path.append('../')
import logger.logger as log
import model.inception as inc_util

class common(WebPyBase):

    def __init__(self):
        self.data = {}
        self.data['home_title']  = config('HOME_TITLE')
    
    def handle(self):
        return ''

    def isInvalidIp(self, ip):
        p = re.compile('^((25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(25[0-5]|2[0-4]\d|[01]?\d\d?)$')
        if p.match(ip):
            return True
        else:
            return False

    def assign(self, k, v):
        self.data[k] = v

    def getCurDepartList(self):
        dept_list = self.session('dept_list')
        return pickle.loads(dept_list)

    def setCurDepartList(self, dept_list):
        dept_list = pickle.dumps(dept_list)
        self.session('dept_list', dept_list)

    def formatSql(self, sql):
        if '\n' in sql: return sql
        formatSqlString = sqlparse.format(sql, reindent=True, keyword_case='upper')
        return formatSqlString

    def deny(self):
        return self.resp(errno=1, errmsg=u'您没有权限')

    def getIdcByHostname(self, hostname):
        return inc_util.getIdcByHostname(hostname)

    def getIncHostPortByIdc(self, idc):
        return inc_util.getIncHostPortByIdc(idc)

    def safeId(self, val):
        try:
            val = int(val)
        except:
            raise Exception('invalid request')
        if val < 0:
            raise Exception('invalid request')

    def req(self, k):
        return self.request(k)

class NoAuth(common):
    pass

class Auth(common):

    def __init__(self):
        common.__init__(self)
        self.data['session'] = {}
        self.auth()

    def handle(self):
        return ''

    def auth(self):
        domain_name = self.session('domain_name')
        role = self.session('role')
        if domain_name == '' or domain_name == None:
            #跳转到登录页面
            raise web.seeother('/user/login')
        self.data['session']['domain_name'] = domain_name
        self.data['session']['role'] = role
        #for test
        #self.data['role'] = 'admin'
        #self.data['session']['role'] = 'admin'
        #self.data['session']['role'] = 'guest'
        #self.session('domain_name', 'sunyukun')

class Admin(Auth):

    def __init__(self):
        Auth.__init__(self)
        if self.session('role') != 'admin':
            raise web.seeother('/mysql_change/index')

    def handle(self):
        return ''

class Guest(Auth):

    def __init__(self):
        Auth.__init__(self)

    def handle(self):
        return ''