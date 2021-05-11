# -*- coding: utf-8 -*-
import sys
import socket
from select import select
import json, time, random
from punchobject import PunchObject
from appPublic.background import Background

class NatHole_Env(object):
	def __init__(self, server_ip, server_port):
		self.server_ip = socket.gethostbyname(server_ip)
		self.server_port = server_port

	def server_addr(self):
		return (self.server_ip, self.server_port)


class Endpoint(object):
	track_dict = {}
	session_name = []
	def __init__(self, env, session_name):
		self.env = env
		self.session_name=session_name
		self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.s.setblocking(0)
		self.s.settimeout(5)
		self.rand = random.SystemRandom()
		prt = self.rand.randint(20000,20005)
		self.s.bind(('0.0.0.0', prt))
		print("bound to port ", prt)
		self.p2plist = {}
		self.heartbeat()

	def heartbeat(self):
		self.heartbeat = True
		self.hb_time = 5
		def hb():
			while self.heartbeat:
				self.send_request(0)
				time.sleep(self.hb_time)

		b = Background(hb)
		b.start()

	def send(self, s, addr):
		b = s
		if isinstance(s,bytes):
			b = s
		elif isinstance(s,str):
			b = s.encode('utf-8')
		else:
			b = json.dumps(s)
		self.s.sendto(b,addr)

	def recv(self, recv_len=1024):
		data, addr = self.s.recvfrom(recv_len)
		data = data.decode('utf-8')
		return data, addr

	def send_request(self, offset):
		self.send("%s,%d" % (self.session_name, offset) , self.env.server_addr())
		data,addr=self.recv()
		self.dat = PunchObject(data)
		if self.dat.JSON:
			self.track_dict = json.loads(data[1:])
		
	def connect_endpoint(self, remote_name):
		t = 0
		while t < 999999:
			if self.track_dict.get(remote_name):
				break
			time.sleep(1)
			t += 1
			if t > 30:
				raise Exception(f'{remote_name} not registed')

		"""connect to another endpoint"""
		acc = 0.5 #TODO: implement sleep "growth"
		print(self.track_dict)
		connected = False
		synned = False
		remote_offset = None
		my_pub_offset = None
		syn_time=0
		ack_time=0
		self.dat = PunchObject("")
		for count in range(550):
			print("versuch %s" % count)
			r,w,x = select([self.s], [self.s], [], 0)
			if w:
				if count%4==0:
					if my_pub_offset!=None:
						self.send_request(my_pub_offset)
					else:
						self.send_request(0)

					r_addr = self.track_dict.get(remote_name)
					r_addr = r_addr[0], r_addr[1]
					print("addr update",r_addr)

				if connected:
					print("send msg to", r_addr)
					self.send(self.dat.compose('MSG', "%s offsetted msg: %s has public offset: %s" % (count, self.session_name, my_pub_offset)), r_addr)

				if not self.dat.SYN and not self.dat.ACK:
					msg = self.dat.compose('SYN', "%s %s,%s"%(count, self.session_name, 0) )#SYN mit offset
					self.send(msg, r_addr)
					syn_time = time.time()
	
				if self.dat.SYN:
					msg = self.dat.compose('ACK',"%s %s,%s" % \
								(count, self.session_name, 0) )
					self.send(msg, r_addr)
			if r:
				data,addr=self.recv()
				print("data: ", data)
				self.dat = PunchObject(data)
				if self.dat.MSG:
					num_nomsg = 0
					print(str(self.dat), ':', addr)
				elif self.dat.SYN:
					print("recvd SYN ", str(self.dat), ':', addr)
					synned = True
				elif self.dat.ACK:
					ack_time = time.time()-syn_time
					print("recvd ACK ", str(self.dat), ack_time, ':', addr)
					if synned:
						connected = True
						print("Connected.", remote_name, ':', addr)
						self.p2plist[remote_name] = addr
				elif self.dat.JSON:
					self.track_dict = json.loads(data[1:])
				else:
					num_nomsg += 1
			time.sleep(acc)
		
if __name__ == "__main__":
	if len(sys.argv) < 5:
		print("------------------\nUsage: python server_ip server_port hole-punch.py your-name target-name\n")
		exit(0)
	env = NatHole_Env(sys.argv[1], int(sys.argv[2]))
	name = sys.argv[3]
	connect_name = sys.argv[4]
	pt = Endpoint(env, name)
	pt.connect_endpoint(connect_name)
