
# p node 
import sys
import asyncio
try:
	import ujson as json
except:
	import json
from socket import gethostbyname

from appPublic.uniqueID import getID
from appPublic.jsonConfig import getConfig
from appPublic.rsa import RSA
from appPublic.dictObject import DictObject
from sqlor.dbpools import DBPools

from udppro import serverFactory,TextUDPProtocol, PeerData, getlocalip

class NodePeerData(PeerData):
	def getPeerPublickey(self,peername):
		pk = self.publickeys.get(peername)
		return pk
		config = getConfig()
		if config.publickeys:
			return config.publickeys.get(peername)
		return None


class NodeProtocol(TextUDPProtocol):
	def __init__(self,loop=None):
		self.config = getConfig()
		if loop is None
			self.loop = asyncio.get_event_loop()
		self.peertasks = {}
		self.rsaobj = RSA()
		self.center_addr = gethostbyname(self.config.center), \
					self.config.port
		self.direct_addrs = {}

		self.cpd = NodePeerData(config.nodeid,config.privatekey)
		self.cpd.publickeys = {}
		self.local_ip = getlocalip()
		self.commands={
			"greeting":self.greeting,
			"heartbeatresp":self.heartbeatresp,
			"getpeerinforesp":self.getpeerinforesp,
			"forwardmsg":self.forwardmsg,
			"peer_connect":self.peer_connect,
		}
	
	def on_recv(self,data,addr):
		data = self.cpd.getReceivedData(data,addr)
		func = self.commands.get(data.cmd)
		if func == None:
			print(self.config.nodeid,data.cmd,' not defined',data,type(data.cmd))
			return
		return func(data)

	def greeting(self,d):
		print(self.config.nodeid,'greeting(),d=',d)
		d.cnt = d.cnt + 1
		if d.cnt > 1:
			return 
		f = d.from
		d.from = d.to
		d.o = f
		addr = d.sender_addr
		reciever = d.sender
		del d['sender']
		del d['receiver']
		text = json.dumps(d)
		msg = self.cpd.setSendData(receiver,text)
		self.send(msg, addr)
		
	def make_peer_connect(self,peerdata):

	def peer_connect(self,d):
		print(self.config.nodeid, 'peer_connect(),d=',d)
		self.direct_addrs[d.sender] = d.sender_addr
		d = {
			"cmd":"greeting",
			"msg":"Hello peer " + d.sender,
			"from":self.config.nodeid,
			"cnt":0,
			"to":d.sender
		}
		text = json.dumps(d)
		msg = self.cpd.setSendData(d.sender,text)
		self.send(msg, d.sender_addr)

	def onlinelist(self):
		req = {
			"cmd":"onlinelist"
		}
		text = json.dumps(req)
		msg = self.cpd.setSendData(self.config.center,text)
		self.send(msg, self.center_addr)

	def onlinelistresp(self, d):
		self.onlines = d.onlinelist

	def heartbeat(self):
		dat = {
			"cmd":"heartbeat",
			"nodeid":self.config.nodeid,
			"publickey":self.rsaobj.publickeyText(self.cpd.public_key),
			"innerinfo":(self.local_ip,self.config.port),
                }
		# print('heartbeat=',dat,self.config.nodeid)
		txt = json.dumps(dat)
		msg = self.cpd.setSendData(self.config.center,txt)
		self.send(msg,self.center_addr)
		loop = asyncio.get_event_loop()
		loop.call_later(self.config.heartbeat_timeout or 30,self.heartbeat)

	def heartbeatresp(self,d):
		print(self.config.nodeid,'heartbeatresp(),d=',d)
		self.internet_addr = d.internetinfo

	def getpeerinfo(self,peername):
		"""
		{
			"cmd":"getpeerinfo",
			"peername":"peername"
		}
		"""
		loop = asyncio.get_event_loop()
		loop.call_later(15, self.getpeerinfo, peername)
		d = {
			"cmd":"getpeerinfo",
			"peername":peername
		}
		print(self.config.nodeid,'getpeerinfo(),d=',d)
		txt = json.dumps(d)
		msg = self.cpd.setSendData(self.config.center,txt)
		self.send(msg,self.center_addr)

	def isSameNAT(self,addr):
		ips = addr[0].split('.')
		myips = self.local_ip.split('.')
		if ips[:3] == myips[:3] and ips[3] != myips[3]:
			return True
		return False

	def getpeerinforesp(self,d):
		"""
		{
			"cmd":"getpeerinforesp"
			"publickey":rpubk,
			"peername":d.nodeid,
			"internetinfo":addr,
			"innerinfo":addr1
		}
		"""
		print(self.config.nodeid,'getpeeriforesp(),d=',d)
		rpubk = d.publickey
		self.cpd.publickeys[d.peername] = rpubk
		retdata = {
			"cmd":"peer_connect",
			"to_addr":d.internetinfo,
			"from_addr":self.internet_addr
		}
		text = json.dumps(retdata)
		msg = self.cpd.setSendData(d.nodeid,text)
		addr = tuple(d.internetinfo)
		self.try_connect(msg,addr,d.nodeid)

	def try_connect(self, msg,addr,peername):
		task = self.loop.call_later(0.5,self.try_connect,msg,addr)
		self.peertask[peername] = task
		self.send(msg,addr)

	def forwardmsg(self,d):
		"""
		{
			"cmd":"forwardmsg",
			"forwardfrom":"xxx",
			"forwardto":peername,
			"forwarddata":{
			}
		}
		"""
		print(self.config.nodeid,'forwardmsg(),d=',d)
		if d.forwardto != self.config.nodeid:
			print(self.config.nodeid,'forwardto is not me',d.forwardto)
			return

		if d.forwardfrom != d.forwarddata.nodeid:
			return

		b2a = {
			"cmd":"peer_connect",
			"to_addr":d.forwarddata.internetinfo
			"from_addr":self.internet_addr
		}
		txt = json.dumps(b2a)
		msg = self.cpd.setSendData(d.forwardfrom, json.dumps(d)) 
		addr = tuple(d.forwarddata.internetinfo)
		self.try_connect(msg,addr,d.forwardfrom)

if __name__ == '__main__':
	from appPublic.folderUtils import ProgramPath
	name = None
	pp = ProgramPath()
	workdir = pp
	if len(sys.argv)>1:
		workdir = sys.argv[1]
		
	config = getConfig(workdir,NS={'workdir':workdir,'ProgramPath':pp})
	loop = asyncio.get_event_loop()
	server = serverFactory(NodeProtocol,'0.0.0.0',config.port)
	server.heartbeat()
	if len(sys.argv) > 2:
		loop.call_later(30,server.getpeerinfo, sys.argv[2])
	loop.run_forever()
