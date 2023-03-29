import socket 
from time import sleep
sock = socket.socket()
 
host = "192.168.1.116" #ESP32 IP in local network
port = 9001             #ESP32 Server Port    
print("connect",host,port) 
sock.connect((host, port))
sleep(3)
message = 'READ_PWM,1#'.encode()
sock.send(message)
sleep(0.2)
sock.settimeout(1)
f1 = sock.recv(1024).decode()
#d1 = sock.recv(6).decode().replace("\r\n","")
print(f1)
 
sock.close()