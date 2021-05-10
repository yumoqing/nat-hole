# -*- coding: utf-8 -*-
import sys
import socket
from select import select
import json, time, random
from punchobject import PunchObject

class NatHole_Env(object):
	def __init__(self, server_ip, server_port):
		self.server_port = server_port
		self.server_ip = server_ip

	def server_addr(self):
		return (self.server_ip, server_port)


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
		
	def send(self, s, addr):
		b = s
		if isinstance(s,bytes):
			b = s
		else if isinstance(s,str):
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
		for count in xrange(550):
			print("versuch %s" % count)
			r,w,x = select([self.s], [self.s], [], 0)
			if w:
				if count%4==0:
					if my_pub_offset!=None:
						self.send_request(my_pub_offset)
					else:
						self.send_request(0)
					r_addr = self.track_dict[remote_name]
					r_offset = r_addr[2]
					r_addr = r_addr[0], r_addr[1]
					print("addr update")

				if connected:
					print("send msg")
					self.send(self.dat.compose('MSG', "%s offsetted msg: %s has public offset: %s" % (count, self.session_name, my_pub_offset)), (r_addr[0], r_addr[1]+remote_offset))
					print(r_addr[1]+remote_offset)

				mx = (5 + r_offset + count*2)%65536
				mn =		 (r_offset)%65536-count-5

				if mn>mx:
					mn = mx+1
				if remote_offset==None:# and not connected:
					print("probing offset in range: ", mn+r_addr[1], mx+r_addr[1])
					for i in range(mn,mx):
						#if count<20#if my_pub_offset == None or remote_offset==None:
						if i!=my_pub_offset:
							if not self.dat.SYN and not self.dat.ACK or my_pub_offset != None:
								msg = self.dat.compose('SYN', "%s %s,%s"%(count, self.session_name, i) )#SYN mit offset
								self.send(msg, (r_addr[0], r_addr[1]+i))
								syn_time = time.time()
	
				if self.dat.SYN:
					for i in range(mn,mx):
						if i!=my_pub_offset:
					msg = self.dat.compose('ACK',"%s %s,%s" % (count, self.session_name, my_pub_offset) )
					self.send(msg, (r_addr[0], r_addr[1]+i))
			if r:
				data,addr=self.recv()
				print("data: ", data)
				self.dat = PunchObject(data)
				if self.dat.MSG:
					num_nomsg = 0
					print(str(self.dat))
				elif self.dat.SYN:
					print("recvd SYN ", str(self.dat))
					if my_pub_offset == None and not self.session_name in data[1:]:
						my_pub_offset = int(data[1:].split(",")[-1])
						synned = True
				elif self.dat.ACK:
					str_ro = data[1:].split(",")[-1]
					if str_ro != "None":
						remote_offset = int(str_ro)
					ack_time = time.time()-syn_time
					print("recvd ACK ", str(self.dat), ack_time)
					if synned:
						connected = True
						print("Connected.")
				elif self.dat.JSON:
					self.track_dict = json.loads(data[1:])
				else:
					num_nomsg += 1
			time.sleep(acc)
		
if __name__ == "__main__":
	SERVER_IP = '192.43.193.103'
	SERVER_PORT = 60000
	if len(sys.argv)<3:
		print("------------------\nUsage: python hole-punch.py your-name target-name\n")
		exit(0)
	name = sys.argv[1]
	connect_name = sys.argv[2]
	pt = Endpoint(name)
	pt.connect_endpoint(connect_name)
