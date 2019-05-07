#!/bin/sh
rsync 10.10.25.7::share/xq_slow_query.tar.gz ./ --progress
docker load < ./xq_slow_query.tar.gz