#coding=utf-8

from common_model import *
import agileutil.date as dt

class AutoVerifyModel(CommonModel):
    
    def updateAutoVerify(self, beginTime, endTime, enable = 0, isSendMail = 0, tos = ''):
        sql = "select * from auto_verify"
        rows = self.query(sql)
        insertTag = False
        if rows == None or len(rows) == 0:
            insertTag = True
        if insertTag == True:
            sql = "insert into auto_verify(begin_time, end_time, enable, is_send_mail, tos) values('%s', '%s', %s, %s, '%s')" % (
                beginTime, endTime, enable, isSendMail, tos)
        else:
            id = rows[0]['id']
            sql = "update auto_verify set begin_time='%s', end_time='%s', enable=%s, is_send_mail=%s, tos='%s' where id=%s" % (
                beginTime, endTime, enable, isSendMail, tos, id)
        return self.update(sql)

    def loadAutoVerify(self):
        sql = "select * from auto_verify"
        rows = self.query(sql)
        if rows == None or len(rows) == 0:
            return {
                'begin_time' : '',
                'end_time' : '',
                'enable' : 0,
                'is_send_mail' : 0,
                'tos' : ''
            }
        else:
            return rows[0]