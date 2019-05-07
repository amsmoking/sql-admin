#coding=utf-8

import ldap
import sys
sys.path.append('../')
import logger.logger as log
import demjson

class LDAPApi(object):

    def __init__(self, ldapServer = 'ldap://127.0.0.1:389', ldapBind = '', ldapPass = '', version = ldap.VERSION3):
        self.ldapServer = ldapServer
        self.ldapBind = ldapBind
        self.ldapPass = ldapPass
        self.version =version
        self.conn = None
        
    def bind(self):
        self.conn = ldap.initialize(self.ldapServer)
        self.conn.protocal_version = self.version
        self.conn.simple_bind_s(self.ldapBind, self.ldapPass)

    def authUser(self, username, passwd):
        if username == '':
            return {}, u'用户名必填'
        if passwd == '':
            return {}, u'密码必填'
        if self.conn == None:
            try:
                self.bind()
            except ldap.SERVER_DOWN:
                return {}, u"无法连接到ldap"
            except ldap.INVALID_CREDENTIALS:
                return {}, u"绑定ldap错误"
            except:
                return {}, u"绑定ldap错误"
        searchScope = ldap.SCOPE_SUBTREE
        searchFilter = 'cn=' + username
        self.conn.search('OU=xueqiu,DC=xxx,DC=com', searchScope, searchFilter, None)
        result_type, result_data = self.conn.result(2, 0)
        if result_type != ldap.RES_SEARCH_ENTRY:
            return {}, u"不存在此用户"
        dic = result_data[0][1]
        log.info("user %s ldap info:%s" % (
            username,
            str(dic)
        ))
        distinguishedName = dic['distinguishedName'][0]
        newConn = ldap.initialize(self.ldapServer)
        newConn.protocal_version = self.version
        try:
            newConn.simple_bind_s(distinguishedName, passwd)
        except ldap.SERVER_DOWN:
            return {}, u"无法连接到ldap"
        except:
            return {}, u'密码错误'
        ret = {}
        ret['domain_name'] = dic['name'][0]
        ret['mail'] = dic['mail'][0]
        #ret['mobile'] = dic['mobile'][0]
        ret['mobile'] = ''
        ret['department'] = dic['memberOf'][-1].split(',')[0].split('=')[1]
        #ret['employ_no'] = dic['employeeNumber'][0]
        ret['employ_no'] = ''
        return ret, None
    
    def get_all_groups(self):
        if self.conn == None:
            try:
                self.bind()
            except ldap.SERVER_DOWN:
                return [], u"无法连接到ldap"
            except ldap.INVALID_CREDENTIALS:
                return [], u"绑定ldap错误"
            except:
                return [], u"绑定ldap错误"
        searchFilter = 'cn=*'
        searchScope = ldap.SCOPE_SUBTREE
        result_id = self.conn.search('OU=group,DC=xxxx,DC=com', searchScope, searchFilter, None)
        result_type, result_data = self.conn.result(result_id)
        ou_list = []
        for group in result_data:
            try:
                project = group[1]['project']
                if 'xsql' in project:
                    log.info("xsql in project, project:" + str(project))
                    ou = group[0].split(',')[0].split('=')[1]
                    ou_list.append(ou)
            except:
                pass
        ou_list = list(set(ou_list))
        return ou_list, None
    
    def get_all_group_dn_list(self):
        if self.conn == None:
            try:
                self.bind()
            except ldap.SERVER_DOWN:
                return [], u"无法连接到ldap"
            except ldap.INVALID_CREDENTIALS:
                return [], u"绑定ldap错误"
            except:
                return [], u"绑定ldap错误"
        searchFilter = 'cn=*'
        searchScope = ldap.SCOPE_SUBTREE
        result_id = self.conn.search('OU=group,DC=xxxxx,DC=com', searchScope, searchFilter, None)
        result_type, result_data = self.conn.result(result_id)
        ou_list = []
        for group in result_data:
            try:
                ou = group[0].split(',')[0].split('=')[1]
                ou_list.append(ou)
            except:
                pass
        ou_list = list(set(ou_list))
        return ou_list, None

    def getDepartMembers(self, dept):
        if self.conn == None:
            try:
                self.bind()
            except ldap.SERVER_DOWN:
                return [], u"无法连接到ldap"
            except ldap.INVALID_CREDENTIALS:
                return [], u"绑定ldap错误"
            except:
                return [], u"绑定ldap错误"
        searchFilter = 'cn=' + dept
        searchScope = ldap.SCOPE_SUBTREE
        result_id = self.conn.search('OU=group,DC=xxx,DC=com', searchScope, searchFilter, None)
        result_type, result_data = self.conn.result(result_id)
        user_list = []
        for item in result_data:
            try:
                member_list = item[1]['member']
                user_list = [ m.split(',')[0].split('=')[1] for m in member_list ]
                break
            except:
                pass
        return user_list, None

    def getUserDepartList(self, username):
        depart_en_list, err = self.get_all_groups()
        if err != None:
            return [], err
        try:
            depart_en_list.remove('all-user')
            depart_en_list.remove('developer')
        except:
            pass
        domain_name_dept_list_hash = {}
        for dept in depart_en_list:
            user_list, err = self.getDepartMembers(dept)
            if err == None:
                for u in user_list:
                    if domain_name_dept_list_hash.has_key(u):
                        domain_name_dept_list_hash[u].append(dept)
                    else:
                        domain_name_dept_list_hash[u] = []
                        domain_name_dept_list_hash[u].append(dept)
        if domain_name_dept_list_hash.has_key(username):
            return domain_name_dept_list_hash[username], None
        else:
            return [], None