import socket

#建立 UDP Scoket
UDPSock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
#監聽 所有IP的 5678 端口 
listen_addr = ("", 5678)
UDPSock.bind(listen_addr)

#儲存IP用的 Array
ips = []

while True:
	#接收資料
	data, addr = UDPSock.recvfrom(1024)
	print(addr , 'is connected.')
	#將Client IP:Port 儲存到Array內
	data = data.decode('utf-8')
	ips.append(str(addr[0]) + ':' + str(addr[1]))
	#當第二個Client連上時，進行IP交換動作
	if(len(ips) == 2):
		dest = ''
		UDPSock.sendto(ips[0].encode('utf-8'),
				(ips[1].split(':')[0],int(ips[1].split(':')[1])))
		UDPSock.sendto(ips[1].encode('utf-8'),
				(ips[0].split(':')[0],int(ips[0].split(':')[1])))
		ips = []
