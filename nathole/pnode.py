
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
		if pk is None:
			return None
		config = getConfig()
		if config.publickeys:
			return config.publickeys.get(peername)
		return None


class NodeProtocol(TextUDPProtocol):
	def __init__(self):
		self.config = getConfig()
		self.rsaobj = RSA()
		self.center_addr = gethostbyname(self.config.center), \
					self.config.port
		self.direct_addrs = {}

		self.cpd = NodePeerData(config.nodeid,config.privatekey)
		self.local_ip = getlocalip()
		self.commands={
			"greeting":self.greeting,
			"heartbeatresp":self.heartbeatresp,
			"getpeerinforesp":self.getpeerinfo,
			"forwardmsgresp":self.forwardmsgresp,
			"a_connect_b":self.a_connect_b,
			"b_connect_a":self.b_connect_a,
		}
	
	def on_recv(self,data,addr):
		data = self.cpd.getReceivedData(data,addr)
		func = self.commands.get(data.cmd)
		if func == None:
			return
		return func(data)

	def greeting(self,d):
		print(self.config.nodeid,'greeting(),d=',d)
		
	def b_connect_a(self,d):
		print(self.config.nodeid, 'b_connect_a(),d=',d)
		self.direct_addrs[d.sender] = d.sender_addr
		d = {
			"cmd":"greeting",
			"msg":"Hello peer ' + d.sender
		}
		text = json.dumps(d)
		msg = self.cpd.setSendData(d.sender,text)
		self.send(msg, d.sender_addr)

	def a_connect_b(self,d):
		print('a_connect_b',d)
		self.direct_Addrs[d.sender] = d.sender_addr
		
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
		d = {
			"cmd":"getpeerinfo",
			"peername":peername
		}
		print(self.config.nodeid,'getpeerinfo(),d=',d)
		txt = json.dumps(d)
		msg = self.cpd.setSendData(self.config.center,txt)
		self.send(msg,self.center_addr)
		loop = asyncio.get_event_loop()
		loop.call_later(60, self.getpeerinfo,peername)

	def atSameNAT(self,addr):
		ips = addr[0].split('.')
		myips = self.inner_ip.split('.')
		if ips[:3] == myips[:3] and ips[3] != myips[3]:
			return True
		return False

	def getpeerinforesp(self,d):
		"""
		{
			"cmd":"getpeerinforesp"
			"publickey":rpubk,
			"peername":d.peername,
			"internetinfo":addr,
			"innerinfo":addr1
		}
		"""
		print(self.config.nodeid,'getpeeriforesp(),d=',d)
		rpubk = d.publickey
		self.cpd.publickeys[d.peername] = rpubk
		retdata = {
			"cmd":"a_connect_b",
			"peername":d.peername,
			"to_addr":d.internetinfo,
			"from_addr":self.internet_addr
		}
		text = json.dumps(retdata)
		msg = self.cpd.setSendData(d.sender,text)
		self.send(msg,d.internetinfo)

	def forwardmsgresp(self,d):
		"""
		{
			"cmd":"forwardmsgresp",
			"forwardfrom":"xxx",
			"forwardto":peername,
			"forwarddata":{
			}
		}
		"""
		print(self.config.nodeid,'forwardmsgresp(),d=',d)
		if d.forwardto[0] != self.config.nodeid:
			return

		if d.forwardfrom != d.forwarddata.nodeid:
			return

		b2a = {
			"cmd":"b_connect_a",
			"sender_id":self.config.nodeid,
			"received_id":d.forwardfrom,
		}
		txt = json.dumps(b2a)
		msg = self.cpd.setSendData(d.forwardfrom, json.dumps(d)) 
		if isSameNAT(forwarddata.innerinfo):
			self.send(msg, d.forwarddata.innerinfo)
		self.send(msg,d.forwarddata.internetinfo)

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
		loop.call_later(60,server.getpeerinfo, sys.argv[2])
	loop.run_forever()
