#coding=utf-8

from common import *
from agileutil.db import DB, Orm
import agileutil.date as dt
import pymysql
import demjson
import pandas
import collections
import sys
reload(sys)
sys.setdefaultencoding('utf-8') 
sys.path.append('../')
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_ins_db_model import MysqlInsDbModel
import logger.logger as log
import sql_checker.parse as sql_parse
from sql_checker.inception import Inception
from db.mysql import mysql_db
import xlwt
import time
import web
import os
import agileutil.util as util

MAX_LIMIT_ROWS = 3000

class online_query(Guest):

    def handle(self):
        self.isHasSlave = -1
        is_export = self.request('is_export')
        sql = self.request('sql')
        if sql == '': 
            return self.resp(errno=1, errmsg='empty sql')
        tableData = self.getTableData()
        if is_export == 'true':
            if config('IS_CHECK_ALL_PERMI') == 'true':
                if self.session('domain_name') not in config('ALLOW_EXPORT_USERS').split(','):
                    raise web.seeother('/sql/query_index')
            return self.export(tableData)
        col_len = len(tableData['cols'][0])
        width = (col_len + 1) * 150
        errno = 0
        if len(tableData['cols'][0]) == 1 and tableData['cols'][0][0]['title'] == 'error' :
            #查询出错
            errno = 1
            width = 800
        ret = {'errno':errno, 'errmsg':'', 'data':tableData, 'width':width, 'is_has_slave' : self.isHasSlave}
        return demjson.encode(ret)

    def getDangerCols(self):
        '''
        过滤敏感数据
        '''
        sql = self.request('sql')
        table = sql_parse.get_table_by_select_sql(sql)
        if table == None: return []
        insDbModel = MysqlInsDbModel()
        ins_db_id = self.request('ins_db_id')
        insDb = insDbModel.load(ins_db_id)
        db_name = insDb['db_name']
        hashname = "%s_%s" % (db_name, table)
        file = './export_rules/%s.json' % hashname
        content = ''
        try:
            f = open(file, 'r')
            content = f.read()
            f.close()
        except:
            pass
        dangerCols = []
        try:
            dangerCols = demjson.decode(content)
        except:
            pass
        return dangerCols

    def export(self, data):
        dangerCols = self.getDangerCols()
        log.info("get dange cols is:" + str(dangerCols))
        if data == None: data = []
        rows = data['rows']
        cols = data['cols'][0]
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet('Sheet1',cell_overwrite_ok=True)
        #title
        i = 0
        for j in xrange(len(cols)):
            sheet.write(i,j,cols[j]['field'])
        #content
        for i in xrange(len(rows)):
            j = 0
            for k,v in rows[i].items():
                val = v
                if k in dangerCols and v != None and v != '':
                    tmp_str = ''
                    for k in range(len(v)):
                        tmp_str = tmp_str + '*'
                    val = tmp_str
                sheet.write(i+1,j,val)
                j = j + 1
        filename = str(int(time.time()))+'.xls'
        file = '/tmp/' + filename
        wbk.save(file)
        web.header('Content-Type','application/octet-stream')
        web.header('Content-disposition', 'attachment; filename=%s' % filename)
        f = open(file, 'rb')
        bufsize = 10240
        while 1:
            c = f.read(bufsize)
            if c:
                yield c
            else:
                break
        f.close()
        try:
            os.remove(file)
        except Exception as ex:
            log.warning("delete export file:%s failed:%s" %  (file, ex))
    
    def getTableData(self):
        sql = self.request('sql')
        server_id = self.request('server_id')
        ins_id = self.request('ins_id')
        ins_db_id = self.request('ins_db_id')
        limitRows = self.getSafeLimit(self.request('limit_rows'))
        serverModel = MysqlServerModel()
        insModel = MysqlInstanceModel()
        insDbModel = MysqlInsDbModel()
        server = serverModel.load(server_id)
        ins = insModel.load(ins_id)
        insDb = insDbModel.load(ins_db_id)
        #取到第一个sql
        cur_user = self.session('domain_name')
        log.info("[online_query], user:%s, db:%s, all sql:%s" % (cur_user, insDb['db_name'] , sql))
        sql = sql.split(';')[0]
        log.info("[online_query], user:%s, db:%s, first sql:%s" % (cur_user, insDb['db_name'], sql))

        #优化建议
        optmize = ''

        #检查关键字
        kw = sql_parse.not_all_execute_kw(sql)
        if kw != None:
            return {
                'cols' : self.makeCols(['error']),
                'rows' : [
                    {'error' : u'不允许 ' + kw},
                ],
                'optmize' : optmize,
            }

        #检查是否配置了从库
        isHasSlave = False
        slaveIp = ins['slave_ip'].strip()
        slavePort = ins['slave_port']
        #主库信息
        optHost = server['ip']
        optPort = int(ins['port'])
        optUser = ins['remote_user']
        optPwd = ins['remote_pwd']
        if slaveIp != '' and slavePort >= 0 and slavePort <= 65535:
            isHasSlave = True
            #从库信息
            optHost = slaveIp
            optPort = slavePort
            log.info('has slave, query will on slave instance, %s:%s' % (optHost, optPort))
        else:
            log.info('no slave, query will on master instance, %s:%s' % (optHost, optPort) )
        self.isHasSlave = isHasSlave

        #调用inception,检查是否有写操作
        try:
            tmp_sql = sql
            tmp_sql =  "use `%s`;%s" % (insDb['db_name'], tmp_sql)
            if tmp_sql[-1] != ';': tmp_sql = tmp_sql + ';'
            idc, _ = self.getIdcByHostname(server['hostname'])
            inc_host, inc_port = self.getIncHostPortByIdc(idc)
            inc = Inception(
                host = inc_host,
                port = inc_port,
                optHost = optHost,
                optPort = optPort,
                optUser = optUser,
                optPwd = optPwd
            )
            resultSet = inc.check(tmp_sql)
            for res in resultSet.resultList:
                if res.affectRows > 0:
                    return {
                        'cols' : self.makeCols(['error']),
                        'rows' : [
                            {'error' : u'不允许修改数据, SQL: ' + res.sql}
                        ],
                        'optmize' : optmize,
                    }
        except Exception as ex:
            log.warning("[online_query], inception check affect rows exception:" + str(ex))

        ###获取优化建议
        try:
            optmize = self.getOptmizeText(optHost, optPort, optUser, optPwd, insDb['db_name'], sql)
            log.info('[online_query] get optmize succed')
        except Exception as ex:
            log.warning("[online_query], get optmize exception:" + str(ex))

        log.info('[online_query] optmize:' + optmize)

        #执行查询
        rows = []
        conn = None
        cursor = None
        try:
            conn = pymysql.connect(
                host=optHost, 
                port=optPort, 
                user=optUser, 
                passwd=optPwd, 
                db=insDb['db_name'],
                charset = 'utf8',
                cursorclass = pymysql.cursors.SSDictCursor,
            )
            df = pandas.read_sql(sql,con=conn, chunksize=limitRows)
            for batchDf in df:
                get_rows = 0
                for index in batchDf.index:
                    if get_rows == limitRows:
                        break
                    get_rows = get_rows + 1
                    row = batchDf.loc[index]
                    row = collections.OrderedDict(row)
                    tmp_row = collections.OrderedDict()
                    for k, v in row.items():
                        if v == None: v = 'NULL'
                        k = k.replace('(', '').replace(')', '').replace('/', '')
                        try:
                            tmp_row[k] = unicode(v)
                        except:
                            tmp_row[k] = v
                        try:
                            tmp_json_data = {'data':tmp_row[k]}
                            demjson.encode(tmp_json_data)
                        except:
                            tmp_row[k] = u'[xsql 字段解析失败]'
                    rows.append(tmp_row)
                break
        except Exception as ex:
            try:
                conn.close()
            except:
                pass
            return {
                'cols' : self.makeCols(['error']), 
                'rows' : [
                    {'error' : str(ex) },
                ],
                'optmize' : optmize,
            }
        if len(rows) == 0:
            #没有数据，这时候尝试把字段取出来
            try:
                sql = 'explain ' + sql
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                row = rows[0]
                table = row['table']
                log.info("try to get table name by sql, get table is:" + table)
                log.info("try to show columns")
                sql = 'show columns from ' + table
                cursor.execute(sql)
                rows = cursor.fetchall()
                cols = []
                for row in rows:
                    cols.append(row['Field'])
                return {
                    'cols' : self.makeCols(cols),
                    'rows' : [],
                    'optmize' : optmize,
                }
            except Exception, ex:
                log.error("try to get table column exception:" + str(ex))
                return {
                    'cols' : [[]],
                    'rows' : [],
                    'optmize' : optmize,
                }
        try:
            conn.close()
        except:
            pass
        row = rows[0]
        cols = row.keys()

        return {
            'cols' : self.makeCols(cols),
            'rows' : rows,
            'optmize' : optmize,
        }

    def genSQLAdvisorConfContent(self, dbHost, dbPort, dbUser, dbPwd, dbName, sql):
        '''
        [sqladvisor]
        username=cmdb_user
        password=xxx
        host=127.0.0.1
        port=3306
        dbname=cmdb
        sqls=select * from idc, isp where idc.isp_id = isp.id and idc.idc_en_name = 'bjxg'
        '''
        content = """[sqladvisor]\nusername=%s\npassword=%s\nhost=%s\nport=%s\ndbname=%s\nsqls=%s""" % (
            dbUser, dbPwd, dbHost, dbPort, dbName, sql
        )
        return content

    def getOptmizeText(self, dbHost, dbPort, dbUser, dbPwd, dbName, sql):
        '''
        cmd = "docker exec -it sqladvisor sqladvisor -h %s -P %s -u %s -p '%s' -d %s -q %s;" % (
            dbHost, dbPort, dbUser, dbPwd, dbName, sql
        )
        '''
        stamp = int(time.time())
        confdir = os.getcwd() + '/sql_advisor_conf/'
        filename = "%s_%s_%s_%s_%s.conf" % (
            dbHost, dbPort, dbUser, dbName, stamp)
        path = confdir + filename
        f = open(path, 'w')
        content = self.genSQLAdvisorConfContent(dbHost, dbPort, dbUser, dbPwd, dbName, sql)
        f.write(content)    
        f.close()
        shFilename = "%s_%s_%s_%s_%s.sh" % (
            dbHost, dbPort, dbUser, dbName, stamp)
        shPath = confdir + shFilename
        f = open(shPath, 'w')
        cmd = "sqladvisor -f /sql_advisor_conf/%s -v 1 2>&1" % (filename)
        f.write(cmd)
        f.close()
        #execCmd = "docker exec -it sqladvisor sh /sql_advisor_conf/%s 2>&1" % shFilename
        execCmd = "docker exec -i sqladvisor sh /sql_advisor_conf/%s 2>&1" % shFilename
        status, output = util.execmd(execCmd)
        log.info("[online query] after exec sqadvisor cmd, status:%s, output:%s" % (status, output))
        try:
            output = unicode(output)
        except:
            pass
        '''
        if '没有优化建议' in output:
            output = '没有优化建议'
            #pass
        if '第1步: 对SQL解析优化之后得到的SQL:select' in output and '第2步: SQLAdvisor结束!' in output:
            output = '没有优化建议'
        if 'No such container' in output:
            output = '没有优化建议'
        if 'Error response from daemon' in output:
            output = '没有优化建议'
        if 'No such file' in output:
            output = '没有优化建议'
        '''
        return output

    def makeCols(self, col_list):
        '''
        {field: 'id', title: 'id', sort: true, fixed: 'left'},
        '''
        cols = []
        for col in col_list:
            cols.append({
                'field' : col,
                'title' : col,
                'sort' : True,
                'fixed' : 'left',
                'edit' : 'text',
            })
        return [ cols ]

    def getSafeLimit(self, limit_rows):
        try:
            limit_rows = int(limit_rows)
        except:
            limit_rows = 100
        if limit_rows > MAX_LIMIT_ROWS:
            limit_rows = MAX_LIMIT_ROWS
        return limit_rows

class add_query_history(Guest):
    def handle(self):
        domain_name = self.session('domain_name')
        sql = self.request('sql')
        if sql == '': return self.resp()
        Orm(mysql_db).table('query_history').data([{
            'domain_name' : domain_name,
            'sql' : sql,
        }]).insert()
        return self.resp()

class is_can_export(Guest):
    def handle(self):
        if config('IS_CHECK_ALL_PERMI') != 'true': return self.resp()
        sql = self.request('sql')
        table = sql_parse.get_table_by_select_sql(sql)
        #add by liyuchen, 临时添加，之后需要删除
        if table == 'portfolio_stock_follow_127': return self.resp()
        if 'spider_column' in table: return self.resp()
        if 'portfolio_stock_108' in table: return self.resp()
        if 'stock_follower' in table: return self.resp()
        log.info("get table by select sql, table:" + str(table))
        file_list = [ filename for filename in os.listdir('./export_rules/')]
        json_file_list = []
        for file in file_list:
            if '.json' in file:
                json_file_list.append(file.replace('.json', ''))
        allow_list = []
        alert_list = []
        for json_file in json_file_list:
            tmp_list = json_file.split('_')
            db_name = tmp_list[0]
            tmp_list.pop(0)
            table_name = ''
            if len(tmp_list) > 1:
                table_name = '_'.join(tmp_list)
            else:
                table_name = tmp_list[0]
            #allow_table_name = db_name + '.' + table_name
            allow_table_name = table_name
            allow_list.append(allow_table_name)
            alert_list.append(db_name + '.' + table_name)
        log.info('allow export table list:' + str(allow_list))
        if table not in allow_list: table = None
        if table == None:
            return self.resp(errno=1, errmsg = u'只有表 ' + ', '.join(alert_list)  + '可以导出')
        else:
            return self.resp()