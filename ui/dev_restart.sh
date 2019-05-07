#!/bin/sh
kill -9 $(ps -ef|grep sql-admin-ui|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
docker rm -f inception
docker rm -f sqladvisor
rm -f ./sql_advisor_conf/*
#启动sql-advisor
docker run -d --name=sqladvisor -v $(pwd)/sql_advisor_conf:/sql_advisor_conf --net host  ppabc/sqladvisor
#启动inception
docker run -itd -p 9012:9011 --name inception --privileged inception:latest /entrypoint.sh
#nohup python sql-admin-ui.py > /dev/null 2>&1 &
find ./ -name "*.pyc" | xargs rm -rf
rm -f ./settings.ini
ln -s ./settings.ini.dev ./settings.ini
python sql-admin-ui.py
#nohup python sql-admin-ui.py > /dev/null 2>&1 &