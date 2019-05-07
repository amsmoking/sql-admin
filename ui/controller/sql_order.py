#coding=utf-8

import sys
sys.path.append('../')
from common import *
from model.order import OrderModel
from model.order import ORDER_STATUS_NO_VIEW
from model.order import ORDER_STATUS_CANCEL
from model.order import ORDER_STATUS_AGREE_SUCCED
from model.order import ORDER_STATUS_AGREE_FAILED
from model.order import ORDER_STATUS_ASYNC_EXEC
from model.order import ORDER_STATUS_NO_COMMIT
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_server_model import MysqlServerModel
from model.mysql_ins_db_model import MysqlInsDbModel
from model.sql_task_model import SqlTaskModel
from sql_checker.inception import Inception
import sql_checker.rollback as sql_rollback
from decouple import config
import logger.logger as log
import notify.notify as notify
import demjson

def jd(string, jd_length = 6):
    '''
    返回截断的字符串，原字符串
    '''
    length = len(string)
    if length <= jd_length:
        return string, string
    jd_str = string[0:jd_length]
    return jd_str + '...', string

class index(Admin):

    def handle(self):
        orders = []
        if self.data['session']['role'] == 'admin':
            #获取所有状态不是未提交的工单
            #orders = OrderModel().rows()
            #order_rows = OrderModel().rows()
            order_rows = OrderModel().rowsByShowCols()
            orders = filter(lambda row: row['order_status'] != ORDER_STATUS_NO_COMMIT, order_rows)
        else:
            orders = OrderModel().loadByReqUser(self.session('domain_name'))
        for order in orders:
            #if config('DEBUG') == 'true':
            #    order['order_status'] = ORDER_STATUS_NO_VIEW 
            order_status = order['order_status']
            order_status_text = ''
            if  order_status == ORDER_STATUS_NO_VIEW:
                #order_status_text = u'未处理'
                order_status_text = u'待上线'
            elif order_status == ORDER_STATUS_CANCEL:
                order_status_text = u'已取消'
            elif order_status == ORDER_STATUS_AGREE_FAILED:
                order_status_text = u'上线失败'
            elif order_status == ORDER_STATUS_AGREE_SUCCED:
                order_status_text = u'上线成功'
            elif order_status == ORDER_STATUS_ASYNC_EXEC:
                order_status_text = u'异步执行中，请等待'
            elif order_status == ORDER_STATUS_NO_COMMIT:
                order_status_text = u'待提交'
            else:
                order_status_text = u'未知错误'
            order['reason_jd'], _ = jd(order['reason'])
            order['latest_exec_result_jd'], _ = jd(order['latest_exec_result'])
            order['order_status_text'] = order_status_text
        self.data['rows'] = orders
        if self.data['session']['role'] == 'admin':
            self.data['page_title'] = u'审批'
        else:
            self.data['page_title'] = u'我的申请'
        return self.render().order_index(data=self.data)

class my_order(Guest):
    def handle(self):
        orders = OrderModel().loadByReqUser(self.session('domain_name'))
        for order in orders:
            if config('DEBUG') == 'true':
                order['order_status'] = ORDER_STATUS_NO_VIEW 
            order_status = order['order_status']
            order_status_text = ''
            if  order_status == ORDER_STATUS_NO_VIEW:
                #order_status_text = u'未处理'
                order_status_text = u'待上线'
            elif order_status == ORDER_STATUS_CANCEL:
                order_status_text = u'已取消'
            elif order_status == ORDER_STATUS_AGREE_FAILED:
                order_status_text = u'上线失败'
            elif order_status == ORDER_STATUS_AGREE_SUCCED:
                order_status_text = u'上线成功'
            elif order_status == ORDER_STATUS_ASYNC_EXEC:
                order_status_text = u'异步执行中，请等待'
            elif order_status == ORDER_STATUS_NO_COMMIT:
                order_status_text = u'待提交'
            else:
                order_status_text = u'未知错误'
            order['reason_jd'], _ = jd(order['reason'])
            order['latest_exec_result_jd'], _ = jd(order['latest_exec_result'])
            order['order_status_text'] = order_status_text
        self.data['rows'] = orders
        self.data['page_title'] = u'我的申请'
        return self.render().order_index(data=self.data)

class delete(Admin):
    def handle(self):
        id = self.request('id')
        OrderModel().delete(id)
        raise web.seeother('/sql_order/index')

class view(Admin):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        form = self.request('form')
        order = OrderModel.load(id)
        self.data['row'] = order
        self.data['form'] = form
        return self.render().order_view(data=self.data)

class cancel(Admin):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        reason = self.request('reason')
        notify.add_comment(id, self.session('domain_name'), self.session('password'), reason)
        orderModel = OrderModel()
        orderModel.id = id
        orderModel.setOrderStatus(ORDER_STATUS_NO_COMMIT)
        #orderModel.cancel(id)
        return self.resp()
        #raise web.seeother('/sql_order/index')

class rollback(Admin):
    def handle(self):
        err =  sql_rollback.rollback(self.request('order_id'))
        if err != None:
            return self.resp(errno=1, errmsg=err)
        else:
            return self.resp()

class online(Admin):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        orderModel = OrderModel()
        order = orderModel.load(id)
        self.data['row'] = order
        return self.render().order_online2(data=self.data)

class view_process(Admin):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        orderModel = OrderModel()
        order = orderModel.load(id)
        self.data['order'] = order
        self.data['async_process_show_intval'] = config('ASYNC_SQL_PROC_GET_INTVAL', cast=int)
        return self.render().view_process(data=self.data)

class view_sql(Guest):
    def handle(self):
        order_id = self.request('order_id')
        self.safeId(order_id)
        orderModel = OrderModel()
        order = orderModel.load(order_id)
        order['sql'] = self.formatSql(order['sql'])
        return self.resp(data=order)

class my_order_delete(Guest):
    def handle(self):
        id = self.request('id')
        self.safeId(id)
        orderModel = OrderModel()
        order = orderModel.load(id)
        req_user = order['req_user']
        cur_user = self.session('domain_name')
        if req_user != cur_user:
            if self.session('role') != 'admin':
                return self.resp(errno=1, errmsg='删除失败')
        orderModel.delete(id)
        return self.resp()

class get_process(Admin):
    def handle(self):
        order_id = self.request('order_id')
        self.safeId(order_id)
        orderModel = OrderModel()
        order = orderModel.load(order_id)
        print 'order', order
        process_text = ''
        percent = '0%'
        exec_status = ''
        order_status = order['order_status']
        if order_status == ORDER_STATUS_NO_VIEW:
            process_text = u'等待管理员审批'
            exec_status = process_text
            percent = '0%'
        if order_status == ORDER_STATUS_AGREE_SUCCED:
            print 'ORDER_STATUS_AGREE_SUCCED'
            process_text = u'执行完成'
            exec_status = process_text
            percent = '100%'
        if order_status == ORDER_STATUS_AGREE_FAILED:
            process_text = u'执行出错，错误信息:\r\n' + order['latest_exec_result']
            exec_status = u'执行出错'
            percent = '100%'
        if order_status == ORDER_STATUS_CANCEL:
            process_text = u'任务已被管理员取消执行'
            exec_status = process_text
            percent = '0%'
        if order_status == ORDER_STATUS_ASYNC_EXEC:
            inception = Inception(host=config('INCEPTION_HOST'), port=config('INCEPTION_PORT'))
            osc_proc = inception.getOscProcessBySql(order['sql'])
            log.info("get_process:" + str(osc_proc))
            if osc_proc:
                process_text = osc_proc['INFOMATION']
                percent = str(osc_proc['PERCENT']) + '%'
                exec_status = u'执行中...'
            else:
                proc = inception.getProcessBySql(order['sql'])
                print 'proc', proc
                if proc:
                    tmp_str = ''
                    try:
                        proc.remove('Id')
                    except:
                        pass
                    for k, v in proc.items():
                        tmp_str = tmp_str + str(k) + ":" + str(v) + "\r\n"
                    process_text = tmp_str
                    exec_status = u'非osc任务无法显示执行百分比'
                    percent = 'no show'
        print 'exec_status', exec_status
        data = {}
        data['process_text'] = process_text
        data['percent'] = percent
        data['exec_status'] = exec_status
        return self.resp(data=data)

class execute(Admin):
    def handle(self):
        '''
        错误码:
        1.有错误
        4.有警告，有错误
        2.有警告，无错误
        3.无警告，有错误
        5.影响行数较多，添加到后台异步执行，稍后反馈执行结果
        6.执行出错了
        8.异常
        '''
        id = self.request('id')
        self.safeId(id)
        orderModel = OrderModel()
        order = orderModel.load(id)
        ins_id = order['ins_id']
        sel_db_name = order['sel_db_name']
        sql = order['sql']
        src_sql = sql
        #sql = "use `%s`;SET NAMES UTF8;%s" % (sel_db_name, sql)
        sql = unicode("use `%s`;SET NAMES UTF8;" % sel_db_name) + unicode(sql)
        #sql = unicode("use `%s`;set names utf8mb4;" % sel_db_name) + unicode(sql)
        log.info("execute sql:"+sql)
        server_id = order['server_id']
        server = MysqlServerModel().load(server_id)
        optHost = server['ip']
        optPort = int(order['sel_port'])
        insModel = MysqlInstanceModel()
        instance = insModel.load(ins_id)
        optUser = instance['remote_user']
        optPwd = instance['remote_pwd']
        log.info("ready to check by inception")
        
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
        inc.curDb = sel_db_name
        inc.curUserRole = self.session('role')
        #备份设置
        if config('IS_BACKUP') == 'true':
            inc.enableRemoteBackup = True
        else:
            inc.enableRemoteBackup = False
        
        resultSet = None
        errno = 0
        errmsg = ''
        try:
            resultSet = inc.check(sql)
            #resultSet = inc.run(sql)
        except Exception, ex:
            #执行检查发生了异常，此时，将异常信息存入工单执行结果中
            errno = 1
            errmsg = str(ex)
            orderModel.setLatestExecResult(id, False, errmsg)
            return self.resp(errno=errno, errmsg=errmsg)
        if resultSet == None:
            errno = 1 
            errmsg = "resultSet is None"
            orderModel.setLatestExecResult(id, False, errmsg)
            return self.resp(errno=errno, errmsg=errmsg)
        sha1List = resultSet.getSqlSha1List()

        ret = {
            'advice' : '',
            'warning' : '',
            'error' : '',
            'sql' : sql,
            'runsql': resultSet.runSql,
            'sha1_list' : sha1List,
            'format_sql' : self.formatSql(src_sql)
        }
        log.info("sha1list:" + str(sha1List))

        warnTag = resultSet.isHasWarning()
        errorTag = resultSet.isHasError()

        if warnTag and errorTag:
            #有警告，有错误
            #这种情况只显示错误，用户先修正错误
            errno = 4
            ret['error'] = resultSet.errorsStr()
            orderModel.setLatestExecResult(id, False, ret['error'])
            return self.resp(errno=errno, data=ret, errmsg=ret['error'])
        elif warnTag and errorTag == False:
            #有警告，无错误
            errno = 2
            ret['warning'] = resultSet.warningsStr()
            orderModel.setLatestExecResult(id, False, ret['warning'])
            return self.resp(errno=errno, data=ret, errmsg=ret['warning'])
        elif warnTag == False and errorTag:
            #无警告，有错误
            errno = 3
            ret['error'] = resultSet.errorsStr() 
            orderModel.setLatestExecResult(id, False, ret['error'])
            return self.resp(errno=errno, data=ret, errmsg=ret['error'])
        else:
            #审核通过，无警告，无错误，判断影响的行数
            if resultSet.isAffectRowsExceedLimit(config('ASYNC_AFFECT_ROWS_LIMIT', cast=int)):
                log.info("sql exceed ASYNC_AFFECT_ROWS_LIMIT add to async task exec")
                #有sql超过了影响的行数，添加到后台任务中执行
                sqlTaskModel = SqlTaskModel()
                sqlTaskModel.orderId = id
                sqlTaskModel.jiraUser = self.session('domain_name')
                sqlTaskModel.jiraPwd = self.session('password')
                sqlTaskModel.addTask()
                orderModel.setToAsyncExecStatus(id)
                return self.resp(errno=5, errmsg=u'影响行数较多，添加到后台异步执行，稍后请查看执行结果')
            try:
                log.info("[exec before run] sql:" + sql)
                resultSet = inc.run(sql)
            except Exception, ex:
                orderModel.setLatestExecResult(id, False, str(ex))
                return self.resp(errno=8, errmsg=str(ex))
            warnTag = resultSet.isHasWarning()
            errorTag = resultSet.isHasError()

            if warnTag:
                warning_info = resultSet.warningsStr()
                log.info("has warning:" + warning_info)
            
            if errorTag == True:
                errstr = ''
                #if warnTag:
                #    warning_info = resultSet.warningsStr()
                #    log.info("has warning:" + str(warning_info))
                #    #errstr = resultSet.warningsStr()
                if errorTag:
                    errstr = resultSet.errorsStr()
                orderModel.setLatestExecResult(id, False, errstr)
                #执行出错了
                return self.resp(errno=6, errmsg=errstr)
            #设置最近执行结果
            orderModel.setLatestExecResult(id, True, u'执行成功')
            #保存inception返回的原生结果集
            orderModel.saveRawResultSet(id, resultSet.rawResultSet)
            #执行成功了
            #调用jira接口，issue状态更新为已解决
            try:
                notify.reslove_issue(id, self.session('domain_name'), self.session('password'))
            except Exception, ex:
                log.error("notify.reslove_issue exception:" + str(ex))
            return self.resp(data=ret)

class api_execute(NoAuth):
    def handle(self):
        '''
        错误码:
        1.有错误
        4.有警告，有错误
        2.有警告，无错误
        3.无警告，有错误
        5.影响行数较多，添加到后台异步执行，稍后反馈执行结果
        6.执行出错了
        8.异常
        '''
        token = self.request('token')
        if token != config('AUTO_VERIFY_TOKEN'):
            return self.resp(errno=1, errmsg = 'request invalid')
        id = self.request('id')
        self.safeId(id)
        orderModel = OrderModel()
        order = orderModel.load(id)
        ins_id = order['ins_id']
        sel_db_name = order['sel_db_name']
        sql = order['sql']
        src_sql = sql
        #sql = "use `%s`;SET NAMES UTF8;%s" % (sel_db_name, sql)
        sql = unicode("use `%s`;SET NAMES UTF8;" % sel_db_name) + unicode(sql)
        #sql = unicode("use `%s`;set names utf8mb4;" % sel_db_name) + unicode(sql)
        log.info("execute sql:"+sql)
        server_id = order['server_id']
        server = MysqlServerModel().load(server_id)
        optHost = server['ip']
        optPort = int(order['sel_port'])
        insModel = MysqlInstanceModel()
        instance = insModel.load(ins_id)
        optUser = instance['remote_user']
        optPwd = instance['remote_pwd']
        log.info("ready to check by inception")
        
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
        inc.curDb = sel_db_name
        #inc.curUserRole = self.session('role')
        inc.curUserRole = 'admin'
        #备份设置
        if config('IS_BACKUP') == 'true':
            inc.enableRemoteBackup = True
        else:
            inc.enableRemoteBackup = False
        
        resultSet = None
        errno = 0
        errmsg = ''
        try:
            resultSet = inc.check(sql)
            #resultSet = inc.run(sql)
        except Exception, ex:
            #执行检查发生了异常，此时，将异常信息存入工单执行结果中
            errno = 1
            errmsg = str(ex)
            orderModel.setLatestExecResult(id, False, errmsg)
            return self.resp(errno=errno, errmsg=errmsg)
        if resultSet == None:
            errno = 1 
            errmsg = "resultSet is None"
            orderModel.setLatestExecResult(id, False, errmsg)
            return self.resp(errno=errno, errmsg=errmsg)
        sha1List = resultSet.getSqlSha1List()

        ret = {
            'advice' : '',
            'warning' : '',
            'error' : '',
            'sql' : sql,
            'runsql': resultSet.runSql,
            'sha1_list' : sha1List,
            'format_sql' : self.formatSql(src_sql)
        }
        log.info("sha1list:" + str(sha1List))

        warnTag = resultSet.isHasWarning()
        errorTag = resultSet.isHasError()

        if warnTag and errorTag:
            #有警告，有错误
            #这种情况只显示错误，用户先修正错误
            errno = 4
            ret['error'] = resultSet.errorsStr()
            orderModel.setLatestExecResult(id, False, ret['error'])
            return self.resp(errno=errno, data=ret, errmsg=ret['error'])
        elif warnTag and errorTag == False:
            #有警告，无错误
            errno = 2
            ret['warning'] = resultSet.warningsStr()
            orderModel.setLatestExecResult(id, False, ret['warning'])
            return self.resp(errno=errno, data=ret, errmsg=ret['warning'])
        elif warnTag == False and errorTag:
            #无警告，有错误
            errno = 3
            ret['error'] = resultSet.errorsStr() 
            orderModel.setLatestExecResult(id, False, ret['error'])
            return self.resp(errno=errno, data=ret, errmsg=ret['error'])
        else:
            #审核通过，无警告，无错误，判断影响的行数
            if resultSet.isAffectRowsExceedLimit(config('ASYNC_AFFECT_ROWS_LIMIT', cast=int)):
                log.info("sql exceed ASYNC_AFFECT_ROWS_LIMIT add to async task exec")
                #有sql超过了影响的行数，添加到后台任务中执行
                sqlTaskModel = SqlTaskModel()
                sqlTaskModel.orderId = id
                #sqlTaskModel.jiraUser = self.session('domain_name')
                #sqlTaskModel.jiraPwd = self.session('password')
                sqlTaskModel.jiraUser = config('AUTO_VERIFY_DEFAULT_JIRA_USER')
                sqlTaskModel.jiraPwd = config('AUTO_VERIFY_DEFAULT_JIRA_PWD')
                sqlTaskModel.addTask()
                orderModel.setToAsyncExecStatus(id)
                return self.resp(errno=5, errmsg=u'影响行数较多，添加到后台异步执行，稍后请查看执行结果')
            try:
                log.info("[exec before run] sql:" + sql)
                resultSet = inc.run(sql)
            except Exception, ex:
                orderModel.setLatestExecResult(id, False, str(ex))
                return self.resp(errno=8, errmsg=str(ex))
            warnTag = resultSet.isHasWarning()
            errorTag = resultSet.isHasError()

            if warnTag:
                warning_info = resultSet.warningsStr()
                log.info("has warning:" + warning_info)
            
            if errorTag == True:
                errstr = ''
                #if warnTag:
                #    warning_info = resultSet.warningsStr()
                #    log.info("has warning:" + str(warning_info))
                #    #errstr = resultSet.warningsStr()
                if errorTag:
                    errstr = resultSet.errorsStr()
                orderModel.setLatestExecResult(id, False, errstr)
                #执行出错了
                return self.resp(errno=6, errmsg=errstr)
            #设置最近执行结果
            orderModel.setLatestExecResult(id, True, u'执行成功')
            #保存inception返回的原生结果集
            orderModel.saveRawResultSet(id, resultSet.rawResultSet)
            #执行成功了
            #调用jira接口，issue状态更新为已解决
            try:
                notify.reslove_issue(id, self.session('domain_name'), self.session('password'))
            except Exception, ex:
                log.error("notify.reslove_issue exception:" + str(ex))
            return self.resp(data=ret)

from agileutil.webpy_base import WebPyBase
class test_test(WebPyBase):
    def handle(self):
        sql = "insert into test(txt) values('123')"
        import sys
        sys.path.append('../')
        import db.mysql as mysql_util
        mysql_util.update(sql)
        return str(mysql_util.lastrowid())
        '''
        order_id = self.request('order_id')
        orderModel = OrderModel()
        order = orderModel.load(order_id)
        print 'order', order
        process_text = ''
        percent = '0%'
        exec_status = ''
        order_status = order['order_status']
        if 1 == 1:
            inception = Inception(host=config('INCEPTION_HOST'), port=config('INCEPTION_PORT'))
            osc_proc = inception.getOscProcessBySql(order['sql'])
            log.info("get_process:" + str(osc_proc))
            if osc_proc:
                process_text = osc_proc['INFOMATION']
                percent = str(osc_proc['PERCENT']) + '%'
                exec_status = u'执行中...'
            else:
                proc = inception.getProcessBySql(order['sql'])
                print 'proc', proc
                if proc:
                    tmp_str = ''
                    try:
                        proc.remove('Id')
                    except:
                        pass
                    for k, v in proc.items():
                        tmp_str = tmp_str + str(k) + ":" + str(v) + "\r\n"
                    process_text = tmp_str
                    exec_status = u'非osc任务无法显示执行百分比'
                    percent = 'no show'
        print 'exec_status', exec_status
        data = {}
        data['process_text'] = process_text
        data['percent'] = percent
        data['exec_status'] = exec_status
        return self.resp(data=data)
        '''

class new_get_process(Admin):
    def handle(self):
        order_id = self.request('order_id')
        self.safeId(order_id)
        orderModel = OrderModel()
        order = orderModel.load(order_id)
        print 'order', order
        process_text = ''
        percent = '0%'
        exec_status = ''
        order_status = order['order_status']
        if order_status == ORDER_STATUS_NO_VIEW:
            process_text = u'等待管理员审批'
            exec_status = process_text
            percent = '0%'
        if order_status == ORDER_STATUS_AGREE_SUCCED:
            print 'ORDER_STATUS_AGREE_SUCCED'
            process_text = u'执行完成'
            exec_status = process_text
            percent = '100%'
        if order_status == ORDER_STATUS_AGREE_FAILED:
            process_text = u'执行出错，错误信息:\r\n' + order['latest_exec_result']
            exec_status = u'执行出错'
            percent = '100%'
        if order_status == ORDER_STATUS_CANCEL:
            process_text = u'任务已被管理员取消执行'
            exec_status = process_text
            percent = '0%'
        if order_status == ORDER_STATUS_ASYNC_EXEC:
            inception = Inception(host=config('INCEPTION_HOST'), port=config('INCEPTION_PORT'))
            osc_proc = inception.getOscProcessBySql(order['sql'])
            log.info("get_process:" + str(osc_proc))
            if osc_proc:
                process_text = osc_proc['INFOMATION']
                percent = str(osc_proc['PERCENT']) + '%'
                exec_status = u'执行中...'
            else:
                proc = inception.getProcessBySql(order['sql'])
                print 'proc', proc
                if proc:
                    tmp_str = ''
                    try:
                        proc.remove('Id')
                    except:
                        pass
                    for k, v in proc.items():
                        tmp_str = tmp_str + str(k) + ":" + str(v) + "\r\n"
                    process_text = tmp_str
                    exec_status = u'非osc任务无法显示执行百分比'
                    percent = 'no show'
        print 'exec_status', exec_status
        data = {}
        data['process_text'] = process_text
        data['percent'] = percent
        data['exec_status'] = exec_status
        return self.resp(data=data)