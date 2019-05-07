#!/bin/sh
kill -9 $(ps -ef|grep sql-admin-ui|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
find ./ -name "*.pyc" | xargs rm -rf
#启动sql-advisor
rm -f ./sql_advisor_conf/*
docker rm -f sqladvisor
docker run -d --name=sqladvisor -v $(pwd)/sql_advisor_conf:/sql_advisor_conf --net host ppabc/sqladvisor
rm -f ./settings.ini
ln -s ./settings.ini.prod ./settings.ini
nohup python sql-admin-ui.py >> /var/log/sql-admin/ui_std.log 2>&1 &