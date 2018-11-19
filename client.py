#Socket client example in python
 
import socket   #for sockets
import sys  #for exit
import json 
 
#create an INET, STREAMing socket
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
except socket.error:
    print 'Failed to create socket'
    sys.exit()

print 'Socket Created'
 
host = 'localhost';
port = 3500;
 
try:
    remote_ip = socket.gethostbyname( host )
 
except socket.gaierror:
    #could not resolve
    print 'Hostname could not be resolved. Exiting'
    sys.exit()
 
#Connect to remote server
s.connect((remote_ip , port))
 
print 'Socket Connected to ' + host + ' on ip ' + remote_ip
 
#Send some data to remote server
message = "GET / HTTP/1.1\r\n\r\n"
 



# data = m

data_string = json.dumps({"c": 0, "b": 0, "a": 0})


# data_string = json.dumps(data) #data serialized
# data_loaded = json.loads(data) #data loaded

try :
    #Set the whole string
    s.sendall(data_string)
except socket.error:
    #Send failed
    print 'Send failed'
    sys.exit()
 
print 'Message send successfully'
 
#Now receive data
while 1:
    reply = s.recv(4096)
 
print reply