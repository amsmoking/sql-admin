#!/bin/sh
rm -rf ./*.pyc
rm -f ./settings.ini
ln -s ./settings.ini.dev ./settings.ini
kill -9 $(ps -ef|grep sql-admin-puller|gawk '$0 !~/grep/ {print $2}' |tr -s '\n' ' ')
nohup python sql-admin-puller.py > /dev/null 2>&1 &