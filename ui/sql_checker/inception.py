#coding=utf-8

import sqlparse
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
sys.path.append('../../')
import MySQLdb
import demjson
import logger.logger as log
from decouple import config
import rpc.proxy as proxy

OPER_TYPE_EXEC = "execute"
OPER_TYPE_CHECK = "check"

class InceptionResultSet(object):

    def __init__(self):
        self.resultList = []
        #执行前组装的sql,用于排查
        self.runSql = ''
        #执行后inception返回的结果集
        self.rawResultSet = []

    def append(self, result):
        if result == None: return
        self.resultList.append(result)

    def warnings(self):
        warnings = []
        for res in self.resultList:
            if res.errlevel == 1:
                warnings.append(res.errmsg)
        return warnings

    def errors(self):
        errors = []
        for res in self.resultList:
            if res.errlevel == 2:
                errors.append(res.errmsg)
        return errors

    def warningsStr(self):
        string = u"\n".join(self.warnings())
        return string

    def errorsStr(self):
        string = u"\n".join(self.errors())
        '''
        if string == 'Unknown error 1063':
            string = "auto_increment column's type should be int or bigint"
        '''
        return string

    def isHasWarning(self):
        if len(self.warnings()) > 0:
            return True
        else:
            return False

    def isHasError(self):
        if len(self.errors()) > 0:
            return True
        else:
            return False

    def affectRowsMap(self):
        m = {}
        for res in self.resultList:
            sql = res.sql
            affect_rows = res.affectRows
            m [sql] = affect_rows
        return m

    def affectRowsString(self):
        string = ''
        for sql, affect_rows in self.resultList:
            string = string + sql + ":" + str(affect_rows) + '\r\n'
        return string

    def isAffectRowsExceedLimit(self, limitNum):
        limitNum = int(limitNum)
        if limitNum <= 0: return False
        for res in self.resultList:
            sql = res.sql
            affect_rows = res.affectRows
            if affect_rows >= limitNum: return True
        return False

    def getAffectRowsExceedLimitSql(self, limitNum):
        '''
        返回影响行数超过阀值的sql 和 影响的行数
        '''
        for res in self.resultList:
            sql = res.sql
            affect_rows = res.affectRows
            if affect_rows >= limitNum: 
                return sql, affect_rows
        return '', 0

    def getCombiInfoList(self):
        '''
        sql, 影响行数，执行时间,stages
        返回一个list
        '''
        combiList = []
        for res in self.resultList:
            sql = res.sql
            execute_time = res.executeTime
            stage = res.stage
            affect_rows = res.affectRows
            m = {}
            m['sql'] = sql
            m['execute_time'] = execute_time
            m['stage'] = stage
            m['affect_rows'] = affect_rows
            combiList.append(m)
        return combiList

    def getCombiInfoString(self):
        combiList = self.getCombiInfoList()
        string = ''
        for item in combiList:
            sql = item['sql']
            execute_time = str(item['execute_time'])
            stage = str(item['stage'])
            affect_rows = str(item['affect_rows'])
            string = string + sql + "\r\n" + "影响行数:" + affect_rows + ", 执行时间:" + execute_time + ", stage:" + stage + "\r\n" + "\r\n"
        return string

    def getSqlSha1List(self):
        sha1List = []
        for res in self.resultList:
            sqlsha1 = res.sqlsha1
            sha1List.append(sqlsha1)
        return sha1List

class InceptionResult(object):

    def __init__(self):
        #表示检查的sql序号的，每次检查都是从1开始
        self.id = 0
        #1, 警告，不影响执行
        #2， 严重错误，必须修改
        self.errlevel = 0
        #错误信息
        self.errmsg = ''
        #表示当前检查的是哪条sql语句
        self.sql = ''
        #表示当前语句执行时预计影响的行数
        self.affectRows = 0
        #sequence,回滚序号，对应Inception_backup_information表中的opid_time
        self.sequence = 0
        #表示的是当前语句产生的备份信息，存储在备份服务器的哪个数据库中,
        #数据库名由IP地址、端口、源数据库名组成，由下划线连接，而如果是不需要备份的语句，则返回字符串None
        self.backupDbName = ''
        #当前语句执行时间，单位为秒，精确到小数点后两位
        self.executeTime = 0
        #这个列显示当前语句已经进行到哪一步了
        self.stage = ''
        #sha1
        self.sqlsha1 = ''

    def dump(self):
        return demjson.encode({
            'id' : self.id,
            'errlevel' : self.errlevel,
            'errmsg' : self.errmsg,
            'sql' : self.sql,
            'affectRows' : self.affectRows,
            'sequence' : self.sequence,
            'backupDbName' : self.backupDbName,
            'executeTime' : self.executeTime,
            'stage' : self.stage,
            'sqlsha1' : self.sqlsha1
        })

class InceptionDB(object):

    def __init__(self, host = '127.0.0.1', port = 6609):
        self.host = host
        self.port = port

    def commandExecute(self, sql):
        '''
        同self.execute()的区别是，execute执行的是格式化后带inception commit的语句， commandExecute是原生命令
        '''
        log.info("connecting to inception, %s:%s" % (self.host, self.port))
        conn=MySQLdb.connect(host = self.host, port = self.port, user = '', passwd = '', db = '', charset='utf8')
        log.info("connected to inception")
        cur=conn.cursor(MySQLdb.cursors.DictCursor)
        try:
            sql = sql.decode("utf8","ignore")
            log.info("ready to exec sql:%s" % sql)
            ret=cur.execute(sql)
            log.info("exec sql finish, ready fetch result")
        except Exception, ex:
            log.error("exec sql exception:" + str(ex))
        rows=cur.fetchall()
        cur.close()
        conn.commit()
        conn.close()
        log.info("close connection finish")
        return rows

    def encodeTranslate(self, sql):
        try:
            sql = unicode(sql, errors='ignore')
            #sql = unicode(sql).encode('utf-8')
            import chardet
            fencoding=chardet.detect(sql)
            log.info("when run sql, sql encode is"+ str(fencoding))
        except Exception, ex:
            log.error("judge sql encode exception:" + str(ex))
        return sql
        
    def formatSql(self, sql):
        try:
            formatSqlString = sqlparse.format(sql, reindent=True, keyword_case='upper')
            log.info("format sql succed")
            return formatSqlString
        except Exception, ex:
            log.error("format sql exception:" + str(ex))
            return sql

    def defaultSpaceToEmpty(self, sql):
        '''
        inception的一个bug,两个引号中间有空格时，检查时不会报错，执行时会报错，这里在代码级别打了一个补丁
        '''
        if ' ' not in sql: return sql
        lines = sql.split(',')
        copy_lines = []
        for line in lines:
            if 'DEFAULT' in line or 'default' in line:
                if ' ' in line:
                    split_sep = ''
                    if 'DEFAULT' in line:
                        split_sep = 'DEFAULT'
                    if 'default' in line:
                        split_sep = 'default'
                    if split_sep == '':
                        continue
                    items = line.split(split_sep)
                    if len(items) == 2:
                        item = items[1]
                        print 'item:', item
                        words = item.split(' ')
                        no_empty_words = []
                        for word in words:
                            if word == '':
                                continue
                            no_empty_words.append(word)
                        if len(no_empty_words) >= 2:
                            word_1 = no_empty_words[0]
                            word_2 = no_empty_words[1]
                            tag = False
                            if word_1 == "'" and word_2 == "'":
                                tag = True
                            if word_1 == '"' and word_2 == '"':
                                tag = True
                            if tag:
                                log.info("has no empty default space value, line:" + line)
                                #将line还原，将里面的'   '变成''
                                new_line = ''
                                no_empty_words[0] = "''" 
                                no_empty_words[1] = ''
                                tmp = ' '.join(no_empty_words)
                                tmp = items[0] + ' DEFAULT ' + tmp
                                line = tmp
            copy_lines.append(line)
        sql = ','.join(copy_lines)
        return sql
    
    def execute(self, sql):
        sql = self.encodeTranslate(sql)
        log.info("connecting to inception, %s:%s" % (self.host, self.port))
        conn=MySQLdb.connect(host = self.host, port = self.port, user = '', passwd = '', db = '', charset='utf8')
        log.info("connected to inception")
        cur=conn.cursor(MySQLdb.cursors.DictCursor)
        sql = self.defaultSpaceToEmpty(sql)
        log.info("ready to exec sql:%s" % sql)
        try:
            log.info("[exec] sql:" + sql)
            ret=cur.execute(sql)
            log.info("exec sql finish, ready fetch result")
        except Exception, ex:
            log.error("exec sql exception:" + str(ex))
        rows=cur.fetchall()
        log.info("run result set:" + str(rows))
        log.info("fetch result finish, ready to make result set")
        resultSet = InceptionResultSet()
        resultSet.rawResultSet = rows
        if rows == None or len(rows) == 0: return resultSet
        for row in rows:
            result = InceptionResult()
            result.id = row['ID']
            result.errlevel = row['errlevel']
            result.errmsg = row['errormessage']
            result.sql = row['SQL']
            result.affectRows = row['Affected_rows']
            result.sequence = row['sequence']
            result.backupDbName = row['backup_dbname']
            result.executeTime = row['execute_time']
            result.stage = row['stage']
            result.sqlsha1 = row['sqlsha1']
            resultSet.append(result)
        log.info("make result set finish")
        cur.close()
        conn.commit()
        conn.close()
        log.info("close connection finish")
        return resultSet

    def loadVariables(self):
        conn = MySQLdb.connect(host=self.host, port=self.port, user='', passwd='', db='', charset='utf8')
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SET NAMES UTF8')
        sql = 'inception get variables'
        ret=cur.execute(sql)
        rows=cur.fetchall()
        cur.close()
        conn.commit()
        conn.close()
        if rows == None or len(rows) == 0: return []
        return rows

    def updateVariables(self, incParamMap):
        if incParamMap == None or len(incParamMap) == 0: return False
        conn = MySQLdb.connect(host=self.host, port=self.port, user='', passwd='', db='', charset='utf8')
        cur = conn.cursor(MySQLdb.cursors.DictCursor)
        cur.execute('SET NAMES UTF8')
        for vari_name, val in incParamMap.items():
            sql = """inception set %s='%s'""" % (vari_name, val)
            cur.execute(sql)
        cur.close()
        conn.commit()
        conn.close()
        return True
        
class Inception(object):

    def __init__(self, host='127.0.0.1', port = 6609, optHost='127.0.0.1', optPort=3306, optUser='', optPwd=''):
        #inception地址
        self.host = host
        #inception端口
        self.port = int(port)
        #inception连接的mysql地址
        self.optHost = optHost
        #inception连接的mysql端口
        self.optPort = int(optPort)
        #inception连接的myql用的用户名
        self.optUser = optUser
        #inception连接mysql用的密码
        self.optPwd = optPwd
        #行完每一条语句之后，暂停多少毫秒, 范围0-100000， 只有在--enable-execute为1的情况下，才起作用。
        self.optSleep = 0
        #告诉Inception，当在执行过程中碰到一个错误时，是中止执行还是保存错误信息继续执行下一个语句
        self.enableForce = False
        #告诉Inception跳过这个警告的检查，继续执行
        self.enableIgnoreWarn = False
        #是否开启备份, inception默认开启备份
        self.enableRemoteBackup = False
        #如果在语句块中存在对同一个表的DDL操作及DML操作，那么在备份及生成回滚语句分析binlog时，由于表结构已经发生改变，会导致inception没法处理，所以使用这个参数将这些语句分成多批，然后再分别执行
        self.enableSplit = True
        #打印提供SQL语句在被MySQL分析之后的执行树结构，以Json的形式提供
        self.enableQueryPrint = False
        #当前用户的角色 admin, guest
        self.curUserRole = ''
        #检查权限的db
        self.curDb = ''
        #机房 bjxg, pingan
        self.Idc = ''
        

    def makeDefaultHeader(self, optType = OPER_TYPE_CHECK):
        header = ""
        opt_list = [
            "--host=%s" % self.optHost,
            "--port=%s" % self.optPort,
            "--user=%s" % self.optUser,
            "--password=%s" % self.optPwd
        ]
        if optType == OPER_TYPE_CHECK:
            opt_list.append('--enable-check')
        else:
            opt_list.append('--enable-execute')
            if self.enableIgnoreWarn:
                opt_list.append('--enable-ignore-warnings')

            #inception默认支持备份
            if not self.enableRemoteBackup:
                opt_list.append('--disable-remote-backup')
        if self.optSleep > 0:
            opt_list.append("--sleep=%s" % self.optSleep)
        if self.enableForce:
            opt_list.append('--enable-force')    
        if self.enableSplit:
            pass
        if self.enableQueryPrint:
            opt_list.append('--enable-query-print')
        header = "/*" + ';'.join(opt_list) + "*/"
        return header

    def makeDefaultInceptionSql(self, sql, optType = OPER_TYPE_CHECK):
        header = self.makeDefaultHeader(optType)
        sql = header + "inception_magic_start;" + sql + "inception_magic_commit;"
        return sql

    def runInceptionSql(self, sql):
        db = InceptionDB(self.host, self.port)
        resultSet = db.execute(sql)
        resultSet.runSql = sql
        return resultSet

    def checkDestMysqlPermission(self):
        if self.curUserRole == '' and self.curDb == '': return None
        if config('IS_CHECK_PERMISSION') != 'true': return None
        is_has_priv = False
        lack_priv = []
        has_priv = []
        err = ''
        try:
            is_has_priv, lack_priv, has_priv, err = proxy.test_privilege(self.optHost, int(self.optPort), self.optUser, self.optPwd, self.curDb, self.host, self.Idc)
        except Exception, ex:
            return str(ex)
        if err != None: return str(ex)
        if is_has_priv: return None
        if self.curUserRole == 'admin':
            return '缺少权限:' + ', '.join(lack_priv)
        else:
            return '缺少权限, 请联系sre'

    '''
    def checkDestMysqlPermission(self):
        #成功返回None, 出错返回错误信息
        if config("SHOW_GRANTS_ON_IP") == 'false':
            return None
        from agileutil.db import DB
        db = DB(self.optHost, self.optPort, self.optUser, self.optPwd, dbName = '')
        #sql = 'show grants for %s' % (self.optUser)
        local_ip_str = ''
        try:
            import agileutil.util as util
            tmp_list = util.local_ipv4_list()
            local_ipv4_list = []
            for ip in tmp_list:
                if ip != '127.0.0.1':
                    local_ipv4_list.append(ip)
            local_ip_str = ','.join(local_ipv4_list)
        except Exception, ex:
            log.error("get local ipv4 failed:" + str(ex))
            return str(ex)
        sql = "show grants for %s @'%s'" % (self.optUser, local_ip_str)
        log.info("ready to check perimission, sql:" + sql)
        rows = db.query(sql)
        if rows == None or len(rows) == 0:
            return u'用户' + unicode(self.optUser) + u'无super, process, replication slave等权限'
        row = rows[0]
        values = row.values()
        grant = values[0]
        permissionTag = True
        if 'SUPER' not in grant:
            permissionTag = False
        if 'PROCESS' not in grant:
            permissionTag = False
        if 'REPLICATION SLAVE' not in grant:
            permissionTag = False
        if permissionTag == False:
            return u'用户' + unicode(self.optUser) + u'无super, process, replication slave等权限'
        return None
    '''

    def makeErrResultSet(self, err):
        result = InceptionResult()
        result.id = 1
        result.errlevel = 2
        result.errmsg = err
        resultSet = InceptionResultSet()
        resultSet.append(result)
        return resultSet

    def check(self, sql):
        '''
        返回一个结果集
        '''
        #检查sql里是否有两个alter语句，如果有那么报错，提示只允许一个去执行
        tmp_list = sql.split(';')
        alter_num = 0
        for item in tmp_list:
            if ' alter ' in item.lower():
                alter_num = alter_num + 1
        if alter_num > 1:
            result = InceptionResult()
            result.id = 1
            result.errlevel = 2
            result.errmsg = u'一次只能提交一个ALTER语句'
            resultSet = InceptionResultSet()
            resultSet.append(result)
            return resultSet
        err = self.checkDestMysqlPermission()
        if err != None: return self.makeErrResultSet(err)
        sql = self.makeDefaultInceptionSql(sql, OPER_TYPE_CHECK)
        log.info("inception, build sql:" + sql)
        resultSet = self.runInceptionSql(sql)
        return resultSet

    def run(self, sql):
        '''
        返回一个结果集
        '''
        err = self.checkDestMysqlPermission()
        if err != None: return self.makeErrResultSet(err)
        sql = self.makeDefaultInceptionSql(sql, OPER_TYPE_EXEC)
        log.info("inception, run, sql:" + sql)
        resultSet = self.runInceptionSql(sql)
        return resultSet

    def showOscProcessList(self):
        '''
        获取通过osc执行的任务列表
        '''
        sql = 'inception get osc processlist;'
        db = InceptionDB(self.host, self.port)
        rows = db.commandExecute(sql)
        if rows == None or len(rows) == 0: return []
        return rows

    def getOscProcessBySql(self, sql):
        proc = None
        osc_process_list =self.showOscProcessList()
        log.info("sql:" + sql)
        log.info("get osc process list:" + str(osc_process_list))
        if osc_process_list == None or len(osc_process_list) == 0: return proc
        for row in osc_process_list:
            log.info("command:" + str(row['COMMAND']))
            if row['COMMAND'] == None: continue
            if row['COMMAND'] == "" : continue
            if row['COMMAND'] in sql:
                proc = row
                return proc
        return proc

    def showProcessList(self):
        '''
        获取不通过osc执行的任务列表
        '''
        sql = 'inception get processlist;'
        db = InceptionDB(self.host, self.port)
        rows = db.commandExecute(sql)
        print 'showProcessList:', rows
        if rows == None or len(rows) == 0: return []
        return rows

    def getProcessBySql(self, sql):
        proc = None
        process_list = self.showProcessList()
        if process_list == None or len(process_list) == 0: return proc
        for row in process_list:
            if row['Current_Execute'] == None: continue
            if row['Current_Execute'] == '': continue
            if row['Current_Execute'] in sql:
                proc = row
                return proc
        return proc

    @staticmethod
    def makeBackupDbName(host, port, db_name):
        tmp_list = []
        tmp_list.extend(host.split('.'))
        tmp_list.append(str(port))
        tmp_list.append(db_name)
        return '_'.join(tmp_list)