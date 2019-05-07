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
import logger.logger as log
import time
from auth.ldap_auth import *
from agileutil.db import DB
import os

def session_clean():
    session_path = config('SESSION_PATH')
    if session_path[-1] != '/': session_path = session_path + '/'
    files = os.listdir(session_path)
    cur_time = time.time()
    expire_time = int(config('SESSION_EXPIRE'))
    for filename in files:
        filepath = session_path + filename
        m_time = os.stat(filepath).st_mtime
        diff_time = cur_time - m_time
        if diff_time >= expire_time:
            log.info("[session clean] file:%s, diff_time:%s > expire_time:%s, ready delete this file" % (filename, diff_time, expire_time) )
            try:
                os.remove(filepath)
                log.info("[session clean] delete file succed")
            except Exception as ex:
                log.error("[session clean] delete file exception:" + str(ex))

def loop_clean():
    while 1:
        time.sleep(int(config('SESSION_CLEAN_INTVAL')))
        try:
            session_clean()
            log.info("[session clean] clean session once")
        except Exception as ex:
            log.error("[session clean] clean session exception:" + str(ex))

def start():
    p=Process(target=loop_clean)
    p.start()
    return