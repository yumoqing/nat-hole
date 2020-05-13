"""
message transfer protocol
message format
send data format:
0|+|0|+|sender|+|receiver|+|body

cryptflag:'0': not crypted; '1':crypted
ziped:'0': not zipped,'1':zipped
msg: text need to send
receiver:id in p2p world
sender:id in p2p world
rpubk:receiver's public key
rprik:receiver's private key
spubk:sender's public key
sprik:sender's private key

"""
import asyncio
try:
	import ujson as json
except:
	import json

import socket
from platform import platform

from asyncio import DatagramProtocol
from appPublic.rsa import RSA
from appPublic.rc4 import RC4
from appPublic.uniqueID import getID
from appPublic.dictObject import DictObject
from appPublic.jsonConfig import getConfig

def getlocalip():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(('8.8.8.8',80))
	ip = s.getsockname()[0]
	s.close()
	return ip

class PeerData:
	def getPeerPublickey(self,peername):
		pass
	
	def getPeerAddr(self,peername):
		pass

	def setPeerAddr(self,peername,addr):
		pass

	def __init__(self,myname,privatefile,coding='utf-8'):
		self.rsa = RSA()
		self.rc4 = RC4()
		self.nodes = {}
		self.myname = myname
		self.coding = coding
		self.private_key = self.rsa.read_privatekey(privatefile)
		self.public_key = self.rsa.create_publickey(self.private_key)

	def getReceivedData(self,transferBytes,addr):
		crypted,zipped,sender,receiver,body = transferBytes.split('|+|')
		if receiver != self.myname:
			return None
		self.setPeerAddr(sender,addr)
		if crypted == '0':
			d = json.loads(body)
			d['sender'] = sender
			d['receiver'] = receiver
			d['sender_addr'] = addr
			return DictObject(**d)
		cryptedkey,sign,cryptedText = body.split('|@|')
		key = self.rsa.decode(self.private_key,cryptedkey)
		text = rc4.decode(cryptText,key)
		spubk = self.rsa.publickeyFromText(self.getPeerPublickey(sender))
		r = self.rsa.check_sign(spubk,text,sign)
		if not r:
			return None
		d = json.loads(text)
		d['sender'] = sender
		d['receiver'] = receiver
		d['sender_addr'] = addr
		return DictObject(**d)

	def setSendData(self,receiver,text,crypted='0',zipped='0'):
		if receiver is None:
			print('Error**********,receiver is None')
			raise Exception('receiver is None')
		if crypted == '0':
			arr = [crypted,'0',self.myname,receiver,text]
			return '|+|'.join(arr)
		
		rpubk = self.rsa.publickeyFromText(self.getPeerPublickey(receiver))
		key = getID()
		ctext = self.rc4.encode(text,key)
		sign = self.rsa.sign(self.private_key,text)
		cryptedkey = self.rsa.encode(rpubk,key)
		arr = [cryptedkey,sign,ctext ]
		return '|@|'.join(arr)

class TextUDPProtocol:
	def connection_made(self,transport):
		self.transport = transport
		self.on_connect(transport)

	"""
	def heartbeat(self):
		if not hasattr(self,'hb_cnt'):
			self.hb_cnt = 0
		self.hb_cnt = self.hb_cnt + 1
		config = getConfig()
		loop = asyncio.get_event_loop()
		hb_to = config.heartbeat_timeout or 180
		loop.call_later(hb_to,self.heartbeat)
		self.send('heartbeat(%d)(%d)' %(self.hb_cnt,hb_to),
			(socket.gethostbyname(config.center),
			config.port))
	"""
	def datagram_received(self,data,addr):
		# print('datagram_received',data,addr)
		message = data.decode(self.coding)
		self.on_recv(message,addr)	

	def send(self,message,addr):
		if not isinstance(message,bytes):
			message = message.encode(self.coding)
		self.transport.sendto(message,addr)
	
	def error_received(self,exc):
		print('Error received:',exc)
		self.on_error(exc)

	def connection_lost(self,exc):
		self.on_lost_connect(exc)

	def on_lost_connect(self,exc):
		pass

	def on_error(self,exc):
		pass

	def on_after_recv(self,message,addr):
		return message

	def on_before_send(self,message,addr):
		return message

	def on_recv(self,message,addr):
		print('addr=',addr,'message=',message)

	def on_connect(self,transport):
		pass

def serverFactory(Klass, host,port,loop=None,coding='utf-8'):
	if loop == None:
		loop = asyncio.get_event_loop()
	listen = loop.create_datagram_endpoint(
		Klass, local_addr=(host,port))
	transport,server = loop.run_until_complete(listen)
	server.coding = coding
	server.loop = loop
	server.port = port
	return server
	
def clientFactory(Klass, host,port,loop=None,coding='utf-8'):
	if loop == None:
		loop = asyncio.get_event_loop()
	connect = loop.create_datagram_endpoint(
		Klass, remote_addr=(host,port))
	transport,client = loop.run_until_complete(connect)
	client.coding = coding
	client._loop = loop
	client.port = port
	client.server = host
	return client
	
if __name__ == '__main__':
	class MyServer(TextUDPProtocol):
		def on_recv(self,message,addr):
			print("recv:",message,addr)
			self.send(messager,addr)

	loop = asyncio.get_event_loop()
	server = serverFactory(MyServer,9999)
	loop.run_forever()
	server.transport.close()
