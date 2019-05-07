#coding=utf-8

import sys
sys.path.append('../')
from multiprocessing import Process
from decouple import config
import logger.logger as log
import time
from model.auto_verify_model import AutoVerifyModel
from model.mysql_instance_model import MysqlInstanceModel
from model.order import OrderModel
import requests

def logInfo(string):
    log.info("[auto_verify] " + string)

def logWarn(string):
    log.warning("[auto_verify] " + string)

def logError(string):
    log.error("[auto_verify] " + string)

def isInExecTimeRange(beginTime, endTime, curTime):
    hour, minute, second = [int(item) for item in  str(curTime).split(':')]
    bHour, bMinute, bSecond = [int(item) for item in  str(beginTime).split(':')]
    eHour, eMinute, eSecond = [int(item) for item in  str(endTime).split(':')]
    logInfo("hour:%s, minute:%s, second:%s" % (hour, minute, second))
    logInfo("bHour:%s, bMinute:%s, bSecond:%s" % (bHour, bMinute, bSecond) )
    logInfo("eHour:%s, eMinute:%s, eSecond:%s" % (eHour, eMinute, eSecond) )
    isCanExecTag = False
    if  hour >= bHour or hour <= eHour:
        if hour >= bHour:
            if hour == bHour:
                if minute >= bMinute:
                    if minute == bMinute:
                        if second >= bSecond:
                            isCanExecTag = True
                        else:
                            isCanExecTag = False
                    else:
                        #>Minute
                        isCanExecTag = True
                else:
                    #minute < bMinute
                    isCanExecTag = False
            else:
                #>bHour
                isCanExecTag = True
        else:
            if hour == eHour:
                if minute <= eMinute:
                    if minute == eMinute:
                        if second <= eSecond:
                            if second == eSecond:
                                isCanExecTag = False
                            else:
                                isCanExecTag = True
                        else:
                            isCanExecTag = False
                    else:
                        isCanExecTag = True
                else:
                    isCanExecTag = False
            else:
                #<eHour
                isCanExecTag = True
    return isCanExecTag

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
    

def verify():
    autoVerify = AutoVerifyModel().loadAutoVerify()
    if autoVerify['enable'] == 0:
        logInfo("not enable, pass")
        return
    #order = OrderModel().getOneToOnlineOrder()
    order = OrderModel().getOneNoDangeOrder()
    if order == None:
        logInfo("no to online order, return")
        return
    orderId = order['id']
    insId = order['ins_id']
    instance = MysqlInstanceModel().load(insId)
    allowBeginTime = instance['allow_begin_time']
    allowEndTime = instance['allow_end_time']
    if allowBeginTime == '' or allowEndTime == '':
        logInfo("instance has no auto verify time range")
        beginTime = autoVerify['begin_time']
        endTime = autoVerify['end_time']
        if beginTime == '' or endTime == '':
            logInfo("auto verify default time range is empty")
            return
        allowBeginTime = beginTime
        allowEndTime = endTime
    else:
        logInfo("use instance time range")
    logInfo("final allow exec time range is:%s - %s"  % (allowBeginTime, allowEndTime) )
    curTime = time.strftime('%H:%M:%S', time.localtime(int(time.time())))
    if isInExecTimeRange(allowBeginTime, allowEndTime, curTime) == False:
        logInfo("not in exec time range, return")
        return
    sql = order['sql']
    if isDangerSql(sql):
        logWarn("found dange sql keyword in sql, not exec, return")
        return
    logInfo("not found danger sql, in time range, ready call exec api")
    url = config('AUTO_VERIFY_API')
    token = config('AUTO_VERIFY_TOKEN')
    params = {
        'id' : str(orderId),
        'token' : token
    }
    r = requests.post(url, data=params)
    code = r.status_code
    resp = r.text
    logInfo("after call auto_verify api, code:%s, resp:%s" % (code, resp) )

def auto_verify():
    logInfo("start")
    while True:
        time.sleep(int(config('AUTO_VERIFY_CHECK_INTVAL')))
        try:
            verify()
            logInfo("check once")
        except Exception as ex:
            logError("global exception:" + str(ex))

def start():
    p=Process(target=auto_verify)
    p.start()
    return