#coding=utf-8

from agileutil.db import DB
from decouple import config
import log
import demjson

STATUS_OK = 0
STATUS_FAILED = 1 

class MysqlBase(object):
    
    def __init__(self):
        self.db = None
        self.errmsg = ''

    def detect(self):
        pass

class Column(MysqlBase):

    def __init__(self):
        MysqlBase.__init__(self)
        self.name = ''

class Table(MysqlBase):
    
    def __init__(self):
        MysqlBase.__init__(self)
        self.name = ''
        self.columns = []
        self.showCreateTable = ''

    def detect(self):
        sql = "show create table %s" % self.name
        rows = self.db.query(sql)
        if rows == None or len(rows) == 0: return
        row = rows[0]
        self.showCreateTable = row['Create Table']
        sql = "show columns from %s" % self.name
        log.info(sql)
        rows = self.db.query(sql)
        if rows == None or len(rows) == 0: return
        column_namne_list = [row['Field'] for row in rows]
        self.columns = column_namne_list

class Database(MysqlBase):

    def __init__(self):
        MysqlBase.__init__(self)
        self.name = ''
        self.tables = []

    def detect(self):
        sql = "use `%s`;" % self.name
        log.info(sql)
        self.db.update(sql)
        sql = "show tables"
        rows = self.db.query(sql)
        if rows == None or len(rows) == 0: return
        table_name_list = []
        for row in rows:
            try:
                values = row.values()
                table_name = values[0]
                table_name_list.append(table_name)
            except:
                pass
        for table_name in table_name_list:
            table = Table()
            table.name = table_name
            table.db = self.db
            if config('IS_DETECT_COLUMN') == 'true': table.detect()
            self.tables.append(table)

    def document(self):
        dic = {}
        for table in self.tables:
            dic[table.name] = table.showCreateTable 
        return demjson.encode(dic)

class Instance(MysqlBase):
    
    def __init__(self):
        MysqlBase.__init__(self)
        self.status = STATUS_FAILED
        self.ip = ''
        self.port = 3306
        self.user = ''
        self.pwd = ''
        self.databases = []
        self.pullerStatus = 'failed'
        self.pullerErrmsg = ''

    def getDatabaseByName(self, name):
        '''
        根据数据库名称获取Database对象
        '''
        for db in self.databases:
            if db.name == name:
                return db
        return None

    def detect(self):
        try:
            self.db = DB(self.ip, int(self.port), self.user, self.pwd, '', ispersist=True, connect_timeout=config('CONNECT_TIMEOUT', cast=int))
            self.db.connect()
            #self.showSlaveStatus()
            self.loadDatabaseInfo()
            self.db.close()
            self.status = STATUS_OK
            self.pullerStatus = 'ok'
            self.pullerErrmsg = ''
            return True
        except Exception, ex:
            self.pullerStatus = 'failed'
            self.pullerErrmsg = str(ex)
            log.error("mysql instance detect exception:%s" % str(ex))
            return False

    def isSlave(self):
        pass
    
    '''
    def showSlaveStatus(self):
        sql = 'show slave status'
        rows = self.db.query(sql)
        import demjson
        log.info("show slave status \g")
        print 'slave status', rows
        assert 0
    '''

    def loadDatabaseInfo(self):
        sql = 'show databases'
        rows = self.db.query(sql)
        log.info(sql)
        if rows == None or len(rows) == 0: return
        db_name_list = [row['Database'] for row in rows]
        for db_name in db_name_list:
            database = Database()
            database.name = db_name
            database.db = self.db
            if config('IS_DETECT_TABLE') == 'true': database.detect()
            self.databases.append(database)

    def dump(self):
        dic = {}
        for database in self.databases:
            dic[database.name] = {} 
            for table in database.tables:
                dic[database.name][table.name] = table.showCreateTable
        return demjson.encode(dic)

    def document(self):
        return self.dump()

class MysqlServer(MysqlBase):

    def __init__(self):
        self.ip = ''
        self.hostname = ''
        self.instances = []