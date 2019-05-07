#coding=utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf8')
sys.path.append('../')
from common import *
from decouple import config
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_ins_db_model import MysqlInsDbModel
from model.dept_server_model import DeptServerModel
from model.department_model import DepartmentModel
from model.order import OrderModel, ORDER_STATUS_NO_COMMIT, ORDER_STATUS_AGREE_FAILED
from model.query_history_model import QueryHistoryModel
from sql_checker.inception import Inception
import logger.logger as log
import notify.notify as notify
from db.mysql import mysql_db
from agileutil.db import Orm

class Permission(Guest):
    '''
    在除了检查admin权限之外，检查有权限查看的myql
    '''

    def __init__(self):
        Guest.__init__(self)
        if self.session('role') != 'admin' and config('OPEN_PRIV_TO_GUEST') != 'true':
            dept_list = self.getCurDepartList()
            allow_server_id_list = []
            deptServerModel = DeptServerModel()
            for dept in dept_list:
                depart = DepartmentModel().loadByEnName(dept)
                dept_id = depart['id']
                tmp_list = deptServerModel.getAllowServerIdsByDeptId(dept_id)
                for item in tmp_list:
                    allow_server_id_list.append(item)
            allow_server_id_list = list(set(allow_server_id_list))
            self.data['allow_server_id_list'] = allow_server_id_list
        else:
            self.data['allow_server_id_list'] = [item['id'] for item in MysqlServerModel().rows()]

    def checkPermission(self):
        order_id = 0
        if self.request('order_id') != '':
            order_id = self.request('order_id')
            order = OrderModel().load(order_id)
            if order['order_status'] != ORDER_STATUS_NO_COMMIT and order['order_status'] != ORDER_STATUS_AGREE_FAILED:
                return False
        return True

    def isCanSave(self):
        return self.checkPermission()

    def isCanCommit(self):
        return self.checkPermission()

    def handle(self):
        pass

class index(Permission):
    def handle(self):
        mysql_server_list = MysqlServerModel().loadByIdList(self.data['allow_server_id_list'])
        self.data['mysql_server_list'] = mysql_server_list
        order_id = self.request('order_id')
        self.data['order'] = {}
        if order_id != '':
            self.safeId(order_id)
            orderModel = OrderModel()
            order = orderModel.load(order_id)
            order['sql'] = self.formatSql(order['sql'])
            self.data['order'] = order
        return self.render().mysql_change2(data=self.data)

class query_index(Permission):
    def handle(self):
        mysql_server_list = MysqlServerModel().loadByIdList(self.data['allow_server_id_list'])
        queryHistoryModel = QueryHistoryModel()
        self.data['mysql_server_list'] = mysql_server_list
        self.data['page_title'] = '在线查询'
        self.data['query_history'] = queryHistoryModel.getQueryHistory(self.session('domain_name'))
        allow_export_user_list = config('ALLOW_EXPORT_USERS').split(',')

        if config('IS_CHECK_ALL_PERMI') == 'false':
            self.data['show_export'] = 'true'
        else:
            if self.session('domain_name') in allow_export_user_list:
                self.data['show_export'] = 'true'
            else:
                self.data['show_export'] = 'false'
        return self.render().query_index(data = self.data)

class save(Permission):
    def handle(self):
        if self.isCanSave() == False:
            return self.deny()
        server_id = self.request('server_id')
        self.safeId(server_id)
        ins_id = self.request('ins_id')
        ins_db_id = self.request('ins_db_id')
        sql = self.request('sql')
        if len(sql) > 30000: return self.resp(errno=1, errmsg='SQL长度大于30000')
        src_sql = self.request('sql')
        sel_ip = self.request('sel_ip')
        sel_port = self.request('sel_port')
        sel_db_name = self.request('sel_db_name')
        reason = self.request('reason')
        serverModel = MysqlServerModel()
        instanceModel = MysqlInstanceModel()
        insDbModel = MysqlInsDbModel()
        server = serverModel.load(server_id)
        instance = instanceModel.load(ins_id)
        insDb = insDbModel.load(ins_db_id)
        optHost = server['ip']
        optPort = instance['port']
        optUser = instance['remote_user']
        optPwd = instance['remote_pwd']
        dbName = insDb['db_name']
        sql = "use `%s`;%s" % (dbName, sql)

        #在这里添加到申请表中，等待管理员审核
        order = OrderModel()
        order_status = None
        order_id = 0
        req_user = self.session('domain_name')
        if self.request('order_id') != '':
            order_id = self.request('order_id')
            tmp = order.load(order_id)
            if tmp:
                #已经存在了，可能是执行失败再编辑,这里获取原来的状态,获取原来的申请人
                order_status = tmp['order_status']
                req_user = tmp['req_user']
        order.id = order_id
        order.serverId = server_id
        order.insId = ins_id
        order.insDbId = ins_db_id
        order.sql = src_sql
        order.selIp = sel_ip
        order.selPort = sel_port
        order.selDbName = sel_db_name
        order.reason = reason
        order.reqUser = req_user
        if order_status:
            order.orderStatus = order_status
        else:
            order.orderStatus = ORDER_STATUS_NO_COMMIT
        order.save()
        return self.resp()

class commit(Permission):
    def handle(self):
        '''
        错误码：
        0.没有警告，没有错误，审核通过，提交到后台中
        1.执行sql检查发生了异常，mysql连接不上等原因，用户名密码不对等
        2.有警告，无错误
        3.无警告，有错误
        4.有警告，有错误
        5.保存失败
        6.无警告，无错误，影响的行数有超过阀值的
        '''
        
        '''
        order_id = 0
        if self.request('order_id') != '':
            order_id = self.request('order_id')
            order = OrderModel().load(order_id)
            if order['order_status'] != ORDER_STATUS_NO_COMMIT:
                return self.deny()
        '''
        if self.isCanCommit() == False:
            return self.deny()
        server_id = self.request('server_id')
        self.safeId(server_id)
        ins_id = self.request('ins_id')
        ins_db_id = self.request('ins_db_id')
        sql = self.request('sql')
        if len(sql) > 30000: return self.resp(errno=1, errmsg='SQL长度大于30000')
        src_sql = self.request('sql')
        sel_ip = self.request('sel_ip')
        sel_port = self.request('sel_port')
        sel_db_name = self.request('sel_db_name')
        reason = self.request('reason')
        serverModel = MysqlServerModel()
        instanceModel = MysqlInstanceModel()
        insDbModel = MysqlInsDbModel()
        server = serverModel.load(server_id)
        instance = instanceModel.load(ins_id)
        insDb = insDbModel.load(ins_db_id)
        optHost = server['ip']
        optPort = instance['port']
        optUser = instance['remote_user']
        optPwd = instance['remote_pwd']
        dbName = insDb['db_name']
        sql = "use `%s`;%s" % (dbName, sql) 

        idc, _ = self.getIdcByHostname(server['hostname'])
        inc_host, inc_port = self.getIncHostPortByIdc(idc)

        inc = Inception(
            host = inc_host,
            port = inc_port,
            optHost = optHost,
            optPort = optPort,
            optUser = optUser,
            optPwd = optPwd
        )

        idc, err = self.getIdcByHostname(server['hostname'])
        if err == None: inc.Idc = idc
        inc.curDb = dbName
        inc.curUserRole = self.session('role')
        resultSet = None
        try:
            resultSet = inc.check(sql)
        except Exception, ex:
            log.error("when check:" + str(ex))
            return self.resp(errno=1, errmsg=str(ex))
        if resultSet == None:
            return self.resp(errno=1, errmsg="resultSet is None") 
        ret = {
            'advice' : '',
            'warning' : '',
            'error' : '',
            'sql' : sql,
            'affect_rows_exceed_sql' : '',
            'affect_rows_exceed_cnt' : 0,
            'affect_rows_exceed_limit' : 0,
            'affect_rows_info' : '',
            'total_info_str' : '',
            'format_sql' : self.formatSql(src_sql)
        }
        errno = 0
        warnTag = resultSet.isHasWarning()
        errorTag = resultSet.isHasError()

        if config('SQL_CHECK') == 'false':
            warnTag = False
            errorTag = False

        if warnTag and errorTag:
            #有警告，有错误
            #这种情况只显示错误，用户先修正错误
            errno = 4
            ret['error'] = resultSet.errorsStr()
            return self.resp(errno=errno, data=ret, errmsg=ret['error'])
        elif warnTag and errorTag == False:
            #有警告，无错误
            errno = 2
            ret['warning'] = resultSet.warningsStr()
            return self.resp(errno=errno, data=ret, errmsg=ret['warning'])
        elif warnTag == False and errorTag:
            #无警告，有错误
            errno = 3
            ret['error'] = resultSet.errorsStr() 
            return self.resp(errno=errno, data=ret, errmsg=ret['error'])
        else:
            #审核通过，无警告，无错误

            #判断影响的行数是否有超过阀值的,这个配置一般不开启
            if config('IS_CHECK_AFFECT_ROWS') == 'true':
                affect_rows_limit = config('AFFECT_ROWS_LIMIT', cast=int)
                ret['affect_rows_exceed_limit'] = affect_rows_limit
                if resultSet.isAffectRowsExceedLimit(affect_rows_limit):
                    #影响的行数超过了阀值, 得到超过阀值的sql
                    affect_rows_exceed_sql,affect_rows_exceed_cnt  = resultSet.getAffectRowsExceedLimitSql(affect_rows_limit)
                    ret['affect_rows_exceed_sql'] = affect_rows_exceed_sql
                    ret['affect_rows_exceed_cnt'] = affect_rows_exceed_cnt
                    errno = 6
                    return self.resp(errno=errno, data=ret)

            errno = 0
            #在这里添加到申请表中，等待管理员审核
            req_user = self.session('domain_name')
            order = OrderModel()
            if self.request('order_id') != '':
                order.id = self.request('order_id')
                row = order.load(self.request('order_id'))
                req_user = row['req_user']
            order.serverId = server_id
            order.insId = ins_id
            order.insDbId = ins_db_id
            order.sql = src_sql
            order.selIp = sel_ip
            order.selPort = sel_port
            order.selDbName = sel_db_name
            order.reason = reason
            order.reqUser = req_user
            order.combiInfo = resultSet.getCombiInfoString()
            if order.save():
                #通知管理员
                try:
                    order_id = order.lastrowid()
                    if self.request('order_id') != '': order_id = self.request('order_id')
                    log.info("lastrowid:" + str(order_id))
                    if config('JIRA_ENABLE') == 'true':
                        notify.notify_jira(order_id, self.session('domain_name'), self.session('password'))
                except Exception, ex:
                    log.error("send notify to admin exception:" + str(ex))
                return self.resp(data=ret)
            else:
                return self.resp(errno=5, errmsg=u'保存失败')

class upload(Permission):
    def handle(self):
        data = web.input()
        print 'web.input', data.keys()
        if data.has_key('file'):
            try:
                file_content = unicode(data['file'])
            except:
                try:
                    file_content = str(data['file'])
                except:
                    file_content = data['file']
            sql = self.formatSql(file_content)
            ret = {'errno' : 0, 'errmsg' : '', 'data' : unicode(sql)}
            import demjson
            return demjson.encode(ret)
        else:
            return self.resp(errno=1)