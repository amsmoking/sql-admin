#coding=utf-8

'''
从sql_task表中获取异步执行的耗时sql, 来执行
'''

import sys
sys.path.append("../")
import time
from decouple import config
from agileutil.log import Log
from multiprocessing import Process
from model.sql_task_model import SqlTaskModel
from model.order import OrderModel
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_ins_db_model import MysqlInsDbModel
from sql_checker.inception import *
import notify.notify as notify
import model.inception as inc_util

log = Log(config('ASYNC_SQL_EXEC_LOG'))
sqlTaskModel = SqlTaskModel()
orderModel = OrderModel()
serverModel = MysqlServerModel()
insModel = MysqlInstanceModel()
insDbModel = MysqlInsDbModel()

def get_one_task():
    task = sqlTaskModel.getOneTask()
    return task

def do_task(task):
    if task == None: return
    log.info("ready to do sql task")
    sqlTaskModel.setExecStatusToExecIng(task['id'])
    order_id = task['order_id']
    order = orderModel.load(order_id)
    server_id = order['server_id']
    ins_id = order['ins_id']
    server = serverModel.load(server_id)
    ins = insModel.load(ins_id)
    optHost = server['ip']
    optPort = int(order['sel_port'])
    optUser = ins['remote_user']
    optPwd = ins['remote_pwd']
    sel_db_name = order['sel_db_name']
    sql = order['sql']
    #sql = "use `%s`;%s" % (sel_db_name, sql)
    #sql = unicode("use `%s`;SET NAMES UTF8;" % sel_db_name) + unicode(sql)
    sql = "use `%s`;SET NAMES UTF8;%s" % (sel_db_name, sql)
    idc, _ = inc_util.getIdcByHostname(server['hostname'])
    inc_host, inc_port = inc_util.getIncHostPortByIdc(idc)
    inc = Inception(
        host = inc_host,
        port = inc_port,
        optHost=optHost,
        optPort=optPort,
        optUser=optUser,
        optPwd=optPwd
    )
    #备份设置
    if config('IS_BACKUP') == 'true':
        inc.enableRemoteBackup = True
    else:
        inc.enableRemoteBackup = False
    resultSet = None
    log.info("ready to run in inception")
    try:
        resultSet = inc.run(sql)
        log.info("run in inception finish")
    except Exception, ex:
        log.error("run in inception exception:%s" % str(ex))
        return str(ex)
    log.info("after run in inception, resultSet is:")
    for res in resultSet.resultList:
        log.info(res.dump())
    if resultSet.isHasWarning():
        #有警告
        warning_info = resultSet.warningsStr()
        log.warning("exec sql has warning:" + warning_info) 
        #return warning_info
    if resultSet.isHasError():
        #有错误
        err_info = resultSet.errorsStr()
        log.error("exec sql has error:" + err_info)
        return err_info
    #没警告，没错误
    log.info("exec in inception succed")
    #保存inception返回的原生结果集
    orderModel.saveRawResultSet(order_id, resultSet.rawResultSet)
    return None

def main():
    task = get_one_task()
    if task == None:
        log.info("no sql tasks")
        return
    log.info("get task:" + str(task) )
    err = do_task(task)
    order_id = task['order_id']
    if err != None:
        #出错了
        orderModel.setLatestExecResult(order_id, False, err)
        log.info("set latest exec status in table order to failed")
        notify.send_alarm('xsql', '[async exec sql] failed:' + err)
    else:
        #成功了
        orderModel.setLatestExecResult(order_id, True, u'异步执行成功')
        log.info("set latest exec status in table order to succed")
        #调用jira接口更新任务状态为已解决
        try:
            notify.reslove_issue(task['order_id'], task['jira_user'], task['jira_pwd'])
            log.info("call jira api to reslove issue succed")
        except Exception, ex:
            log.error("call jira api to reslove issue exception:" + str(ex))
    sqlTaskModel.setExecStatusToExecFinish(task['id'])
    log.info("set sql task status to finish")

def async_exec_sql_target():
    while 1:
        log.info('sleep')
        time.sleep(config('ASYNC_SQL_CONSUMER_EXEC_INTVAL', cast=int))
        #main()
        try:
            main()
        except Exception, ex:
            log.error("async exec sql global exception:%s" % (str(ex)))

def start():
    p=Process(target=async_exec_sql_target)
    p.start()
    return