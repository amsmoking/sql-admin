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

def getIndexSummaryByDb(db):
    summary = None
    if db == None: return summary
    sql = """SELECT OBJECT_SCHEMA AS table_schema,OBJECT_NAME AS table_name,INDEX_NAME as index_name,COUNT_FETCH AS rows_selected, SUM_TIMER_FETCH AS select_latency,COUNT_INSERT AS rows_inserted, SUM_TIMER_INSERT AS insert_latency, COUNT_UPDATE AS rows_updated, SUM_TIMER_UPDATE AS update_latency,COUNT_DELETE AS rows_deleted, SUM_TIMER_INSERT AS delete_latency FROM performance_schema.table_io_waits_summary_by_index_usage WHERE index_name IS NOT NULL ORDER BY sum_timer_wait DESC"""
    try:
        summary = db.query(sql)
    except Exception as ex:
        log.warning("getIndexSummaryByDb exception, pass this instance:" + str(ex) )
    return summary

def index_cal_by_instance():
    serverModel = MysqlServerModel()
    servers = serverModel.rows()
    no_use_indexs = []
    for server in servers:
        serverModel.id = server['id']
        instances = serverModel.loadInstances()
        for ins in instances:
            masterIp = server['ip']
            masterPort = int(ins['port'])
            user = ins['remote_user']
            pwd = ins['remote_pwd']
            slaveIp = ins['slave_ip']
            slavePort = int(ins['slave_port'])
            masterDb = DB(masterIp, masterPort, user, pwd, 'performance_schema')
            masterIndexSummary = getIndexSummaryByDb(masterDb)
            if masterIndexSummary == None: continue
            for row in masterIndexSummary:
                index_name = row['index_name']
                table_name = row['table_name']
                rows_inserted = row['rows_inserted']
                rows_deleted = row['rows_deleted']
                rows_updated = row['rows_updated']
                rows_selected = row['rows_selected']
                table_schema = row['table_schema']
                if index_name == 'PRIMARY' : continue
                if table_schema == 'mysql': continue
                if rows_selected == 0 and rows_deleted == 0 and rows_updated == 0:
                    row['instance'] = masterIp + ":" + str(masterPort)
                    no_use_indexs.append(row)
    
    content = '[]'
    if len(no_use_indexs) == 0:
        pass
    else:
        content = demjson.encode(no_use_indexs)

    f = open(config('INDEX_CAL_FILE'), 'w')
    f.write(content)
    f.close()
    log.info("index cal task write file succed")

def index_cal():
    while True:
        index_cal_by_instance()
        try:
            index_cal_by_instance()
            log.info("index cal finish once")
        except Exception as ex:
            log.error("index cal task exception:" + str(ex))
        time.sleep(int(config('INDEX_CAL_INTVAL')))

def start():
    p=Process(target=index_cal)
    p.start()
    return