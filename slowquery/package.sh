#!/bin/sh
docker commit -m 'c_slow_query' c_slow_query  xq_slow_query:latest
docker save -o xq_slow_query.tar.gz xq_slow_query:latest
rsync ./xq_slow_query.tar.gz 127.0.0.1::share/ --progress