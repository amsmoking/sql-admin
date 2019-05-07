#coding=utf-8

from common_model import *
import agileutil.date as dt

class QueryHistoryModel(CommonModel):

    def getQueryHistory(self, domain_name, limit = 50):
        sql = "select * from query_history where domain_name = '%s' order by id desc limit %s" % (domain_name, limit)
        rows = self.query(sql)
        if rows == None: rows = []
        for row in rows:
            query_time = row['query_time']
            print 'query_time', query_time
            row['query_time'] = dt.datestr_to_zh_time(query_time)
        return rows

    def getByDateRange(self, startDate, endDate):
        sql = "select id, query_time from query_history where query_time >= '%s' and query_time <= '%s'" % (startDate, endDate)
        rows = self.query(sql)
        if rows == None: rows = []
        return rows