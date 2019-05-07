#coding=utf-8

import demjson
from decouple import config
from agileutil.db import DB
import sys
sys.path.append('../')
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_ins_db_model import MysqlInsDbModel
from model.order import OrderModel
from sql_checker.inception import Inception
import logger.logger as log

def rollback(order_id):
    '''
    回滚
    成功返回None
    否则返回出错信息
    '''
    log.info('ready to rollback, order_id:' + str(order_id))
    orderModel = OrderModel()
    serverModel = MysqlServerModel()
    insModel = MysqlInstanceModel()
    insDbModel = MysqlInsDbModel()
    order = orderModel.load(order_id)
    roll_back_times = order['roll_back_times']
    if roll_back_times > 0:
        return u'已经回滚过，不能二次回滚'
    server_id = order['server_id']
    ins_id = order['ins_id']
    ins_db_id = order['ins_db_id']
    server = serverModel.load(server_id)
    ip = server['ip']
    instance = insModel.load(ins_id)
    port = instance['port']
    user = instance['remote_user']
    pwd = instance['remote_pwd']
    ins_db = insDbModel.load(ins_db_id)
    db_name = ins_db['db_name']
    run_result_set = order['run_result_set']
    run_result_set = demjson.decode(run_result_set)
    log.info("get run result set:" + str(run_result_set))
    
    #反转顺序
    run_result_set = list(reversed(run_result_set)) 
    log.info("get reversed run result set:" + str(run_result_set))
    
    #得到sequence列表，用于回滚
    sequence_list = []
    for row in run_result_set:
        affect_rows = row['Affected_rows']
        sequence = row['sequence']
        if affect_rows > 0:
            sequence_list.append(sequence)
    log.info("get sequence list:" + str(sequence_list))
    
    #得到备份库中的数据库名
    backup_db_host = config('BACKUP_DB_HOST')
    backup_db_port = config('BACKUP_DB_PORT', cast=int)
    backup_db_user = config('BACKUP_DB_USER')
    backup_db_pwd = config('BACKUP_DB_PWD')
    backup_db_name = Inception.makeBackupDbName(ip, port, db_name)
    log.info("get backup db info is  %s:%s:%s:%s:%s" % (
        backup_db_host, backup_db_port, backup_db_user, backup_db_pwd, backup_db_name
    ) )

    #从备份库中拿到拼接的sql语句
    rollback_sql, err = get_sql_from_backup_db_by_sequences(
        backup_db_host,
        backup_db_port,
        backup_db_user,
        backup_db_pwd,
        backup_db_name,
        sequence_list
    ) 

    if err != None:
        return err

    #执行拿到的回滚语句
    inc = Inception(
        host = config('INCEPTION_HOST'),
        port = config('INCEPTION_PORT', cast=int),
        optHost = ip,
        optPort = port,
        optUser = user,
        optPwd = pwd
    )
    #回滚的语句不保存
    inc.enableRemoteBackup = False
    resultSet = None
    
    log.info("ready to rollback")
    try:
        resultSet = inc.run(rollback_sql)
    except Exception, ex:
        log.error("exec rollback sql exception:%s" % (str(ex)))
        return str(ex)
    warnTag = resultSet.isHasWarning()
    errorTag = resultSet.isHasError()
    if warnTag == True or errorTag == True:
        errstr = ''
        if warnTag:
            errstr = resultSet.warningsStr()
        if errorTag:
            errstr = resultSet.errorsStr()
        return errstr

    log.info("rollback succed, increase rollback times")
    #rollback次数+1
    orderModel.increaseRollbackTimes(order_id)
    log.info("rollback succed")
    return None

def get_sql_from_backup_db_by_sequences(
    backup_db_host,
    backup_db_port,
    backup_db_user,
    backup_db_pwd,
    backup_db_name,
    sequence_list
):
    '''
    成功返回sql语句，None
    出错返回"", 错误信息
    '''
    backup_db = DB(
        backup_db_host,
        backup_db_port,
        backup_db_user,
        backup_db_pwd,
        backup_db_name
    )
    
    backup_info_list = []

    #得到备份记录的信息，主要是为了得到一个语句在哪个表中
    for sequence in sequence_list:
        sequence = sequence.replace("'", '')
        print sequence
        sql = "select * from $_$Inception_backup_information$_$ where opid_time='%s'" % (sequence)
        rows = backup_db.query(sql)
        if rows == None or len(rows) == 0:
            return "", u"某些语句的备份记录查询不到"
        row = rows[0]
        backup_info_list.append(row)
    
    #从对应表中得到回滚的sql语句
    rollback_sql_list = []
    for backup_info in backup_info_list:
        opid_time = backup_info['opid_time']
        table_name = backup_info['tablename']
        sql = "select * from %s where opid_time='%s'" % (table_name, opid_time)
        rows = backup_db.query(sql)
        if rows == None or len(rows) == 0:
            return "", u"备份语句查询不到"
        for row in rows:
            rollback_sql_list.append(row['rollback_statement'])

    rollback_sql = ' '.join(rollback_sql_list)
    log.info("get rollback sql is:" + rollback_sql)
    return rollback_sql, None