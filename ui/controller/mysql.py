#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../')
from common import *
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
import agileutil.util as util
import logger.logger as log

class base(Admin):

    def toInsParams(self, ports, root_pwds, remote_users, remote_pwds, remarks):
        ports_list = ports.split(',')
        #root_pwds_list = root_pwds.split(',')
        remote_users_list = remote_users.split(',')
        remote_pwds_list = remote_pwds.split(',')
        remarks_list = remarks.split(',')
        ins_list = []
        for i in xrange(len(ports_list)):
            ins_list.append(
                {
                    'port' : ports_list[i].strip(),
                    'root_pwd' : '',
                    'remote_user' : remote_users_list[i].strip(),
                    'remote_pwd' : remote_pwds_list[i].strip(),
                    'remark' : remarks_list[i].strip()
                }
            )
        return ins_list

    def checkInsParamsEmpty(self, instance_params):
        if instance_params == None:
            return True
        for param in instance_params:
            try:
                port = int(param['port'])
                if port >= 0 and port <= 65535:
                    pass
                else:
                    return '端口必须为0-65535数字'
            except:
                return '端口必须为0-65535数字'
            port = param['port']
            root_pwd = param['root_pwd']
            remote_user = param['remote_user']
            remote_pwd = param['remote_pwd']
            remark = param['remark']
            if port == "":
                return u"请将mysql实例的端口填写完整"
            if remote_user == "":
                return u"请将远程执行用户填写完整"
            if remote_pwd == "":
                return u"请将远程执行密码填写完整"
        return ''

class index(base):
    def handle(self):
        local_ip_str = ''
        try:
            tmp_list = util.local_ipv4_list()
            local_ipv4_list = []
            for ip in tmp_list:
                if ip != '127.0.0.1':
                    local_ipv4_list.append(ip)
            local_ip_str = ','.join(local_ipv4_list)
        except Exception, ex:
            log.error("get local ip exception:" + str(ex))
        model = MysqlServerModel()
        rows = model.rows()
        self.data['rows'] = rows
        self.data['local_ip'] = local_ip_str
        return self.render().mysql_index(data = self.data)

class view(base):
    def handle(self):
        id = self.request('id')
        form = self.request('form')
        if form == 'edit':
            model = MysqlServerModel()
            row = model.load(id)
            myInsModel = MysqlInstanceModel()
            instances = myInsModel.loadInstanceByServerId(row['id'])
            ins_num= len(instances)
            if ins_num <= 0: ins_num = 1
            data = {'row':row, 'form':form, 'operate_zh':u'编辑', 'instances':instances, 'ins_num':ins_num}
            self.data = dict(self.data.items() + data.items())
        else:
            #add
            data = {'row':{}, 'form':form, 'operate_zh':u'添加', 'instances': [{
                'port' : '',
                'root_pwd' : '',
                'remote_user' : '',
                'remote_pwd' : '',
                'remark' : ''
            }], 'ins_num':1}
            self.data = dict(self.data.items() + data.items())
        return self.render().mysql_view(data=self.data)

class change(base):
    def handle(self):
        return self.render().mysql_change(self.data)

class delete(base):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        model = MysqlServerModel()
        model.delete(id)
        raise web.seeother('/mysql/index')

class edit(base):
    def handle(self):
        model = MysqlServerModel()
        model.id = self.request('id')
        model.hostname = self.request('hostname')
        try:
            idc = model.hostname.split('-')[0]
            if idc == 'bjxg' or idc == 'pingan':
                pass
            else:
                return self.resp(errno=1, errmsg='主机名必须以bjxg或pingan开头')
        except Exception, ex:
            return self.resp(errno=1, errmsg='主机名必须以bjxg或pingan开头')
        model.ip = self.request('ip')
        model.isp = self.request('isp')
        model.remark = self.request('remark')
        #mysql实例参数
        instance_count = int(self.request('instance_count'))
        ports = self.request('ports');
        root_pwds = self.request('root_pwds')
        remote_users = self.request('remote_users')
        remote_pwds = self.request('remote_pwds')
        remarks = self.request('remarks')
        if model.hostname == "":
            return self.resp(errno=1, errmsg=u"请填写主机名")
        if model.ip == "":
            return self.resp(errno=2, errmsg=u"请填写ip")
        if not self.isInvalidIp(model.ip):
            return self.resp(errno=3, errmsg=u"ip地址格式错误")
        if model.remark == "":
            return self.resp(errno=3, errmsg=u"请填写备注")
        #mysql实例参数转换成数组
        instance_params = self.toInsParams(ports, root_pwds, remote_users, remote_pwds, remarks)
        #检查参数是否有为空的
        errmsg = self.checkInsParamsEmpty(instance_params)
        if errmsg != "":
            return self.resp(errno=4, errmsg=errmsg)
        srcRow = model.load(model.id)
        if model.isHostnameExist():
            if srcRow['hostname'] == model.hostname:
                pass
            else:
                return self.resp(errno=5, errmsg=u'主机名已存在')
        if model.isIpExist():
            if srcRow['ip'] == model.ip:
                pass
            else:
                return self.resp(errno=6, errmsg=u'IP地址已存在')
        src_instances = model.loadInstances()
        model.save() 
        #删除旧的instance
        mysql_server_id = model.id
        MysqlInstanceModel().delInstancesByServerId(mysql_server_id)
        for param in instance_params:
            mysqlInsModel = MysqlInstanceModel()
            mysqlInsModel.serverId = mysql_server_id
            mysqlInsModel.port = int(param['port'])
            mysqlInsModel.rootPwd = param['root_pwd']
            mysqlInsModel.remark = param['remark']
            mysqlInsModel.remoteUser = param['remote_user']
            mysqlInsModel.remotePwd = param['remote_pwd']
            mysqlInsModel.save()
        return self.resp()

class add(base):
    def handle(self):
        model = MysqlServerModel()
        model.hostname = self.request('hostname')
        try:
            idc = model.hostname.split('-')[0]
            if idc == 'bjxg' or idc == 'pingan':
                pass
            else:
                return self.resp(errno=1, errmsg='主机名必须以bjxg或pingan开头')
        except Exception, ex:
            return self.resp(errno=1, errmsg='主机名必须以bjxg或pingan开头')
        model.ip = self.request('ip')
        model.isp = self.request('isp')
        model.remark = self.request('remark')
        #mysql实例参数
        instance_count = int(self.request('instance_count'))
        ports = self.request('ports');
        root_pwds = self.request('root_pwds')
        remote_users = self.request('remote_users')
        remote_pwds = self.request('remote_pwds')
        remarks = self.request('remarks')
        if model.hostname == "":
            return self.resp(errno=1, errmsg=u"请填写主机名")
        if model.ip == "":
            return self.resp(errno=2, errmsg=u"请填写ip")
        if not self.isInvalidIp(model.ip):
            return self.resp(errno=3, errmsg=u"ip地址格式错误")
        if model.remark == "":
            return self.resp(errno=3, errmsg=u"请填写备注")
        #mysql实例参数转换成数组
        instance_params = self.toInsParams(ports, root_pwds, remote_users, remote_pwds, remarks)
        #检查参数是否有为空的
        errmsg = self.checkInsParamsEmpty(instance_params)
        if errmsg != "":
            return self.resp(errno=4, errmsg=errmsg)
        if model.isHostnameExist():
            return self.resp(errno=5, errmsg=u'主机名已存在')
        if model.isIpExist():
            return self.resp(errno=6, errmsg=u'IP地址已存在')
        if model.save(): 
            mysql_server_id = model.lastrowid()
            for param in instance_params:
                mysqlInsModel = MysqlInstanceModel()
                mysqlInsModel.serverId = mysql_server_id
                mysqlInsModel.port = int(param['port'])
                mysqlInsModel.rootPwd = param['root_pwd']
                mysqlInsModel.remark = param['remark']
                mysqlInsModel.remoteUser = param['remote_user']
                mysqlInsModel.remotePwd = param['remote_pwd']
                mysqlInsModel.save()
            return self.resp()
        else: return self.resp(errno=4, errmsg=u'添加失败')