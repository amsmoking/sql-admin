#!/bin/sh
docker rm -f c_slow_query
docker run -itd --name c_slow_query -p 8081:80 --privileged xq_slow_query:latest /entrypoint.sh