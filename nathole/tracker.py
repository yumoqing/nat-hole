# -*- coding: utf-8 -*-
import sys
import socket, json
from punchobject import PunchObject

class Tracker(object):
	track_dict = {}
	
	def __init__(self, port):
		self.track_dict['this'] = ['localhost', port, 0]
		self.p = PunchObject("")
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.bind(('0.0.0.0', self.track_dict['this'][1]))

	def send(self, s, addr):
		b = s
		if isinstance(s, str):
			b = s.encode('utf-8')
		self.s.sendto(b, addr)

	def recv(self, recv_len=1024):
		(data,addr) = self.s.recvfrom(recv_len)
		data = data.decode('utf-8')
		return data, addr

	def listen(self):
		while 1:
			(data,addr)= self.recv()
			data = data.split(',')
			session_name = data[0]
			offset = data[1]
			self.track_dict[session_name] = [addr[0], int(addr[1]), int(offset)]
			msg = self.p.compose('JSON', json.dumps(self.track_dict))
			self.send( msg, addr)
			print(self.track_dict)


port = 50000
if len(sys.argv) >= 2:
	port = int(sys.argv[1])
t = Tracker(port)
t.listen()
