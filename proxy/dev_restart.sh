#!/bin/sh
kill -9 $(ps -ef|grep sql-admin-proxy|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
nohup python sql-admin-proxy.py 9018 > /dev/null 2>&1 &
python sql-admin-proxy.py 9017