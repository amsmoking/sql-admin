#coding=utf-8

from common import *
from mysql_change import Permission
import sys
sys.path.append('../')
from model.mysql_server_model import MysqlServerModel
from model.grant import GrantModel
import demjson
import logger.logger as log

class index(Permission):
    def handle(self):
        mysql_server_list = MysqlServerModel().loadByIdList(self.data['allow_server_id_list'])
        self.data['mysql_server_list'] = mysql_server_list
        self.data['read_only_lower_priv_list'] = GrantModel.getReadOnlyLowerPrivList()
        self.data['read_write_lower_priv_list'] = GrantModel.getReadWriteLowerPrivList()
        self.data['all_lower_priv_list'] = GrantModel.getAllLowerPrivList()
        self.data['roll_service_list'] = GrantModel.getRollingServiceList()
        return self.render().grant_index(data=self.data)

class apply(Permission):

    PASS_TYPE_AUTO_GEN = 1
    PASS_TYPE_SPEC = 2
    
    def handle(self):
        reason = self.req('reason')
        if reason == '':
            return self.resp(errno=1, errmsg='请输入申请授权的原因')
        server_id = self.req('server_id')
        self.safeId(server_id)
        if server_id == '':
            return self.resp(errno=1, errmsg = '请选择MySQL')
        ins_id = self.req('ins_id')
        self.safeId(ins_id)
        if ins_id == '':
            return self.resp(errno=1, errmsg = '请选择端口实例')
        ins_db_id = self.req('ins_db_id')
        self.safeId(ins_db_id)
        if ins_db_id == '':
            return self.resp(errno=1, errmsg = '请选择库名')
        privilege = self.req('privilege')
        self.safeId(privilege)
        privilege = int(privilege)
        if privilege not in [GrantModel.PRIVILEGE_READONLY, GrantModel.PRIVILEGE_READWRITE, GrantModel.PRIVILEGE_ALL, GrantModel.PRIVILEGE_SELF_DEFINE]: raise 'invalid request'
        priv_list = self.req('priv_list')
        priv_list = priv_list.split(',')
        try:
            priv_list.remove('')
        except:
            pass
        if len(priv_list) == 0:
            return self.resp(errno=1, errmsg = '请选择权限')
        node_type = self.req('node_type')
        self.safeId(node_type)
        node_type = int(node_type)
        if node_type not in [GrantModel.NODE_10_10_RANGE, GrantModel.NODE_ROLLING, GrantModel.NODE_SELF_DEFINE]: raise 'invalid request'
        roll_service_name = self.req('roll_service_name')
        if node_type == GrantModel.NODE_ROLLING:
            if roll_service_name == '':
                return self.resp(errno=1, errmsg = '请选择rolling服务名')
        ips = self.req('ips')
        ips = ips.split('\n')
        ips = list(set(ips))
        try:
            ips.remove('')
        except:
            pass
        if len(ips) == 0:
            return self.resp(errno=1, errmsg = '请输入授权的IP, 每行一个')
        for ip in ips:
            if ',' in ip or ';' in ip:
                return self.resp(errno=1, errmsg = '每行一个IP')

        pass_type = self.req('pass_type')
        spec_user = self.req('spec_user')
        spec_pass = self.req('spec_pass')
        if pass_type == '': return self.resp(errno=1, errmsg = 'pass_type is required')
        pass_type = int(pass_type)
        if pass_type == self.PASS_TYPE_SPEC:
            if spec_user == '': return self.resp(errno=2, errmsg = 'spec_user is required')
            if spec_pass == '': return self.resp(errno=3, errmsg = "spec_pass is required")
            if len(spec_user) <= 4: return self.resp(errno=3, errmsg = "账号太短了，建议5-10位")
            if len(spec_user) >= 30: return self.resp(errno = 3, errmsg = "账号太长了，建议5-10位")
            if len(spec_pass) <= 4: return self.resp(errno=3, errmsg = "密码太短了，建议5-10位")
            if len(spec_pass) >= 100: return self.resp(errno = 3, errmsg = "密码太长了，建议5-10位复杂密码")

        dataMap = {
            'reason' : reason,
            'server_id' : server_id,
            'ins_id' : ins_id,
            'ins_db_id' : ins_db_id,
            'privilege' : privilege,
            'priv_list' : priv_list,
            'node_type' : node_type,
            'roll_service_name' : roll_service_name,
            'ips' : ips,
            'req_user' : self.session('domain_name'),
            'pass_type' : pass_type,
            'spec_user' : spec_user,
            'spec_pass' : spec_pass,
        }

        GrantModel().addGrantApply(dataMap)
            
        return self.resp()

class order(Guest):
    def handle(self):
        orderList = GrantModel().getGrantOrderList()
        print('order list:', orderList)
        self.data['orders'] = orderList
        if self.session('role') == 'admin':
            self.data['page_title'] = '授权审批'
        else:
            self.data['page_title'] = '授权记录'

        #for test
        #self.data["session"]["role"] = "guest"
        return self.render().grant_order(data = self.data)

class order_detail(Permission):
    def handle(self):
        order_id = self.request('order_id')
        self.safeId(order_id)
        order = GrantModel().loadGrantOrder(order_id)
        order['priv_str'] = ','.join(order['priv_list'])
        mysql_server_list = MysqlServerModel().loadByIdList(self.data['allow_server_id_list'])
        self.data['order'] = order
        self.data['mysql_server_list'] = mysql_server_list
        return self.render().grant_detail(data = self.data)

class grant(Guest):
    def handle(self):
        order_id = self.req('order_id')
        self.safeId(order_id)
        order = GrantModel().loadGrantOrder(order_id)
        try:
            GrantModel().grant(order)
        except Exception as ex:
            log.error("[grant] grant failed, order_id:%s, err:%s"  % (order_id, str(ex)) )
            GrantModel().setStatus(order_id, GrantModel.STATUS_FAILED)
            return self.resp(errno=1, errmsg = str(ex))
        GrantModel().setStatus(order_id, GrantModel.STATUS_SUCCED)
        return self.resp()

class del_order(Permission):
    def handle(self):
        order_id = self.req('order_id')
        self.safeId(order_id)
        GrantModel().deleteOrder(order_id)
        raise web.seeother('/grant/order')