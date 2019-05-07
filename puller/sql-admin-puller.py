#coding=utf-8

from api import Api
from decouple import config
import time
import log
from mysql import Instance
import demjson
import sys

def del_dbs(insId, to_del_db_list):
    if to_del_db_list == None or len(to_del_db_list) == 0: return
    ret = Api.delDbsByInsId(insId, to_del_db_list)
    if ret:
        log.info("del instance db succed, del dbs:%s, ins_id:%s" % (
            str(to_del_db_list), insId ))
    else:
        log.error("del instance db failed, to del dbs:%s, ins_id:%s" % (
            str(to_del_db_list), insId ))

def add_dbs(insId, to_add_db_obj_list):
    if to_add_db_obj_list == None or len(to_add_db_obj_list) == 0: return
    ret = Api.addDbsByInsId(insId, to_add_db_obj_list)
    to_add_db_name_list = [ database.name for database in to_add_db_obj_list ]
    if ret:
        log.info("add instance db succed, add dbs:%s, ins_id:%s" % (
            str(to_add_db_name_list), insId ))
    else:
        log.error("add instance db failed, to add dbs:%s, ins_id:%s" % (
            str(to_add_db_name_list), insId ))

def update_by_ins(insObj, insId):
    log.info("ready update instance's db")
    if insObj == None: return
    dbs = Api.getDbsByInsId(insId)
    src_db_name_list = [ db['db_name'].strip() for db in dbs ]
    new_db_name_list = [ database.name.strip() for database in insObj.databases ]
    to_add = []
    to_del = []
    for database in insObj.databases:
        if database.name not in src_db_name_list:
            to_add.append(database)
    for db_name in src_db_name_list:
        if db_name not in new_db_name_list:
            to_del.append(db_name)
    #print "to_add", to_add
    #print "to_del", to_del
    #删除旧的db
    del_dbs(insId, to_del)
    #添加需要添加的db
    add_dbs(insId, to_add)

def pull_by_instance(ip, ins):
    if ins == None: return
    port = ins['port']
    remote_user = ins['remote_user']
    remote_pwd = ins['remote_pwd']
    insObj = Instance()
    insObj.ip = ip
    insObj.port = port
    insObj.user = remote_user
    insObj.pwd = remote_pwd
    insObj.detect()
    if insObj.pullerStatus == 'ok':
        log.info("%s:%s:%s:%s connect succed" % (ip, port, remote_user, remote_pwd))
        log.info("ready update puller status to ok")
        Api.updatePullerStatus(ins['id'], insObj.pullerStatus, insObj.pullerErrmsg)
        log.info("instance detect table structure finish")
        log.info("ready update instance, %s:%s:%s:%s" % (ip, port, remote_user, remote_pwd))
        update_by_ins(insObj, ins['id'])
        log.info("update instance, %s:%s:%s:%s finish" % (ip, port, remote_user, remote_pwd))
    else:
        log.error("%s:%s:%s:%s connect failed" % (ip, port, remote_user, remote_pwd))
        log.error("ready update pull status to failed")
        Api.updatePullerStatus(ins['id'], insObj.pullerStatus, insObj.pullerErrmsg)
        if len(insObj.databases) > 0: update_by_ins(insObj, ins['id'])

def pull_by_server(server):
    if server == None: return
    ip = server['ip']
    server_id = server['id']
    instances = Api.getInstanceByServerId(server_id)
    if instances == None:
        log.error("get mysql instance failed, server_id:%s" % server_id)
        return
    log.info("get mysql instance by api succed, count:%s" % len(instances))
    for ins in instances:
        pull_by_instance(ip, ins)

def main():
    log.info("reay pull")
    mysql_servers = Api.getMysqlServers()
    if mysql_servers == None: 
        log.error("get mysql server by api return None")
        return
    log.info("get mysql servers by api succed, count:%s" % len(mysql_servers))
    for server in mysql_servers:
        pull_by_server(server)
    log.info("end pull")

if __name__ == '__main__':
    while True:
        if config('DEBUG') != 'true': 
            log.info('sleep')
            time.sleep(config('SLEEP_INTVAL', cast=int)) 
        try:
            main()
        except Exception, ex:
            log.error("global exception:%s" % str(ex))