#coding=utf-8
import time
import sys
sys.path.append('../')
from multiprocessing import Process
from agileutil.log import Log
from decouple import config
from db.mysql import mysql_db
from agileutil.db import Orm, DB
from croniter import croniter
import agileutil.date as dt
from datetime import datetime
import zmq

log = Log(config('CRON_JUDGER_LOG'))
if config('LOG_OUTPUT') == 'true': log.setOutput(True)

def send_msg(msg):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    log.info("ready to connect to mq")
    socket.connect (config('MQ_ADDR'))
    log.info("connected")
    socket.send(msg)
    response = socket.recv()
    log.info("recv response is:" + response)

def cron_judger():
    #获取当前时间
    now_time = datetime.now()
    now_stamp = time.mktime(now_time.timetuple())
    #获取所有任务
    tasks = Orm(mysql_db).table('archive_task').get()
    #遍历任务
    for task in tasks:
        #检查状态是否为启用
        status = int(task['status'])
        if status == 0: 
            log.info("task id:%s status is 0, pass not send exec msg" % task['id'])
            continue
        #计算下一次执行时间
        cron = task['cron']
        latest_exec_time = task['latest_exec_time']
        log.info('task_id:%s, cron:%s, last exec time: %s' % (task['id'], cron, str(latest_exec_time)))
        next_dt = None
        try:
            iter = croniter(cron, latest_exec_time)
            next_dt = iter.get_next(datetime)
        except Exception as ex:
            log.error("cal next exec time exception:%s, pass this task" % str(ex) )
            continue
        log.info("after cal, last exec time:%s, cron:%s, next exec time:%s" % (latest_exec_time, cron, str(next_dt)) )
        #转换成时间戳，比较
        next_exec_stamp =  time.mktime(next_dt.timetuple())
        #转换成时间戳，比较
        next_exec_stamp =  time.mktime(next_dt.timetuple())
        log.info("next exec stamp:%s, now stamp:%s" % (next_exec_stamp, now_stamp))
        if now_stamp >= next_exec_stamp:
            log.info("cur stamp > next exec stamp, ready to update latest exec time")
            try:
                Orm(mysql_db).table('archive_task').data({'latest_exec_time':dt.current_time()}).where("id", task['id']).update()
            except Exception as ex:
                log.error("update latest exec time exception:%s, pass this task" % str(ex))
                continue
            #发送一个执行消息
            try:
                send_msg(str(task['id']))
            except Exception as ex:
                log.error("send msg to mq exception:%s, pass this task" % str(ex))
                continue
            log.info("send exec msg finish")
            #判断是否只执行一次，如果只执行一次，那么将状态设置为禁用
            if task['is_exec_once'] == 1:
                #发送消息成功，此时将状态设置为禁用
                try:
                    Orm(mysql_db).table('archive_task').data({'status' : 0}).where('id', task['id']).update()
                    log.info("update status to disable succed")
                except Exception as ex:
                    log.error("update status to disable failed:" + str(ex))

def cron_judger_target():
    while 1:
        try:
            cron_judger()
        except Exception as ex:
            log.error("global exception:" + str(ex))
        time.sleep(int(config('CRON_JUDGER_INTVAL')))

def start():
    #cron_judger_target()
    p=Process(target=cron_judger_target)
    p.start()
    return