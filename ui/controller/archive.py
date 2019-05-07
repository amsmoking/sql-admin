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

def jd(string, jd_length = 15):
    '''
    返回截断的字符串，原字符串
    '''
    length = len(string)
    if length <= jd_length:
        return string, string
    jd_str = string[0:jd_length]
    return jd_str + '...', string

class task(Admin):
    def handle(self):
        tasks = Orm(mysql_db).table('archive_task').get()
        for row in tasks:
            src_mysql = ''
            src_mysql = src_mysql + '<div>' + row['src_host'] + '</div>'
            src_mysql = src_mysql + '<div>' + str(row['src_port']) + '</div>'
            src_mysql = src_mysql + '<div>' + row['src_user'] + '</div>'
            src_mysql= src_mysql + '<div>' + row['src_db'] + '</div>'
            row['src_mysql_jd'] = src_mysql

            dst_mysql = ''
            dst_mysql = dst_mysql + '<div>' + row['dst_host'] + '</div>'
            dst_mysql = dst_mysql + '<div>' + str(row['dst_port']) + '</div>'
            dst_mysql = dst_mysql + '<div>' + row['dst_user'] + '</div>'
            dst_mysql= dst_mysql + '<div>' + row['dst_db'] + '</div>'
            row['dst_mysql_jd'] = dst_mysql

            other = ''
            other = other + '<div>归档前备份: '
            if row['is_backup'] == 0:
                other = other + '否' + '</div>'
            else:
                other = other + '是' + '</div>'
            
            other = other + '<div>表不存在时创建: '
            if row['dst_if_no_create'] == 0:
                other = other + '否'
            else:
                other = other + '是'
            
            other = other + '<div>删除归档数据: '
            if row['is_del_src_data'] == 0:
                other = other + '否'
            else:
                other = other + '是'

            if row['dst_table'] != '':
                other = other + '<div>' + '目的表名: ' + row['dst_table'] + '</div>'
            else:
                if row['dst_table_type'] == ArchiveTaskModel.TABLE_TYPE_SAME:
                    other = other + '<div>' + '目的表名: 与源表名一致' + '</div>'
                elif row['dst_table_type'] == ArchiveTaskModel.TABLE_TYPE_STAMP:
                    other = other + '<div>' + '目的表名: 源表名_ + 时间戳' + '</div>'
                elif row['dst_table_type'] == ArchiveTaskModel.TABLE_TYPE_Y:
                    other = other + '<div>' + '目的表名: 源表名_年' + '</div>'
                elif row['dst_table_type'] == ArchiveTaskModel.TABLE_TYPE_Y_M:
                    other = other + '<div>' + '目的表名: 源表名_年_月' + '</div>'
                elif row['dst_table_type'] == ArchiveTaskModel.TABLE_TYPE_Y_M_D:
                    other = other + '<div>' + '目的表名: 源表名_年_月_日' + '</div>'
                elif row['dst_table_type'] == ArchiveTaskModel.TABLE_TYPE_Y_M_D_H_M_S:
                    other = other + '<div>' + '目的表名: 源表名_年_月_日_时_分_秒' + '</div>'
                else:
                    pass

            if row['is_exec_once'] == 1:
                other = other + '<div>' + '一次性执行: 是' + '</div>'
            else:
                other = other + '<div>' + '一次性执行: 否' + '</div>'

            if row['status'] == 0:
                row['status_zh'] = '启用'
            else:
                row['status_zh'] = '禁用'

            to_archive_tables_str = ''
            to_archive_tables = row['to_archive_tables'].split(',')

            to_archive_tables.sort()

            for tb in to_archive_tables:
                to_archive_tables_str = to_archive_tables_str + '<div>' + tb + '</div>'

            row['to_archive_tables'] = to_archive_tables_str

            row['remark_jd'], _ = jd(row['remark'])
            row['other'] = other
            
        self.data['tasks'] = tasks
        self.data['page_title'] = '任务列表'
        return self.render().archive_task(data=self.data)
        '''
        tasks = Orm(mysql_db).table('archive_task').get()
        for row in tasks:
            row['src_mysql'] = ':'.join([ row['src_host'], str(row['src_port']), row['src_user'],'...', row['src_db'], row['src_table'] ])
            row['src_mysql_jd'], _ = jd(row['src_mysql'])
            row['dst_mysql'] = ':'.join([ row['dst_host'],str(row['dst_port']), row['dst_user'], '...', row['dst_db'], row['dst_table'] ])
            row['dst_mysql_jd'], _ = jd(row['dst_mysql'])
            row['remark_jd'], _ = jd(row['remark'], 4)
        self.data['tasks'] = tasks
        self.data['page_title'] = '任务列表'
        return self.render().archive_task(data=self.data)
        '''

class view(Admin):
    def handle(self):
        form = self.request('form')
        if form == 'add':
            self.data['page_title'] = '添加归档任务'
            self.data['task'] = {}
        if form == 'edit':
            task_id = self.request('task_id')
            task = Orm(mysql_db).table('archive_task').where('id', task_id).first()
            self.data['task'] = task
            self.data['page_title'] = '编辑归档任务'
        return self.render().archive_view(data = self.data)

'''
DROP TABLE IF EXISTS `archive_task`;
CREATE TABLE `archive_task` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `req_user` varchar(255) not NULL DEFAULT '' COMMENT '申请人',
    `src_host` varchar(255) not NULL DEFAULT '' COMMENT '源地址',
    `src_port` int(11) unsigned not NULL DEFAULT 3306 COMMENT '源端口',
    `src_user` varchar(255) not NULL DEFAULT '' COMMENT '源用户名',
    `src_pwd` varchar(255) not NULL DEFAULT '' COMMENT '源密码',
    `src_db` varchar(255) not NULL DEFAULT '' COMMENT '源库名',
    `src_table` varchar(255) not NULL DEFAULT '' COMMENT '源表名',
    `where_condition` varchar(255) not NULL DEFAULT '' COMMENT 'where条件',
    `dst_host` varchar(255) not NULL DEFAULT '' COMMENT '目的地址',
    `dst_port` int(11) unsigned not NULL DEFAULT 3306 COMMENT '目的端口',
    `dst_user` varchar(255) not NULL DEFAULT '' COMMENT '目的用户',
    `dst_pwd` varchar(255) not NULL DEFAULT '' COMMENT '目的密码',
    `dst_db` varchar(255) not NULL DEFAULT '' COMMENT '目的库名',
    `dst_table` varchar(255) not NULL DEFAULT '' COMMENT '目的表名',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `is_delete` int(3) not NULL DEFAULT 1 COMMENT '是否删除源归档数据,1删除，0不删除',
    `is_backup` int(3) not NULL DEFAULT 1 COMMENT '是否归档前备份,1备份，0不备份',
    `charset` varchar(255) not NULL DEFAULT 'utf8' COMMENT '字符集',
    `cron` varchar(255) not NULL DEFAULT '' COMMENT '时间规则'，
    `remark` varchar(255) not NULL DEFAULT '' COMMENT '备注',
    `status` int(3) not NULL DEFAULT 1 COMMENT '状态, 0禁用，1启用',
    `latest_exec_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最近执行时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '归档任务表';
'''

class commit(Admin):
    def handle(self):
        task_id = self.request('task_id')
        self.safeId(task_id)

        err = self.check()
        if err != None:
            return self.resp(errno=1, errmsg = err)

        req_user = self.session('domain_name')
        src_host = self.request('src_host')
        src_port = self.request('src_port')
        src_user = self.request('src_user')
        src_pwd = self.request('src_pwd')
        src_db = self.request('src_db')
        src_table = self.request('src_table')
        where_con = self.request('where_con')
        dst_host = self.request('dst_host')
        dst_port = self.request('dst_port')
        dst_user = self.request('dst_user')
        dst_pwd = self.request('dst_pwd')
        dst_db = self.request('dst_db')
        dst_table = self.request('dst_table')

        is_delete = self.request('is_delete')
        is_backup = self.request('is_backup')
        charset = self.request('charset')
        if charset == '': charset = 'utf8'
        cron = self.request('cron')
        remark = self.request('remark')

        if task_id == '':
            Orm(mysql_db).table('archive_task').data({
                'req_user' : req_user,
                'src_host' : src_host,
                'src_port' : src_port,
                'src_user' : src_user,
                'src_pwd' : src_pwd,
                'src_db' : src_db,
                'src_table' : src_table,
                'where_condition' : where_con,
                'dst_host' : dst_host,
                'dst_port' : dst_port,
                'dst_user' : dst_user,
                'dst_pwd' : dst_pwd,
                'dst_db' : dst_db,
                'dst_table' : dst_table,
                'is_delete' : is_delete,
                'is_backup' : is_backup,
                'charset' : charset,
                'remark' : remark,
                'cron' : cron,
            }).insert()
            notify.send_alarm('xsql', '[archive] add a task')
        else:
            print Orm(mysql_db).table('archive_task').data({
                #'req_user' : req_user,
                'src_host' : src_host,
                'src_port' : src_port,
                'src_user' : src_user,
                'src_pwd' : src_pwd,
                'src_db' : src_db,
                'src_table' : src_table,
                'where_condition' : where_con,
                'dst_host' : dst_host,
                'dst_port' : dst_port,
                'dst_user' : dst_user,
                'dst_pwd' : dst_pwd,
                'dst_db' : dst_db,
                'dst_table' : dst_table,
                'is_delete' : is_delete,
                'is_backup' : is_backup,
                'charset' : charset,
                'remark' : remark,
                'cron' : cron,
            }).where('id', task_id).update()
            notify.send_alarm('xsql', '[archive] edit a task')
        return self.resp()
        #return self.resp(errno=1, errmsg = 'test')

    def check(self):
        #检查端口范围
        src_port = int(self.request('src_port'))
        dst_port = int(self.request('dst_port'))
        if src_port >= 0 and src_port <= 65535 and dst_port >= 0 and dst_port <= 65535:
            pass
        else:
            return '端口范围0-65535'
        #检查两个Mysql是否能够用提交的账号连接
        src_host = self.request('src_host')
        src_user = self.request('src_user')
        src_pwd = self.request('src_pwd')
        src_db = self.request('src_db')
        src_db_ins = None
        try:
            src_db_ins = DB(src_host, src_port, src_user, src_pwd, src_db)
            src_db_ins.connect()
        except Exception as ex:
            return "源MySQL用此用户名密码连接失败，请确认用户名、密码、是否正确，库名是否存在"
        dst_host = self.request('dst_host')
        dst_user = self.request('dst_user')
        dst_pwd = self.request('dst_pwd')
        dst_db = self.request('dst_db')
        dst_db_ins = None
        try:
            dst_db_ins = DB(dst_host, dst_port, dst_user, dst_pwd, dst_db)
            dst_db_ins.connect()
        except Exception as ex:
            return "目的MySQL用此用户名密码连接失败，请确认用户名、密码、是否正确，库名是否存在"
        #检查表名是否存在
        src_table = self.request('src_table')
        dst_table = self.request('dst_table')
        try:
            sql = 'show tables'
            rows = src_db_ins.query(sql)
            if rows != None:
                tables = []
                for row in rows:
                    values = row.values()
                    for val in values:
                        tables.append(val)
                if src_table not in tables:
                    return '源MySQL表名' + src_table + '不存在'
            '''
            rows = dst_db_ins.query(sql)
            if rows != None:
                tables = []
                for row in rows:
                    values = row.values()
                    for val in values:
                        tables.append(val)
                if dst_table not in tables:
                    return '目的MySQL表名' + dst_table + '不存在'
            '''
        except Exception as ex:
            pass
        #检查where条件语法是否正确
        where_con = self.request('where_con')
        if where_con != '':
            try:
                sql = """select * from %s where %s limit 1""" % (src_table, where_con)
                print "sql:", sql
                rows = src_db_ins.query(sql)
            except Exception as ex:
                return 'WHERE条件语法错误：' + str(ex)
        #检查cron格式是否正确
        cron = self.request('cron')
        if not self.isValidCron(cron):
            return 'cron格式错误'
        try:
            src_db_ins.close()
            dst_db_ins.close()
        except:
            pass
        return None

    def isValidCron(self, string):
        try:
            user_cron = CronTab()
            job = user_cron.new(command = 'ls')
            job.setall(string)
        except Exception as ex:
            return False
        return True

class delete(Admin):
    def handle(self):
        task_id = self.request('task_id')
        self.safeId(task_id)
        Orm(mysql_db).table('archive_task').where('id', task_id).delete()
        return self.resp()

class reverse_status(Admin):
    def handle(self):
        task_id = self.request('task_id')
        self.safeId(task_id)
        task = Orm(mysql_db).table('archive_task').where('id', task_id).first()
        status = task['status']
        newstatus = None
        if status == 0: newstatus = 1
        else: newstatus = 0
        print 'src_status', status, 'new_status', newstatus
        Orm(mysql_db).table('archive_task').data({'status':newstatus}).where('id', task_id).update()
        return self.resp()

class log_index(Admin):
    def handle(self):
        task_id = self.request('task_id')
        self.safeId(task_id)
        logs = Orm(mysql_db).table('archive_log').where('task_id', int(task_id)).get()
        for log in logs: 
            log['output_jd'], _ = jd(log['output'])
            log['bak_file_jd'], _ = jd(log['bak_file'])
        self.data['logs'] = logs
        self.data['page_title'] = '归档日志'
        return self.render().log_index(data = self.data)

class delete_log(Admin):
    def handle(self):
        log_id = self.request('log_id')
        self.safeId(log_id)
        Orm(mysql_db).table('archive_log').where('id', int(log_id)).delete()
        return self.resp()

class start_now(Admin):
    def handle(self):
        task_id = int(self.request('task_id'))
        self.safeId(task_id)
        task = Orm(mysql_db).table('archive_task').where("id", task_id).first()
        if int(task['status']) == 0:
            #'状态, 0禁用，1启用',
            return self.resp(errno=1, errmsg = '任务已被禁用')
        self.send_msg(str(task_id))
        return self.resp()

    def send_msg(self, msg):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        log.info("ready to connect to mq")
        socket.connect (config('MQ_ADDR'))
        log.info("connected")
        socket.send(msg)
        response = socket.recv()
        log.info("recv response is:" + response)

class new_task(Admin):
    def handle(self):
        return self.render().new_task(data = self.data)