#coding=utf-8

from common import *
from decouple import config
import sys
sys.path.append("../")
from auth.ldap_auth import LDAPApi
from model.user_model import UserModel
from agileutil.log import Log
import notify.notify as notify
import logger.logger as log

class login(common):
    def handle(self):
        domain_name = self.session('domain_name')
        if domain_name != '' and domain_name != None:
            raise web.seeother('/')
        return self.render().user_login(data=self.data)

class logout(Auth):
    def handle(self):
        self.kill_session()
        raise web.seeother('/')

class auth(common):
    def handle(self):
        domain_name = self.session('domain_name')
        if domain_name != '' and domain_name != None:
            raise web.seeother('/')
        domain_name = self.request('domain_name')
        password = self.request('password')
        #log.info("user try to login, domain_name:%s, passwd:%s" % (domain_name, password))
        log.info("user try to login, domain_name:%s" % (domain_name))
        ldapApi = LDAPApi(ldapServer=config('LDAP_SERVER'), ldapBind=config('LDAP_BIND'), ldapPass=config('LDAP_PASS'))
        user_info, err = ldapApi.authUser(domain_name, password)
        if err != None:
            return self.resp(errno=1, errmsg=err)
        domain_name = user_info['domain_name']
        mail = user_info['mail']
        mobile = user_info['mobile']
        #department = user_info['department']
        depart_list , _ = ldapApi.getUserDepartList(domain_name)
        employ_no = user_info['employ_no']
        role = ''
        #判断用户是否存在，不存在则创建用户，存在则更新用户的信息
        userModel = UserModel()
        userModel.domainName = domain_name
        userModel.mail = mail
        userModel.mobile = mobile
        if len(depart_list) > 0:
            userModel.department = depart_list[0]
        userModel.employNo = employ_no
        if userModel.isUserExist(user_info['domain_name']):
            role = userModel.loadRoleByDomainName(user_info['domain_name'])
            userModel.role = role
            userModel.updateUserByDomainName(user_info['domain_name'])
        else:
            userModel.addUser()
        #设置session
        self.session('domain_name', domain_name)
        self.session('mail', mail)
        self.session('mobile', mobile)
        self.setCurDepartList(depart_list)
        self.session('employ_no', employ_no)
        #如果是sre组的，默认设为管理员
        if 'sre' in depart_list or 'SRE' in depart_list: role = 'admin'
        self.session('role', role)
        #这里存个密码用于之后调用jira api
        self.session('password', password)
        return self.resp()

class add_feedback(common):
    def handle(self):
        text = self.request('text')
        user = ''
        try:
            user = self.session('domain_name')
        except:
            pass
        notify.send_alarm('xsql', '[feedback] user:%s, text:%s' % (user, text))
        try:
            log = Log('/var/log/sql-admin/feedback')
            log.info('[feedback] user:%s, text:%s' % (user, text))
        except:
            pass
        return self.resp()