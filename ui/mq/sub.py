#coding=utf-8

import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://127.0.0.1:9039")
print 'connected'
socket.setsockopt(zmq.SUBSCRIBE,'')

while 1:
    msg = socket.recv()
    print 'recv: ', msg