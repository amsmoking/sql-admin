#coding=utf-8

'''
确保mysqldump已经安装，并且已经在环境变量中
'''

import time
import sys
sys.path.append('../')
from multiprocessing import Process
from agileutil.log import Log
from decouple import config
import zmq
from db.mysql import mysql_db
from agileutil.db import DB, Orm
from datetime import datetime
import os
import agileutil.util as util
import agileutil.date as dt
from agileutil.db import DB
import pymysql
import notify.notify as notify
from model.archive_task import ArchiveTaskModel
import signal

'''
生成的sql文件名称为:
IP_端口_库名_表名_当前时间戳.sql
'''

log = Log(config('CRON_EXECUTOR_LOG'))
log.setOutput(True)

#mysqldump --skip-lock-tables --single-transaction --flush-logs --hex-blob --master-data=2 -uroot -pqihoo360 --ignore-table=falcon.moni_speed_detail --ignore-table=falcon.host --ignore-table=falcon.moni_data_minute_max --ignore-table=falcon.moni_data_month --ignore-table=falcon.moni_speed_history --ignore-table=falcon.moni_data_minute --ignore-table=falcon.moni_item --ignore-table=falcon.moni_data_day --ignore-table=falcon.moni_data_minute_sum --ignore-table=falcon.moni_data_hour --databases falcon ops_server transfer_center > falcon_db.sql  

class DumpResult:
    '''
    备份一个task时(多个表)的导出结果
    '''
    def __init__(self):
        self.dump_suc_table_list = []
        self.dump_fail_table_list = []


def mysql_dump(task):
    '''
    备份源表数据, mysqldump带where条件，dump出来
    成功返回备份文件路径（列表）,  None
    否则返回[], 错误信息
    遇到一个备份错误就终止
    '''
    tables =    list( set( [ item.strip() for item in task['to_archive_tables'].split(',') ] ) )
    dump_suc_table_list = []
    dump_fail_table_list = []
    for table in tables:
        sql_file_name = "%s_%s_%s_%s_%s_%s.sql" % (
            task['src_host'],
            task['src_port'],
            task['src_db'],
            table, 
            task['id'],
            int(time.time())
        )
        log.info("[archive] gen sql file name: " + sql_file_name)
        backup_dir = config('ARCHIVE_BACKUP_DIR')
        if backup_dir[-1] != '/': backup_dir = backup_dir + '/'
        try:
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
                log.info("[archive] mkdir " + backup_dir)
        except Exception as ex:
            log.error("try to create backup dir exception:"+ str(ex))
        sql_file = backup_dir + sql_file_name
        log.info("[archive] gen sql file path: " + sql_file)
        where = task['where']
        if where != '':
            if 'where' in where.lower():
                where = where.replace('where', '')
                where = where.replace('WHERE', '')
                where = where.replace('Where', '')
            where = '--where="' + where + '"'
        else:
            where = ''
        cmd = "mysqldump -h%s -P%s -u'%s' -p'%s' --skip-lock-tables --single-transaction --flush-logs --hex-blob --master-data=2 %s %s %s > %s" % (
            task['src_host'], task['src_port'], task['src_user'], task['src_pwd'], where , task['src_db'], table, sql_file
        )
        log.info("[archive] gen mysqldump cmd:" + cmd)
        log.info("[archive] ready to exec mysqldump")
        status, output = util.execmd(cmd)
        log.info("[archive] after exec mysqldump, status:%s, output:%s" % (status, output))
        if status == 0:
            log.info("[archive] exec mysqldump succed, save to: " + sql_file)
            dump_suc_table_list.append(table)
        else:
            log.error("exec mysqldump failed")
            return [], str(output)

    return dump_suc_table_list, None
    
'''
pt-archiver --source h=192.168.1.4,P=3306,u='xdev',p='xdev',D=xcrypto,t=user_info1 \
--dest h=192.168.1.4,P=3306,u='xdev',p='xdev',D='sys',t=user_info2 \
 --where 'id<6000' --statistics --no-delete --charse=UTF8MB4 --limit 500 --txn-size 500 --progress 10  --bulk-delete  --local --retries 2
'''

def pt_archive(task):
    '''
    执行归档逻辑
    成功返回 output, None
    出错返回 output, 错误信息
    '''
    src_host = task['src_host']
    src_port = int(task['src_port'])
    src_user = task['src_user']
    src_pwd = task['src_pwd']
    src_db = task['src_db']

    dst_host = task['dst_host']
    dst_port = task['dst_port']
    dst_user = task['dst_user']
    dst_pwd = task['dst_pwd']
    dst_db = task['dst_db']

    tables = [ item.strip() for item in task['to_archive_tables'].split(',') ]
    tables.sort()

    where = ''
    if task['where'] != '':
        where = """ --where " """ + task['where'].replace('where', '').replace('WHERE', '') + """ " """  
    else:
        where = """ --where "1=1" """

    delete = '--no-delete'
    if int(task['is_del_src_data']) == 1: 
        log.info('[archive] is del src data is enable')
        delete = '--purge'
    else:
        log.info('[archive] is del src data is disable')
    
    charset = task['charset']
    limit = 2000
    txn_size = 2000
    progress = 1000
    retries = 2

    for table in tables:
        dst_table_name = ArchiveTaskModel.genTableName(task['dst_table_type'], table, task['dst_table'])
        cmd = "pt-archiver --source h=%s,P=%s,u='%s',p='%s',D=%s,t=%s " % (src_host, src_port, src_user, src_pwd, src_db, table)
        cmd = cmd + "  --dest h=%s,P=%s,u='%s',p='%s',D='%s',t=%s " % (dst_host, dst_port, dst_user, dst_pwd, dst_db, dst_table_name)
        cmd = cmd + " %s --statistics %s --charset=%s --limit %s --txn-size %s --progress %s  --bulk-delete  --local --retries %s" % (
            where, delete, charset, limit, txn_size, progress, retries
        )
        log.info("[archive] gen archive cmd: " + cmd)
        log.info("[archive] ready to exec archive cmd")
        status, output = util.execmd(cmd)
        log.info("status:%s, output:%s" % (status, output) )
        if status != 0:
            return output, "exec archive failed:" + output
    
    return 'all tables archive succed', None

def ensure_dst_table_exist(task):
    '''
    若表不存在，尝试创建
    '''

    tables = [ item.strip() for item in task['to_archive_tables'].split(',') ]

    src_db = DB(
        task['src_host'],
        int(task['src_port']),
        task['src_user'],
        task['src_pwd'],
        task['src_db'],
        ispersist = True
    )

    dst_db = DB(
        task['dst_host'],
        int(task['dst_port']),
        task['dst_user'],
        task['dst_pwd'],
        task['dst_db'],
        ispersist = True
    )

    for table in tables:
        dst_table_name = ArchiveTaskModel.genTableName(task['dst_table_type'], table, task['dst_table'])
        sql = "show create table %s" % table
        rows = src_db.query(sql)
        row = rows[0]
        create_sql = row['Create Table']
        log.info("[archive] src db show create table: " + create_sql)
        create_sql = create_sql.replace(
            "CREATE TABLE `%s`" % table, 
            "CREATE TABLE IF NOT EXISTS %s" % dst_table_name
        )
        log.info("[archive] if not exist create sql: " + create_sql)
        #在目的mysql中执行
        dst_db.update(create_sql)
        log.info("[archive] ensure table exists succed")

def safe_archive(task_id):
    '''
    执行归档
    1.获取task详细信息
    2.mysqldump备份源表的数据(带where条件)
    3.调用pt-archive归档，获取输出内容
    4.保存执行日志

    成功返回output, None
    否则返回'', 错误信息
    '''
    log.info("[archive] ready to archive, task id:" + task_id)
    task = Orm(mysql_db).table("archive_task").where("id", int(task_id)).first()
    if task == None or len(task) == 0:
        return '', 'task id %s not found in db' % task_id

    sql_file = ''
    output = ''

    #备份
    if task['is_backup'] == 1:
        log.info("[archive] is_backup is enable, ready backup")
        suc_table_list, err = mysql_dump(task)
        if err != None:
            log.error("[archive] has table backup failed:" + err)
            return '', err
        else:
            log.info("[archive] backup succed")
    else:
        log.info("[archive] is_backup is disable, not backup")
    
    #确定目标表是否存在
    if task['dst_if_no_create'] == 1:
        err = None
        try:
            err = ensure_dst_table_exist(task)
        except Exception as ex:
            return '', str(ex)
        if err != None:
            return '', err

    #准备开始归档
    ar_output, err = pt_archive(task)
    return ar_output, err

def add_archive_exec_log(task_id, start_time, end_time, bak_file, status, output):
    Orm(mysql_db).table('archive_log').data({
        'task_id' : int(task_id),
        'start_time' : start_time,
        'end_time' : end_time,
        'bak_file' : bak_file,
        'status' : int(status),
        'output' : pymysql.escape_string(output) 
    }).insert()

def chldhandler(signum, stackframe):
    log.info('[archive] recv signal:' + str(signum) )
    try:
        result = os.waitpid(-1, os.WNOHANG)
        log.info('[archive] os.waitpid succed')
    except Exception as ex:
        log.error('[archive] os.waitpid failed:' + str(ex))
    log.info('[archive] handle SIGCHLD finish')

def archive_target(task_id):
    try:
        import setproctitle
        setproctitle.setproctitle("xsql_archive_task_" + str(task_id))
        log.info('[archive] set proc title succed')
    except Exception as ex:
        log.error("[archive] set proc title failed:" + str(ex))
    #开始执行时间
    start_time = dt.current_time()
    output, err = safe_archive(task_id)
    #结束执行时间
    end_time = dt.current_time()
    status = 0
    if err != None:
        log.info("[archive] exec archive task failed:" + err)
        status = 1
        notify.send_alarm('xsql', '[archive] exec task failed, task id:' + str(task_id) + " error:" + err)
    if err != '':
        output = output + ' ' + str(err)
    try:
        add_archive_exec_log(task_id, start_time, end_time, '', status, output)
        log.info("[archive] add archive log finish")
    except Exception as ex:
        log.error("[archive] add archive log exception:" + str(ex))
    sys.exit(0)

def cron_executor_target():
    #try:
    #    signal.signal(signal.SIGCHLD, chldhandler)
    #    log.info('[archive] set SIGCHLD signal handler succed')
    #except Exception as ex:
    #    log.error('[archive] set SIGCHLD signal handler failed:' + str(ex) )
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind(config('MQ_ADDR'))
    log.info("[archive] start listen...")
    while 1:
        task_id = socket.recv()
        socket.send('recieved')
        log.info("[archive]recv msg:" + task_id)
        log.info("[archive] ready to start archive process")
        p=Process(target=archive_target, args= (task_id,))
        p.start()


def start():
    p=Process(target=cron_executor_target)
    p.start()
    return