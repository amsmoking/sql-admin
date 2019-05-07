drop database if exists xsql;
create database xsql;
use xsql;

DROP TABLE IF EXISTS `mysql_server`;   
CREATE TABLE `mysql_server` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `hostname` varchar(255) DEFAULT '' COMMENT '主机名',
    `ip` varchar(255) DEFAULT '' COMMENT 'ip',
    `isp` varchar(255) DEFAULT '' COMMENT '运营商',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `remark` varchar(255) DEFAULT '' COMMENT '备注',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT 'mysql服务器';

DROP TABLE IF EXISTS `mysql_instance`; 
CREATE TABLE `mysql_instance` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `server_id` int(11) DEFAULT 0 COMMENT '所属服务器',
    `port` int(6) DEFAULT 3306 COMMENT '使用的端口',
    `root_pwd` varchar(255) DEFAULT '' COMMENT '默认密码',
    `remote_user` varchar(255) DEFAULT '' COMMENT '远程执行用户',
    `remote_pwd` varchar(255) DEFAULT '' COMMENT '远程执行密码',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `puller_status` varchar(255) NOT NULL DEFAULT '' COMMENT 'poller检测的状态',
    `puller_errmsg` varchar(255) NOT NULL DEFAULT '' COMMENT 'poller检测的错误信息',
    `remark` varchar(255) DEFAULT '' COMMENT '备注',
    `slave_ip` varchar(255) NOT NULL DEFAULT '' COMMENT '从库IP',
    `slave_port` int(11) NOT NULL DEFAULT 0 COMMENT '从库端口',
    `allow_begin_time` varchar(255) NOT NULL DEFAULT '' COMMENT '允许自动执行的启始时间',
    `allow_end_time` varchar(255) NOT NULL DEFAULT '' COMMENT '允许自动执行的结束时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '实例';

DROP TABLE IF EXISTS `mysql_ins_db`;
CREATE TABLE `mysql_ins_db` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `ins_id` int(11) DEFAULT 0 COMMENT '所属实例',
    `db_name` varchar(255) DEFAULT '' COMMENT '数据库名称',
    `doc` TEXT COMMENT '表结构',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '实例下的数据库';

DROP TABLE IF EXISTS `sql_order`;
CREATE TABLE `sql_order` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `server_id` int(11) DEFAULT 0 COMMENT 'mysql服务器id',
    `ins_id` int(11) DEFAULT 0 COMMENT 'mysql实例id',
    `ins_db_id` int(11) DEFAULT 0 COMMENT '数据库id',
    `sql` LONGTEXT COMMENT 'sql语句',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `sel_ip` varchar(255) DEFAULT '' COMMENT '选的ip内容',
    `sel_port` int(6) DEFAULT 0 COMMENT '选的端口',
    `sel_db_name` varchar(255) DEFAULT '' COMMENT '选的数据库名',
	`reason` VARCHAR(255) DEFAULT '' COMMENT '备注',
	`req_user` VARCHAR(255) DEFAULT '' COMMENT '申请人',
    `order_status` int(3) DEFAULT 0 COMMENT '工单状态，0未审批，1审批，操作成功，2审批，操作失败，3取消操作，4异步执行中',
    `latest_exec_result` TEXT COMMENT '最近执行结果',
    `combi_info` LONGTEXT COMMENT '一些inception的信息',
    `issue_key`  VARCHAR(255) DEFAULT '' COMMENT '创建的jira issue key',
    `run_result_set` LONGTEXT COMMENT '返回的执行结果信息,用于回滚',
    `roll_back_times` int(11) NOT NULL DEFAULT 0 COMMENT '回滚的次数，用于判断不允许二次回滚',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT 'sql审核';

DROP TABLE IF EXISTS `user_info`;
CREATE TABLE `user_info` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `domain_name` varchar(255) DEFAULT '' COMMENT '域账号',
    `mail` varchar(255) DEFAULT '' COMMENT '邮箱',
    `mobile` varchar(255) DEFAULT '' COMMENT '手机号',
    `department` varchar(255) DEFAULT '' COMMENT '部门',
    `employ_no` varchar(255) DEFAULT '' COMMENT '员工号',
    `role` varchar(255) DEFAULT '' COMMENT '角色',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '用户';

DROP TABLE IF EXISTS `sql_task`;
CREATE TABLE `sql_task` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `order_id` varchar(255) DEFAULT '' COMMENT '工单号',
    `exec_status` int(5)  DEFAULT 0 COMMENT '执行状态,0未执行,1执行中,2执行完',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '用户';

DROP TABLE IF EXISTS `sql_task`;
CREATE TABLE `sql_task` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `order_id` varchar(255) DEFAULT '' COMMENT '工单号',
    `exec_status` int(5)  DEFAULT 0 COMMENT '执行状态,0未执行,1执行中,2执行完',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `jira_user` varchar(255) DEFAULT '' COMMENT '异步任务执行时调用jira接口的用户名',
    `jira_pwd` varchar(255) DEFAULT '' COMMENT '异步任务执行时调用jira接口的密码',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '用户';

DROP TABLE IF EXISTS `department`;
CREATE TABLE `department` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `zh_name` varchar(255) DEFAULT '' COMMENT '部门名中文',
    `en_name` varchar(255) DEFAULT '' COMMENT '部门名英文',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '部门';

DROP TABLE IF EXISTS `dept_server`;
CREATE TABLE `dept_server` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `dept_id` int(11) NOT NULL DEFAULT 0 COMMENT '部门id',
    `server_id` int(11) NOT NULL DEFAULT 0 COMMENT 'mysql服务器id',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT '部门与mysql权限表';

DROP TABLE IF EXISTS `archive_task`;
CREATE TABLE `archive_task` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `req_user` varchar(255) not NULL DEFAULT '' COMMENT '申请人',
    `src_host` varchar(255) not NULL DEFAULT '' COMMENT '源地址',
    `src_port` int(11) unsigned not NULL DEFAULT 3306 COMMENT '源端口',
    `src_user` varchar(255) not NULL DEFAULT '' COMMENT '源用户名',
    `src_pwd` varchar(255) not NULL DEFAULT '' COMMENT '源密码',
    `src_db` varchar(255) not NULL DEFAULT '' COMMENT '源库名',
    `to_archive_tables` TEXT COMMENT '源表名',
    `dst_host` varchar(255) not NULL DEFAULT '' COMMENT '目的地址',
    `dst_port` int(11) unsigned not NULL DEFAULT 3306 COMMENT '目的端口',
    `dst_user` varchar(255) not NULL DEFAULT '' COMMENT '目的用户',
    `dst_pwd` varchar(255) not NULL DEFAULT '' COMMENT '目的密码',
    `dst_db` varchar(255) not NULL DEFAULT '' COMMENT '目的库名',
    `where` varchar(255) not NULL DEFAULT '' COMMENT 'where条件',
    `is_del_src_data` int(3) not NULL DEFAULT 0 COMMENT '是否删除源归档数据,1删除，0不删除',
    `is_backup` int(3) not NULL DEFAULT 0 COMMENT '是否归档前备份,1备份，0不备份',
    `is_exec_once` int(3) not NULL DEFAULT 0 COMMENT '是否只执行一次，0否，1是',
    `dst_if_no_create` int(3) NOT NULL DEFAULT 0 COMMENT '目的MySQL中没有同名表时自动创建, 1,自动创建，0，不创建',
    `charset` varchar(255) not NULL DEFAULT 'utf8' COMMENT '字符集',
    `cron` varchar(255) not NULL DEFAULT '' COMMENT '时间规则',
    `remark` varchar(255) not NULL DEFAULT '' COMMENT '备注',
    `status` int(3) not NULL DEFAULT 1 COMMENT '状态, 0禁用，1启用',
    `latest_exec_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最近执行时间',
    `dst_table` varchar(255) not NULL DEFAULT '' COMMENT '目的表名,保留字段',
    `dst_table_type` int(3) not NULL DEFAULT 0 COMMENT '目的表类型',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '归档任务表';

DROP TABLE IF EXISTS `archive_log`;
CREATE TABLE `archive_log` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `task_id` int(11) unsigned NOT NULL DEFAULT 0 COMMENT '任务ID',
    `start_time` DATETIME not NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始执行时间',
    `end_time` DATETIME not NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结束执行时间',
    `bak_file` varchar(255) not NULL DEFAULT '' COMMENT '备份文件路径',
    `status` int(3) not NULL DEFAULT 0 COMMENT '执行结果:0成功，1失败',
    `output` TEXT COMMENT '执行输出',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '归档日志表';

DROP TABLE IF EXISTS `archive_log_bak`;
CREATE TABLE `archive_log_bak` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `task_id` int(11) unsigned NOT NULL DEFAULT 0 COMMENT '任务ID',
    `start_time` DATETIME not NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始执行时间',
    `end_time` DATETIME not NULL DEFAULT CURRENT_TIMESTAMP COMMENT '结束执行时间',
    `bak_file` varchar(255) not NULL DEFAULT '' COMMENT '备份文件路径',
    `status` int(3) not NULL DEFAULT 0 COMMENT '执行结果:0成功，1失败',
    `output` TEXT COMMENT '执行输出',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '归档日志备份表';

DROP TABLE IF EXISTS `query_history`;
CREATE TABLE `query_history` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `domain_name` varchar(255) NOT NULL DEFAULT '' COMMENT '域账号',
    `query_time` DATETIME not NULL DEFAULT CURRENT_TIMESTAMP COMMENT '查询时间',
    `sql` TEXT COMMENT '查询语句a',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '查询历史表';

DROP TABLE IF EXISTS `auto_verify`;
CREATE TABLE `auto_verify` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `begin_time` varchar(255) NOT NULL DEFAULT '' COMMENT '起始时间',
    `end_time` varchar(255) NOT NULL DEFAULT '' COMMENT '结束时间',
    `enable` int(3) unsigned NOT NULL DEFAULT 0 COMMENT '状态, 0禁用,1启用',
    `is_send_mail` int(3) unsigned NOT NULL DEFAULT 0 COMMENT '是否发送邮件,0不发，1发',
    `tos` varchar(255) NOT NULL DEFAULT '' COMMENT '接收邮件的邮箱地址',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '自动审核表';

DROP TABLE IF EXISTS `grant_apply`;
CREATE TABLE `grant_apply` (
    `id` int(11) unsigned NOT NULL AUTO_INCREMENT COMMENT 'id',
    `req_user` varchar(255) NOT NULL DEFAULT '' COMMENT '申请人',
    `reason` varchar(255) NOT NULL DEFAULT '' COMMENT '申请原因',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
    `server_id` int(11) NOT NULL DEFAULT 0 COMMENT '服务器id',
    `ins_id` int(11) NOT NULL DEFAULT 0 COMMENT '实例id',
    `ins_db_id` int(11) NOT NULL DEFAULT 0 COMMENT 'db id',
    `privilege` int(3) NOT NULL DEFAULT 0 COMMENT '权限类型',
    `priv_list` TEXT COMMENT '权限列表',
    `node_type` int(3) NOT NULL DEFAULT 0 COMMENT '节点类型',
    `roll_service_name` varchar(255) NOT NULL DEFAULT '' COMMENT '对应的rolling服务名',
    `ips` varchar(255) NOT NULL DEFAULT '' COMMENT '授权的IP',
    `status` int(3) NOT NULL DEFAULT 0 COMMENT '状态，0未授权，1授权成功, 2授权失败',
    `username` varchar(255) NOT NULL DEFAULT '' COMMENT '用户名',
    `password` varchar(255) NOT NULL DEFAULT '' COMMENT '密码',
    `pass_type` int(3) NOT NULL DEFAULT 1 COMMENT '账号类型：1，系统生成, 2自定义账号、密码',
    `spec_user` varchar(255) NOT NULL DEFAULT '' COMMENT '自定义账号',
    `spec_pass` varchar(255) NOT NULL DEFAULT '' COMMENT '自定义密码',
    PRIMARY KEY  (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT '授权申请表';