# center node 
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

from udppro import serverFactory,TextUDPProtocol, PeerData

class CenterPeerData(PeerData):
	def getPeerPublickey(self,peername):
		return self.nodeinfo[peername].public_key
		config = getConfig()
		if config.publickeys:
			return config.publickeys.get(peername)
		return None


class CenterProtocol(TextUDPProtocol):
	
	def __init__(self):
		self.config = getConfig()
		self.rsaobj = RSA()
		self.nodeinfo = {}
		self.cpd = CenterPeerData(config.nodeid,config.privatekey)
		self.commands={
			"heartbeat":self.heartbeat,
			"getpeerinfo":self.getpeerinfo,
			"onlinelist":self.onlinelist,
		}

	def on_recv(self,data,addr):
		print(self.config.nodeid,'on_recv()', addr)
		data = self.cpd.getReceivedData(data,addr)
		print(self.nodeid,'on_recv():d=',data)
		func = self.commands.get(data.cmd)
		if func == None:
			return
		return func(data)

	def onlinelist(self,d):
		resp = {
			"cmd":"onlinelistresp",
			"onlinelist":[i for i in self.nodeinfo.keys() if i!=d.sender ]
		}
		
		text = json.dumps(resp)
		msg = self.cpd.setSendData(d.sender,text)
		self.send(msg, d.sender_addr)

	def heartbeat(self,d):
		"""
		d has following format
		{
			nodeid:"fff",
			publickey:"ffkgrjgr",
			innerinfo:('192.168.1.22',19993),
			service:{
			}
		}
		"""
		d.nodeinfo.internetinfo = d.sender_addr
		self.nodeinfo[d.nodeid] = d.nodeinfo
		retdata = {
			"cmd":"heartbeatresp",
			"internetinfo":d.sender_addr
		}
		text = json.dumps(retdata)
		msg = self.cpd.setSendData(d.sender,text)
		self.send(msg,d.sender_addr)

	def getpeerinfo(self,d):
		"""
		{ request
			"cmd":"getpeerinfo",
			"peername":"peername"
		}
                { response
                        "cmd":"getpeerinforesp"
                        "publickey":rpubk,
                        "peername":d.peername,
                        "internetinfo":addr,
                        "innerinfo":addr1
                }
                { forward to b
                        "cmd":"forwardmsgresp",
                        "forwardfrom":"xxx",
                        "forwardto":peername,
                        "forwarddata":{
                        }
                }

		"""
		nodeinfo = self.nodeinfo.get(d.peername)
		retdata = {}
		if nodeinfo is None:
			retdata={
				"publickey":None,
				"cmd":"getpeerinforesp",
				"peername":d.peername,
				"internetinfo":None,
				"innerinfo":None
			}
		else:
			retdata.update(nodeinfo)
		text = json.dumps(retdata)
		msg = self.cpd.setSendData(d.sender,text)
		self.send(msg,d.sender_addr)
		forward = {
			"cmd":"forwardmsg",
			"forwardfrom":d.sender,
			"forwardto":d.peername,
			"forwarddata":self.nodeinfo.get(d.sender)
		}
		text = json.dumps(forward)
		msg,addr = self.cpd.setSendData(d.peername,text)
		self.send(msg,nodeinfo.internetinfo)

if __name__ == '__main__':
	from appPublic.folderUtils import ProgramPath
	pp = ProgramPath()
	workdir = pp
	if len(sys.argv) > 1:
		workdir = sys.argv[1]
	config = getConfig(workdir,NS={'workdir':workdir,'ProgramPath':pp})
	loop = asyncio.get_event_loop()
	server = serverFactory(CenterProtocol, '0.0.0.0', config.port)
	loop.run_forever()

