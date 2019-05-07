#coding=utf-8

from common import *
import sys
sys.path.append('../')
from model.mysql_instance_model import MysqlInstanceModel

class get_ins_by_server_id(NoAuth):
    def handle(self):
        serverId = self.request('server_id')
        self.safeId(serverId)
        model = MysqlInstanceModel()
        rows = model.loadInstanceByServerId(serverId)
        return self.resp(data=rows)

class get_ins_db_by_ins_id(NoAuth):
    def handle(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        dbs = MysqlInstanceModel().loadDbsByInsId(ins_id)
        #这里过滤掉mysql自带的几个数据库information_schema,mysql,performance_schema
        if dbs == None: dbs = []
        filer_db_name_list = config('FILTER_DB_NAME_LIST').split(',')
        ret_dbs = []
        for db in dbs:
            if db['db_name'] in filer_db_name_list: continue
            ret_dbs.append(db)
        return self.resp(data=ret_dbs)

class get_ins_by_id(NoAuth):
    def handle(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        ins = MysqlInstanceModel().load(ins_id)
        return self.resp(data = ins)