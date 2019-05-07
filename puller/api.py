#coding=utf-8

import log
import agileutil.util as util
from decouple import config
import demjson

class Api(object):

    def __init__(self):
        pass

    @staticmethod
    def getMysqlServers():
        url = config('API_URL') + config('GET_MYSQL_SERVERS_URI')
        token = config('PULLER_TOKEN')
        url = url + "?token=" + token
        code, resp = util.http(url)
        if code != 200:
            log.error('getMysqlServers() failed, url:%s, code:%s, resp:%s' % (url, code, resp))
            return None
        data = demjson.decode(resp)
        if data['errno'] != 0:
            log.error('getMysqlServers() resp errno is %s' % data['errno'])
            return None
        return data['data']
    
    @staticmethod
    def getInstanceByServerId(serverId):
        url  = config('API_URL') + config('GET_INS_BY_SERVER_ID_URI')
        token = config('PULLER_TOKEN')
        params = {'token':token, 'server_id':serverId}
        code, resp = util.http(url,params)
        if code != 200:
            log.error('getInstanceByServerId() failed, url:%s, code:%s, resp:%s' % (url, code, resp))
            return None
        data = demjson.decode(resp)
        if data['errno'] != 0:
            log.error('getInstanceByServerId() resp errno is %s' % data['errno'])
            return None
        return data['data']

    @staticmethod
    def getDbsByInsId(insId):
        url = config('API_URL') + config('GET_DBS_BY_INS_ID_URI')
        token = config('PULLER_TOKEN')
        params = {'token':token, 'ins_id':insId}
        code, resp = util.http(url, params)
        if code != 200:
            log.error('getDbsByInsId() failed, url:%s, code:%s, resp:%s' % (url, code, resp))
            return None
        data = demjson.decode(resp)
        if data['errno'] != 0:
            log.error('getDbsByInsId() resp errno is %s' % data['errno'])
            return None
        return data['data']

    @staticmethod
    def delDbsByInsId(insId, toDelDbList):
        if toDelDbList == None or len(toDelDbList) == 0: return False
        url = config('API_URL') + config('DEL_DBS_BY_INS_ID_URI')
        token = config('PULLER_TOKEN')
        params = {'token':token, 'ins_id':insId, 'to_del_dbs':','.join(toDelDbList)}
        code, resp = util.http(url, params)
        if code != 200:
            log.error('delDbsByInsId() failed, url:%s, code:%s, resp:%s' % (url, code, resp))
            return False
        data = demjson.decode(resp)
        if data['errno'] != 0:
            log.error('delDbsByInsId() resp errno is %s' % data['errno'])
            return False
        log.info("del database, ins_id:%s, toDelDbList:%s" % (insId, str(toDelDbList)))
        return True

    @staticmethod
    def addDbByInsId(insId, dbName, doc):
        url = config('API_URL') + config('ADD_DB_BY_INS_ID_URI')
        token = config('PULLER_TOKEN')
        params = {'token':token, 'ins_id':insId, 'db_name':dbName, 'doc':doc}
        print "params,", params
        code, resp = util.http(url, params)
        print "code, resp", code, resp
        if code != 200:
            log.error('addDbByInsId() failed, url:%s, code:%s, resp:%s' % (url, code, resp))
            return False
        data = demjson.decode(resp)
        if data['errno'] != 0:
            log.error('addDbByInsId() resp errno is %s' % data['errno'])
            return False
        return True

    @staticmethod
    def addDbsByInsId(insId, toAddDbList):
        if toAddDbList == None or len(toAddDbList) == 0: return False
        ret = True
        for database in toAddDbList:
            result = Api.addDbByInsId(insId, database.name, database.document())
            if result == False: ret = False
        return ret

    @staticmethod
    def updatePullerStatus(insId, puller_status, puller_errmsg):
        url = config('API_URL') + config('UPDATE_PULLER_STATUS_URI')
        token = config('PULLER_TOKEN')
        params = {'token':token, 'ins_id':insId, 'puller_status':puller_status, 'puller_errmsg':puller_errmsg}
        code, resp = util.http(url, params)
        if code != 200:
            log.error('updatePullerStatus() failed, url:%s, code:%s, resp:%s' % (url, code, resp))
            return False
        data = demjson.decode(resp)
        if data['errno'] != 0:
            log.error('updatePullerStatus() resp errno is %s' % data['errno'])
            return False
        return True