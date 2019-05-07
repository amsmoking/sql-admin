#coding=utf-8

import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.PUB)  
socket.bind("tcp://127.0.0.1:9039")

num = 0
while True:
    time.sleep(1)
    socket.send(str(num))
    print 'send: ', num
    num = num + 1
