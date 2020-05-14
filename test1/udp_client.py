import socket
from threading import Thread
from time import sleep
 
UDPSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
 
data = 'hello'
#先連線到公開的伺服器
addr = ("210.74.14.107", 5678)
 
#接收到封包之後傳給另一台躲在NAT後的主機
def threaded_function(arg):
    for i in range(100):
        print( 'Send ' , i ,'to ', arg)
        UDPSock.sendto(str(i).encode('utf-8'), (arg.split(':')[0], int(arg.split(':')[1])))
        sleep(1)
 
#先丟給SERVER封包，讓伺服器取得IP資訊
UDPSock.sendto(data.encode('utf-8'),addr)
#接收伺服器回傳的另一台主機IP:PORT
dest,adr = UDPSock.recvfrom(1024)
print( 'send ping to ' , dest)
#進行打洞
dest = desc.decode('utf-8')
UDPSock.sendto(b'ping', (dest.split(':')[0], int(dest.split(':')[1])))
thread = Thread(target = threaded_function, args = (dest, ))
thread.start()

#持續接收封包
while True:
    data,adr = UDPSock.recvfrom(1024)
    print( 'Recv' , data , 'from' ,adr)
    
