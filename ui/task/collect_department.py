#coding=utf-8

'''
启动时这里同步一下部门信息，用于添加权限
'''

import sys
sys.path.append('../')
from multiprocessing import Process
from decouple import config
from model.department_model import DepartmentModel
import logger.logger as log
import time
from auth.ldap_auth import *

def run():
    la = LDAPApi(config('LDAP_SERVER'), config('LDAP_BIND'), config('LDAP_PASS'))
    all_groups = []
    err = None
    try:
        all_groups, err = la.get_all_groups()
    except Exception, ex:
        err = str(ex)
    #如果获取失败，那么重试
    if err != None:
        while 1:
            time.sleep(config('COLLECT_DEPART_TASK_SLEEP_INTVAL', cast=int))
            try:
                all_groups, err = la.get_all_groups()
            except Exception, ex:
                err = str(ex)
            if err != None:
                log.warning("get all groups by ldap failed:%s, ready retry" % err)
                continue
            else: break
    log.info("get all groups by ldap succed")
    departmentModel = DepartmentModel()
    department_list = departmentModel.rows()
    depart_en_list = [depart['en_name'] for depart in department_list]
    try:
        depart_en_list.remove('all-user')
    except:
        pass
    to_add = []
    log.info("get all groups is:" + str(all_groups))
    for group in all_groups:
        if group not in depart_en_list:
            if group != 'xueqiu':
                to_add.append(group)
    departmentModel.addEnDepartments(to_add)

'''
def collect_department():
    while True:
        try:
            #run()
            p=Process(target=collect_department)
            p.start()
            log.info("collect department info finish")
        except Exception, ex:
            log.warning("collect department info exception:" + str(ex) )
        time.sleep(60)
'''

def collect_department():
    while True:
        p = Process(target=run)
        p.start()
        time.sleep(60)

def start():
    p=Process(target=collect_department)
    p.start()
    return