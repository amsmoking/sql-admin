#coding=utf-8

import sys
sys.path.append("../")
from common import *
from auth.ldap_auth import LDAPApi
from decouple import config
from model.mysql_server_model import MysqlServerModel
from model.mysql_instance_model import MysqlInstanceModel
from model.mysql_ins_db_model import MysqlInsDbModel
from model.sql_task_model import SqlTaskModel
from model.order import OrderModel
from model.order import ORDER_STATUS_AGREE_FAILED
from model.order import ORDER_STATUS_AGREE_SUCCED
from model.order import ORDER_STATUS_ASYNC_EXEC
from model.order import ORDER_STATUS_CANCEL
from model.order import ORDER_STATUS_NO_COMMIT
from model.order import ORDER_STATUS_NO_VIEW
from model.query_history_model import QueryHistoryModel
from model.archive_task import ArchiveTaskModel
from model.grant import GrantModel
import demjson
import time
import agileutil.date as dt
from agileutil.db import DB
from crontab import CronTab
from decouple import config

class api(NoAuth):

    def auth(self):
        token = self.request('token')
        if token != config('PULLER_TOKEN'):
            return False
        else:
            return True

    def handle(self):
        if not self.auth():
            return self.resp(errno=1, errmsg="invalid request")
        else:
            return self.deal()

    def deal(self):
        return ''

class get_mysql_servers(api):
    def deal(self):
        rows = MysqlServerModel().rows()
        return self.resp(data=rows)

class get_ins_by_server_id(api):
    def deal(self):
        server_id = self.request('server_id')
        self.safeId(server_id)
        mysqlServerModel = MysqlServerModel()
        mysqlServerModel.id = server_id
        instances = mysqlServerModel.loadInstances()
        return self.resp(data=instances)

class get_dbs_by_ins_id(api):
    def deal(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        dbs = MysqlInstanceModel().loadDbsByInsId(ins_id)
        return self.resp(data=dbs)

class del_dbs_by_ins_id(api):
    def deal(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        to_del_dbs = self.request('to_del_dbs')
        to_del_db_list = to_del_dbs.split(',')
        MysqlInstanceModel().delDbsByInsId(ins_id, to_del_db_list)
        return self.resp()

class add_db_by_ins_id(api):
    def deal(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        db_name = self.request('db_name')
        doc = self.request('doc')

        insDbModel = MysqlInsDbModel()

        if insDbModel.isExists(ins_id, db_name):
            return self.resp(errno=1, errmsg = 'has exist')

        insDbModel.insId = ins_id
        insDbModel.dbName = db_name
        insDbModel.doc = doc
        if insDbModel.save(): return self.resp()
        else: return self.resp(errno=1, errmsg='add db failed')

class update_puller_status(api):
    def deal(self):
        ins_id = self.request('ins_id')
        self.safeId(ins_id)
        puller_status = self.request('puller_status')
        puller_errmsg = self.request('puller_errmsg')
        instanceModel = MysqlInstanceModel()
        instanceModel.id = ins_id
        instanceModel.puller_status = puller_status
        instanceModel.puller_errmsg = puller_errmsg
        instanceModel.updatePullerStatus()
        return self.resp()

class reset_async(NoAuth):
    def handle(self):
        order_id = self.request('order_id')
        self.safeId(order_id)
        SqlTaskModel().resetAsync(order_id)
        return order_id

class reset_succed(NoAuth):
    def handle(self):
        order_id = self.request('order_id')
        self.safeId(order_id)
        is_async = self.request('is_async')
        SqlTaskModel().resetSucced(order_id, is_async)
        return order_id

class sql_online_cal_by_db(NoAuth):
    def handle(self):
        #获取所有数据库名
        insList = MysqlInstanceModel().rows()
        insIdList = [ ins['id'] for ins in insList ]
        insDbList = MysqlInsDbModel().getInsDbByInsIdList(insIdList)
        dbNameList = list( set(  [ insDb['db_name'] for insDb in insDbList ] ) )
        ignoreDbNameList = config('FILTER_DB_NAME_LIST').split(',')
        for ignDbName in ignoreDbNameList:
            try:
                dbNameList.remove(ignDbName)
            except:
                pass
        #获取所有上线了的工单
        dbCntMap = {}
        for dbName in dbNameList:
            dbCntMap[dbName] = 0
        orderList = OrderModel().rows()
        
        total = 0
        for order in orderList:
            selDbName = order['sel_db_name']
            if selDbName in dbNameList:
                    dbCntMap[selDbName] = dbCntMap[selDbName] + 1
            else:
                print selDbName + ' not in db name list'
                pass
            order_status = order['order_status']
            if order_status == ORDER_STATUS_AGREE_FAILED or order_status == ORDER_STATUS_AGREE_SUCCED:
                total = total + 1
        data = []
        for dbName, cnt in dbCntMap.items():
            data.append({
                'label' : dbName + "：" + str(cnt),
                'data' : cnt
            })
        ret = {}
        ret['data'] = data
        ret['total'] = total
        return demjson.encode(ret)

class online_query_cal(NoAuth):
    def handle(self):
        latestDays = config('ONLINE_QUERY_CAL_LATEST_DAYS', cast = int)
        if config('DEBUG') == 'true': latestDays = 80
        today = dt.today()
        stamp = dt.date_str_to_stamp(str(today) + ' 00:00:00')
        stampList = []
        for i in xrange(latestDays):
            stampList.append(stamp - i*24*3600)
        stampList.sort()
        dateList = [ dt.stamp_to_date_str(stamp)[0:10] for stamp in stampList ]
        startDate = dateList[0] + ' 00:00:00'
        endDate = dateList[-1] + ' 23:59:59'
        if config('DEBUG') == 'true': startDate = '2018-01-01 00:00:00'
        queryHis = QueryHistoryModel().getByDateRange(startDate, endDate)
        queryHisMap = {}
        for his in queryHis:
            queryTime = str(his['query_time'])[0:10]
            if queryHisMap.has_key(queryTime):
                queryHisMap[queryTime] = queryHisMap[queryTime] + 1
            else:
                queryHisMap[queryTime] = 1
        dateNumMap = {}
        ret = {}
        categories = []
        yAxis = {}
        yAxis['name'] = u'查询次数'
        yAxis['data'] = []
        for date in dateList:
            if queryHisMap.has_key(date):
                dateNumMap[date] = queryHisMap[date]
            else:
                dateNumMap[date] = 0
            stamp = dt.date_str_to_stamp(date + ' 23:59:59')
            categories.append(date)
            yAxis['data'].append(dateNumMap[date])

        ret['categories'] = categories
        ret['series'] = [ yAxis ]
        return demjson.encode(ret)

class order_status_cal(NoAuth):
    '''
    from model.order import ORDER_STATUS_AGREE_FAILED
    from model.order import ORDER_STATUS_AGREE_SUCCED
    from model.order import ORDER_STATUS_ASYNC_EXEC
    from model.order import ORDER_STATUS_CANCEL
    from model.order import ORDER_STATUS_NO_COMMIT
    from model.order import ORDER_STATUS_NO_VIEW
    '''
    def handle(self):
        ret = {}
        orderList = OrderModel().rows()
        #ret[u'总数'] = len(orderList)
        ret[u'上线失败'] = 0
        ret[u'上线成功'] = 0
        ret[u'执行中'] = 0
        ret[u'已取消'] = 0
        ret[u'保存，未提交'] = 0
        ret[u'已提交，待上线'] = 0
        for order in orderList:
            orderStatus = order['order_status']
            if orderStatus == ORDER_STATUS_AGREE_SUCCED:
                ret[u'上线成功'] = ret[u'上线成功'] + 1
            elif orderStatus == ORDER_STATUS_AGREE_FAILED:
                ret[u'上线失败'] = ret[u'上线失败'] + 1
            elif orderStatus == ORDER_STATUS_ASYNC_EXEC:
                ret[u'执行中'] = ret[u'执行中'] + 1
            elif orderStatus == ORDER_STATUS_CANCEL:
                ret[u'已取消'] = ret[u'已取消'] + 1
            elif orderStatus == ORDER_STATUS_NO_COMMIT:
                ret[u'保存，未提交'] = ret[u'保存，未提交'] + 1
            else:
                ret[u'已提交，待上线'] = ret[u'已提交，待上线'] + 1
        data = []
        for k, v in ret.items():
            data.append({
                'label' : k + "：" + str(v),
                'data' : v
            })
        ret = {}
        ret['data'] = data
        ret['total'] = len(orderList)
        return demjson.encode(ret)

class test_mysql_conn_state(NoAuth):
    def handle(self):
        db_host = self.req('db_host')
        db_port = self.req('db_port')
        db_user = self.req('db_user')
        db_pwd = self.req('db_pwd')
        if db_host == '': return self.resp(errno=1, errmsg = 'IP不能为空')
        if db_port == '' : return self.resp(errno=2, errmsg = '端口不能为空')
        try:
            db_port = int(db_port)
        except:
            return self.resp(errno=3, errmsg = '端口非法')
        if not (db_port >= 0 and db_port <= 65535):
            return self.resp(errno=4, errmsg = '端口范围0-65535')
        if db_user == '': return self.resp(errno=5, errmsg = '用户名不能为空')
        db = DB(db_host, db_port, db_user, db_pwd, '')
        try:
            db.connect()
        except Exception as ex:
            return self.resp(errno=6, errmsg = "测试连接失败:" + str(ex))
        try:
            db.close()
        except:
            pass
        return self.resp()

class load_src_dst_info(NoAuth):
    def handle(self):
        src_host = self.req('src_host')
        src_port = int(self.req('src_port'))
        src_user = self.req('src_user')
        src_pwd = self.req('src_pwd')
        dst_host = self.req('dst_host')
        dst_port = int(self.req('dst_port'))
        dst_user = self.req('dst_user')
        dst_pwd = self.req('dst_pwd')
        src_db = DB(src_host, src_port, src_user, src_pwd, '', ispersist = True)
        dst_db = DB(dst_host, dst_port, dst_user, dst_pwd, '', ispersist = True)
        src_info = self.loadDbInfo(src_db)
        dst_info = self.loadDbInfo(dst_db)
        ret = {
            'src_info' : src_info,
            'dst_info' : dst_info
        }
        return self.resp(data = ret)

    def loadDbInfo(self, db):
        sql = 'show databases'
        rows = db.query(sql)
        dbTableMap = {}
        if rows == None or len(rows) == 0: return dbTableMap
        dbList = []
        for row in rows:
            dbList.extend(row.values())
        dbList = list( set( dbList ) )
        ignoreDbList = [ item.strip() for item in config('FILTER_DB_NAME_LIST').split(',') ]
        for ignore in ignoreDbList:
            try:
                dbList.remove(ignore)
            except:
                pass
        
        for dbName in dbList:
            tables = self.loadTableInfo(db, dbName)
            dbTableMap[dbName] = tables
        
        return dbTableMap

    def loadTableInfo(self, db, dbName):
        sql = "use `%s`" % dbName
        db.update(sql)
        sql = "show tables"
        rows = db.query(sql)
        if rows == None or len(rows) == 0: return []
        tableList = []
        for row in rows:
            tableList.extend(row.values())
        return tableList

class add_archive_task(NoAuth):
    def handle(self):
        src_host = self.req('src_host')
        src_port = int(self.req('src_port'))
        src_user = self.req('src_user')
        src_pwd = self.req('src_pwd')
        
        dst_host = self.req('dst_host')
        dst_port = int(self.req('dst_port'))
        dst_user = self.req('dst_user')
        dst_pwd = self.req('dst_pwd')
        dst_if_no_create = self.req('dst_if_no_create')

        src_db = self.req('src_db')
        dst_db = self.req('dst_db')

        dst_table_type = int(self.req('dst_table_type'))
        dst_table = self.req('dst_table')

        to_archive_tables = self.req('to_archive_tables')
        to_archive_tables =  list( set( [ item.strip() for item in to_archive_tables.split(',') ] ) )

        is_exec_once = int(self.req('is_exec_once'))

        req_user = self.req('req_user')
        try:
            req_user = self.session('domain_name')
        except:
            pass

        if dst_table_type == ArchiveTaskModel.TABLE_TYPE_SELF_DEFINE:
            if dst_table == '':
                return self.resp(errno=1, errmsg = '目的表名不能为空')
            if len(to_archive_tables) > 1:
                return self.resp(errno=1, errmsg = '自定义目的表名时，只能选择一个需要归档的表')

        #结合前端UI的逻辑，这一步骤，只需要检查如下的信息即可，上面的变量在其他接口已经检查过
        #在调用此接口时，上面的变量已经被检查并认为合法
        where = self.req('where')
        is_del_src_data = int(self.req('is_del_src_data'))
        is_backup = int(self.req('is_backup'))
        charset = self.req('charset')
        cron = self.req('cron')
        remark = self.req('remark')

        #检查where条件语法是否正确
        err = self.isValidWhere(src_host, src_port, src_user, src_pwd, src_db, to_archive_tables, where)
        if err != None:
            return self.resp(errno=2, errmsg = err)

        #检查cron是否合法
        if not self.isValidCron(cron):
            return self.resp(errno=3, errmsg = 'cron格式错误')

        dataMap = {
            'req_user' : req_user,
            'src_host' : src_host,
            'src_port' : src_port,
            'src_user' : src_user,
            'src_pwd' : src_pwd,
            'src_db' : src_db,
            'dst_host' : dst_host,
            'dst_port' : dst_port,
            'dst_user' : dst_user,
            'dst_pwd' : dst_pwd,
            'dst_db' : dst_db,
            'to_archive_tables' : ','.join(to_archive_tables),
            'where' : where,
            'is_del_src_data' : is_del_src_data,
            'dst_if_no_create' : dst_if_no_create,
            'is_backup' : is_backup,
            'charset' : charset,
            'cron' : cron,
            'remark' : remark,
            'is_exec_once' : is_exec_once,

            'dst_table_type' : dst_table_type,
            'dst_table' : dst_table,
        }

        ArchiveTaskModel().addTask(dataMap)
        return self.resp()

    def isValidWhere(self, src_host, src_port, src_user, src_pwd, src_db, to_archive_tables, where):
        '''
        where条件合法，返回None,
        where条件错误，或字段不正确，返回错误信息
        '''
        if where != '':
            #为了避免输入了WHERE关键字，这里检查一下
            condition = ''
            if 'WHERE' in where.upper():
                condition = ' ' + where
            else:
                condition = ' WHERE ' + where
                 
            #需要遍历到每一个表，为了避免较多连接，这里保持连接
            src_db_ins = DB(src_host, src_port, src_user, src_pwd, src_db, ispersist = True)
            for table_name in to_archive_tables:
                sql = """select * from %s %s limit 1""" % (table_name, condition)
                try:
                    src_db_ins.query(sql)
                except Exception as ex:
                    ex = str(ex)
                    print ex
                    if 'Unknown column' in ex:
                        return '表' + table_name + '没有where条件中填写的字段'
                    elif 'You have an error in your SQL syntax' in ex:
                        return 'where条件语法错误'
                    else:
                        return ex
            try:
                src_db_ins.close()
            except:
                pass

        return None

    def isValidCron(self, string):
        try:
            user_cron = CronTab()
            job = user_cron.new(command = 'ls')
            job.setall(string)
        except Exception as ex:
            print(ex)
            return False
        return True

class get_mysql_priv_list(NoAuth):
    def handle(self):
        #1只读，2读写，3所有，4自定义
        #priv_type = self.req('priv_type')
        priv_type = self.request('priv_type')
        if priv_type == '1':
            return self.resp(data = GrantModel.getReadOnlyLowerPrivList())
        elif priv_type == '2':
            return self.resp(data = GrantModel.getReadWriteLowerPrivList())
        elif priv_type == '3':
            return self.resp(data = GrantModel.getAllLowerPrivList())
        else:
            return self.resp(data = [])

class get_rolling_container_map_list(NoAuth):
    def handle(self):
        return demjson.encode(GrantModel.getRollingContainerMapList())

class get_rolling_nodes_by_service(NoAuth):
    def handle(self):
        service_name = self.req('service_name')
        envstr = self.req('env')
        envList = envstr.split(',')
        try:
            envList.remove('')
        except:
            pass
        if len(envList) == 0:
            return self.resp(data = GrantModel.getAllRollNodesByServiceNameEnv(service_name))
        else:
            #返回指定环境的节点
            allNodes = []
            for env in envList:
                nodes = GrantModel.getRollNodesByServiceNameEnv(service_name, env)
                allNodes.extend(nodes)
            return self.resp(data = allNodes)

class get_rolling_nodes_str_by_service(NoAuth):
    def handle(self):
        allNodes = []
        service_name = self.req('service_name')
        envstr = self.req('env')
        envList = envstr.split(',')
        try:
            envList.remove('')
        except:
            pass
        if len(envList) == 0:
            allNodes = GrantModel.getAllRollNodesByServiceNameEnv(service_name)
        else:
            #返回指定环境的节点
            for env in envList:
                nodes = GrantModel.getRollNodesByServiceNameEnv(service_name, env)
                allNodes.extend(nodes)
        return self.resp(data = '\n'.join(allNodes))

class reverse_archive_task_status(NoAuth):
    def handle(self):
        task_id = self.request('task_id')
        self.safeId(task_id)
        try:
            ArchiveTaskModel().reverseStatus(task_id)
        except Exception as ex:
            return self.resp(errno=1, errmsg = str(ex))
        return self.resp()

class get_user_depart(NoAuth):
    def handle(self):
        domain_name = self.request('domain_name')
        if domain_name == '': return self.resp(errno=1, errmsg = 'domain_name is empty')
        ldapApi = LDAPApi(ldapServer=config('LDAP_SERVER'), ldapBind=config('LDAP_BIND'), ldapPass=config('LDAP_PASS'))
        depart_list , err = ldapApi.getUserDepartList(domain_name)
        print 'depart_list:'
        ret = []
        for dept in depart_list:
            print dept.decode('utf8')
            ret.append(dept.decode('utf8'))
        if err != None: return self.resp(errno=2, errmsg = str(err))
        return self.resp(data = ret)