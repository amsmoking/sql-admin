#coding=utf-8

'''
这个任务里，定时统计一下各个库的索引的使用情况
'''

import sys
sys.path.append('../')
from multiprocessing import Process
from decouple import config
from model.department_model import DepartmentModel
from model.mysql_server_model import MysqlServerModel
from model.sql_task_model import SqlTaskModel
import logger.logger as log
import time
from auth.ldap_auth import *
from agileutil.db import DB
import os
import commands

def check_defunct():
    cmd = "ps -ef | grep defunct | grep -v grep | wc -l"
    status, output = commands.getstatusoutput(cmd)
    defunct_num = int(output)
    threshold = int(config('RESTART_INCEPTION_DEFUNCT_THRESHOLD'))
    if defunct_num >= threshold:
        log.info("[check defunct] defunct num:%s >= threshold:%s" % (defunct_num, threshold))
        #检查当前是否有异步任务在执行
        execingTask = SqlTaskModel().getOneExecingTask()
        if execingTask == None:
            log.info("[check defunct] no execing task, ready restart inception")
            cmd = config('RESTART_INCEPTION_CMD')
            status, output = commands.getstatusoutput(cmd)
            log.info("[check defunct], cmd:%s, status:%s, output:%s" % ( cmd, status, output) )
        else:
            log.info("[check defunct] has one execing task, not restart, pass")
    log.info("[check defunct] check once")
    return defunct_num

def loop_check():
    while 1:
        time.sleep(int(config('CHECK_DEFUNCT_INTVAL')))
        try:
            defunct_num = check_defunct()
            log.info("[check defunct] check once, defunct num:" + str(defunct_num))
        except Exception as ex:
            log.error("[check defunct] check exception:" + str(ex))

def start():
    p=Process(target=loop_check)
    p.start()
    return