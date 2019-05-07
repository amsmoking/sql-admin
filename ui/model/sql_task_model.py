#coding=utf-8

from common_model import *
import agileutil.date as dt
from order import OrderModel, ORDER_STATUS_ASYNC_EXEC

EXEC_STATUS_TO_EXEC = 0
EXEC_STATUS_EXEC_ING = 1
EXEC_STATUS_EXEC_FINISH = 2

class SqlTaskModel(CommonModel):

    def __init__(self):
        CommonModel.__init__(self)
        self.tableName = 'sql_task'
        #columons
        self.orderId = 0
        self.execStatus = 0
        self.jiraUser = ''
        self.jiraPwd = ''
        self.createTime = dt.current_time()

    def addTask(self):
        sql = "insert into sql_task(order_id, exec_status, create_time, jira_user, jira_pwd) values(%s, %s, '%s', '%s', '%s')" % (
            self.orderId, self.execStatus, dt.current_time(), self.jiraUser, self.jiraPwd)
        return self.update(sql)

    def resetAsync(self, order_id):
        sql = "update sql_task set exec_status=%s where order_id=%s" % (
            EXEC_STATUS_TO_EXEC, order_id
        )
        self.update(sql)
        sql = "update sql_order set order_status=%s, latest_exec_result='' where id=%s" % (
            ORDER_STATUS_ASYNC_EXEC, order_id   
        )
        return self.update(sql)

    def resetSucced(self, order_id, is_async = '0'):
        zh = '执行成功'
        if is_async == '1':
            zh = '异步执行成功'
        sql = "update sql_order set order_status=1, latest_exec_result='" + zh +"' where id=%s" % order_id
        return self.update(sql)

    def getOneTask(self):
        sql = "select * from sql_task where exec_status=%s limit 1" % EXEC_STATUS_TO_EXEC
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return None
        row = rows[0]
        return row

    def getOneExecingTask(self):
        sql = "select * from sql_task where exec_status=%s limit 1" % EXEC_STATUS_EXEC_ING
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return None
        row = rows[0]
        return row

    def setExecStatusToExecIng(self, task_id):
        return self.updateExecStatus(task_id, EXEC_STATUS_EXEC_ING)

    def setExecStatusToExecFinish(self, task_id):
        return self.updateExecStatus(task_id, EXEC_STATUS_EXEC_FINISH)

    def updateExecStatus(self, task_id, status):
        sql = "update sql_task set exec_status=%s where id=%s" % (status, task_id)
        self.update(sql)