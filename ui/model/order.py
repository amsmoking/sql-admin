#coding=utf-8

from common_model import *
from mysql_server_model import MysqlServerModel
import agileutil.date as dt
import demjson

ORDER_STATUS_NO_VIEW = 0
ORDER_STATUS_AGREE_SUCCED = 1
ORDER_STATUS_AGREE_FAILED = 2
ORDER_STATUS_CANCEL = 3
ORDER_STATUS_ASYNC_EXEC = 4
#用户保存了工单，但没有提交，不显示在管理员的审批列表中
ORDER_STATUS_NO_COMMIT = 5

def isDangerSql(sql):
    dangeKeywordList = ['delete', 'drop', 'truncate', 'DELETE', 'DROP', 'TRUNCATE']
    try:
        sql.lower()
    except:
        pass
    for keyword in dangeKeywordList:
        if keyword in sql:
            return True
    return False

class OrderModel(CommonModel):

    def __init__(self):
        CommonModel.__init__(self)
        self.tableName = 'sql_order'
        #columons
        self.serverId = 0
        self.insId = 0
        self.insDbId = 0
        self.sql = ''
        self.createTime = dt.current_time()
        self.selIp = ''
        self.selPort = 0
        self.selDbName = ''
        self.reason = ''
        self.reqUser = ''
        self.orderStatus = ORDER_STATUS_NO_VIEW
        self.latestExecResult = ''
        self.combiInfo = ''
        self.rollbacTimes = 0
        self.runResultSet = ''

    def save(self):
        if self.id == 0:
            #create
            self.createTime = dt.current_time()
            sql = "insert into %s(server_id, ins_id, ins_db_id, `sql`, create_time, sel_ip, sel_port, sel_db_name, reason, req_user, order_status, latest_exec_result, combi_info) "\
            "values(%s, %s, %s, '%s', '%s', '%s', %s, '%s', '%s', '%s', %s, '%s', '%s')" % (
                self.tableName, self.serverId, self.insId, self.insDbId, self.escapeString(self.sql), self.createTime, self.selIp, self.selPort,
                self.selDbName, self.escapeString(self.reason), self.reqUser, self.orderStatus, self.escapeString(self.latestExecResult), self.escapeString(self.combiInfo))
        else:
            #update
            sql = "update %s set server_id=%s, ins_id=%s, ins_db_id=%s, `sql`='%s',"\
            "sel_ip='%s', sel_port=%s, sel_db_name='%s', reason='%s', req_user='%s',"\
            "order_status=%s, latest_exec_result='%s', combi_info='%s' "\
            "where id=%s" % (
                self.tableName, self.serverId, self.insId, self.insDbId, self.escapeString(self.sql),
                self.selIp, self.selPort, self.selDbName, self.escapeString(self.reason), self.reqUser,
                self.orderStatus, self.latestExecResult, self.escapeString(self.combiInfo), self.id
            )
            print sql
        return self.update(sql)

    def setOrderStatus(self, status):
        sql = "update %s set order_status=%s where id=%s" % (
            self.tableName, status, self.id)
        return self.update(sql) 

    def cancel(self, id):
        #调用jira接口，提交一个comment
        self.id = id
        return self.setOrderStatus(ORDER_STATUS_CANCEL)

    def setLatestExecResult(self, id, isSucced = True, result = ''):
        if isSucced:
            self.orderStatus = ORDER_STATUS_AGREE_SUCCED
        else:
            self.orderStatus = ORDER_STATUS_AGREE_FAILED
        sql = "update %s set order_status=%s, latest_exec_result='%s' where id=%s" % (
            self.tableName, self.orderStatus, self.escapeString(result), id)
        return self.update(sql)

    def setToAsyncExecStatus(self, id):
        sql = "update %s set order_status=%s, latest_exec_result='%s' where id=%s" % (
            self.tableName, ORDER_STATUS_ASYNC_EXEC, '', id)
        return self.update(sql)

    def setIssueKey(self, id, issueKey):
        sql = "update %s set issue_key='%s' where id=%s" % (self.tableName, issueKey, id)
        return self.update(sql)

    def loadByReqUser(self, reqUser):
        sql = "select * from %s where req_user='%s'" % (self.tableName, reqUser)
        return self.query(sql)

    def saveRawResultSet(self, id, rawResultSet):
        rawResultSet = demjson.encode(rawResultSet)
        sql = "update %s set run_result_set='%s' where id=%s" % (self.tableName, self.escapeString(rawResultSet), id)
        return self.update(sql)

    def increaseRollbackTimes(self, order_id):
        order = self.load(order_id)
        rollback_times = int(order['roll_back_times'])
        rollback_times = rollback_times + 1
        sql = "update %s set roll_back_times=%s where id=%s" % (self.tableName, rollback_times, order_id)
        return self.update(sql)

    def rowsByShowCols(self):
        sql = 'select id,req_user,reason,create_time,sel_ip,sel_db_name,sel_port,order_status,latest_exec_result,roll_back_times from sql_order order by id desc limit 50'
        rows = self.query(sql)
        if rows == None: rows = []
        return rows

    def countByStatus(self, status):
        sql = 'select count(*) as cnt from `%s` where order_status=%s' % (self.tableName, status)
        rows = self.query(sql)
        row = rows[0]
        cnt = row['cnt']
        return cnt

    def getToOnlineOrderList(self):
        sql = 'select * from %s where order_status=0' % self.tableName
        rows = self.query(sql)
        if rows == None or len(rows) == 0: rows = []
        return rows

    '''
    def getHasWindowTimeOrderList(self):
        orderList = self.getToOnlineOrderList()
        for order in orderList:
            if order['']
    '''

    def getOneToOnlineOrder(self):
        sql = 'select * from %s where order_status=0 limit 1' % self.tableName
        rows = self.query(sql)
        if rows == None or len(rows) == 0: return None
        return rows[0]

    def getOneNoDangeOrder(self):
        orderList = self.getToOnlineOrderList()
        for order in orderList:
            sql = order['sql']
            if not isDangerSql(sql):
                return order
