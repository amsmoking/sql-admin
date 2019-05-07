#coding=utf-8

from common import *
import sys
sys.path.append('../')
from db.mysql import mysql_db
from agileutil.db import Orm, DB
from crontab import CronTab
import logger.logger as log
import zmq
import notify.notify as notify
from model.archive_task import ArchiveTaskModel
from decouple import config

class index(Guest):
    def handle(self):
        self.data['home_title'] = u'慢查询'
        self.data['iframe_href'] = config('SLOW_QUERY_URL')
        return self.render().slow_query(data = self.data)