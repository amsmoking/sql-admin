#coding=utf-8

import time
from common_model import *
import agileutil.date as dt
import sys
sys.path.append('../')
from db.mysql import mysql_db
from agileutil.db import Orm, DB

class ArchiveTaskModel(CommonModel):
    
    '''
    <option value="0">与原表名一致</option>
    <option value="1">原表名 + “_” + 时间戳</option>
    <option value="2">原表名 + “_” + 年</option>
    <option value="3">原表名 + “_” + 年_月</option>
    <option value="4">原表名 + “_” + 年_月_日</option>
    <option value="5">原表名 + “_” + 年_月_日_时_分_秒</option>
    <option value="6">自定义</option>
    '''
    
    TABLE_TYPE_SAME = 0
    TABLE_TYPE_STAMP = 1
    TABLE_TYPE_Y = 2
    TABLE_TYPE_Y_M = 3
    TABLE_TYPE_Y_M_D = 4
    TABLE_TYPE_Y_M_D_H_M_S = 5
    TABLE_TYPE_SELF_DEFINE = 6

    @classmethod
    def genSuffix(cls, tableType):
        tableType = int(tableType)
        if tableType == ArchiveTaskModel.TABLE_TYPE_SAME:
            return ''
        elif tableType == ArchiveTaskModel.TABLE_TYPE_STAMP:
            return '_' + str(int(time.time()))
        elif tableType == ArchiveTaskModel.TABLE_TYPE_Y:
            return '_' + dt.current_time()[0:4]
        elif tableType == ArchiveTaskModel.TABLE_TYPE_Y_M:
            return '_' + '_'.join([
                dt.current_time()[0:4],
                dt.current_time()[5:7]
            ])
        elif tableType == ArchiveTaskModel.TABLE_TYPE_Y_M_D:
            return '_' + '_'.join([
                dt.current_time()[0:4],
                dt.current_time()[5:7],
                dt.current_time()[8:10]
            ])
        elif tableType == ArchiveTaskModel.TABLE_TYPE_Y_M_D_H_M_S:
            return '_' + '_'.join([
                dt.current_time()[0:4],
                dt.current_time()[5:7],
                dt.current_time()[8:10],
                dt.current_time()[11:13],
                dt.current_time()[14:16],
                dt.current_time()[17:19]
            ])
        else:
            return ''

    @classmethod
    def genTableName(cls, tableType, srcTableName, dstTableName = ''):
        if dstTableName != '': return dstTableName
        return srcTableName + ArchiveTaskModel.genSuffix(tableType)

    def __init__(self):
        self.tableName = 'archive_task'

    def addTask(self, dataMap):
        return Orm(mysql_db).table(self.tableName).data(dataMap).insert()

    def reverseStatus(self, id):
        id = int(id)
        task = self.load(id)
        status = task['status']
        if status == 0:
            status = 1
        else:
            status = 0
        return Orm(mysql_db).table(self.tableName).data({'status':status}).where('id', id).update()