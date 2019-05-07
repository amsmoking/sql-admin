import zmq  

context = zmq.Context()  
print "Connecting to server..."  
socket = context.socket(zmq.REQ)  
socket.connect ("tcp://localhost:9039")
print 'connected' 
socket.send ("hahaahah")
resp = socket.recv()
print resp