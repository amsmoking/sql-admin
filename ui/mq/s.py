
import zmq

context = zmq.Context()  
socket = context.socket(zmq.REP)  
socket.bind("tcp://127.0.0.1:9039")  

while 1:
    message = socket.recv()  
    socket.send('has recieve')
    print "message from client:", message