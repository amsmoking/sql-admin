#!/bin/bash

#cron:  */10 * * * * /bin/bash /usr/local/bin/slowquery_analysis.sh > /dev/null 2>&1
#apt-get install percona-toolkit -y

#需要配置的地方:
pt_query_digest={{pt_query_digest}}
mysql_server_id={{mysql_server_id}}

#改成你的运维管理机MySQL地址（用户权限最好是管理员）
slowquery_db_host="127.0.0.1"
slowquery_db_port="3306"
slowquery_db_user="xxxx"
slowquery_db_password="xxxx"
slowquery_db_database="slowquery"

#改成你的生产MySQL主库地址（用户权限最好是管理员）
mysql_client="mysql"
mysql_host="127.0.0.1"
mysql_port="3306"
mysql_user="falcon"
mysql_password="xxxx"

#改成你的生产MySQL主库慢查询目录和慢查询执行时间（单位秒）
slowquery_dir="/data/mysqldb"
slowquery_long_time=2
slowquery_file=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password  -e "show variables like 'slow_query_log_file'"|grep log|awk '{print $2}'`

#collect mysql slowquery log into slowquery database
$pt_query_digest --user=$slowquery_db_user --password=$slowquery_db_password --port=$slowquery_db_port --review h=$slowquery_db_host,D=$slowquery_db_database,t=mysql_slow_query_review  --history h=$slowquery_db_host,D=$slowquery_db_database,t=mysql_slow_query_review_history  --no-report --limit=100% --filter=" \$event->{add_column} = length(\$event->{arg}) and \$event->{serverid}=$mysql_server_id " $slowquery_file > /tmp/slowquery_analysis.log

##### set a new slow query log ###########
tmp_log=`$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "select concat('$slowquery_dir','slowquery_',date_format(now(),'%Y%m%d%H'),'.log');"|grep log|sed -n -e '2p'`

#config mysql slowquery
$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "set global slow_query_log=1;set global long_query_time=$slowquery_long_time;"
$mysql_client -h$mysql_host -P$mysql_port -u$mysql_user -p$mysql_password -e "set global slow_query_log_file = '$tmp_log'; "

#delete log before 7 days
cd $slowquery_dir
/usr/bin/find ./ -name 'slowquery_*' -mtime +7|xargs rm -f ;

####END####