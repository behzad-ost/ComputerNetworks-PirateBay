import sys
import socket
import time
from thread import *
import json
from random import randint
import threading

HOST = 'localhost'
PORT = 3503
IP = ""
# PING_PORT = 3502

class Node:
	def __init__(self, id, ip):
		self.id = id
		self.ip = ip
		self.records = []
		self.saveQueue = []

	def	describe(self):
		print "================"
		print "id", self.id
		print self.records
		if hasattr(self,"nextPeer"):
			print "nextPeer", self.nextPeer.id, self.nextPeer.ip
		if hasattr(self,"prevPeer"):
			print "prevPeer", self.prevPeer.id, self.prevPeer.ip
		if hasattr(self,"twoNextPeer"):
			print "twoNextPeer", self.twoNextPeer.id, self.twoNextPeer.ip
		print "================"

	def setNextPeer(self, nextPeerID, nextPeerIP):
		self.nextPeer = Node(nextPeerID,nextPeerIP)
	def setTwoNextPeer(self, nextPeerID, nextPeerIP):
		self.twoNextPeer = Node(nextPeerID,nextPeerIP)		
	def setPrevPeer(self, nextPeerID, nextPeerIP):
		self.prevPeer = Node(nextPeerID,nextPeerIP)

	def saveAsStatic(self):
		f = open("staticNodes","a")
		f.write(self.ip + " " + self.id + '\n')
		f.close()

	def connect(self, ip, port):
		self.socket = socket.create_connection((ip , port))
		print "connected to " + ip
	def send(self, msg):
			self.socket.sendall(msg)
	def recv(self, size):
		return self.socket.recv(size)
	def listen(self, host, port):
			self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.serverSocket.bind((host, port))
			self.serverSocket.listen(10)
			self.describe()
			print "Listening On " + str(port)
			while 1:
				conn, addr = self.accept()
				conn.settimeout(20)
				start_new_thread(self.messageHandler ,(conn,addr))
			print "AFTER LISTENING!"
	def accept(self):
		return self.serverSocket.accept()
	def close(self):
		self.socket.close()

	def introduceToNextPeer(self):
		self.connect(self.nextPeer.ip, PORT)
		body = json.dumps({"type": "newNode", "id": self.id})
		self.send(body)
		reply = self.recv(4096)
		try:
			res = json.loads(reply)
			self.setPrevPeer(res["prevPeerID"], res["prevPeerIP"])
			print reply
		except Exception as e:
			print reply

		self.close()

	def greetNewNode(self, connection, addr):
		# reply = "Hello my prev! FROM: " + self.ip + " PrevID: " + self.prevPeer.id
		# self.setPrevPeer()
		reply = json.dumps({"prevPeerID": self.prevPeer.id, "prevPeerIP": self.prevPeer.ip})
		connection.sendall(reply)

	def warnPrevForUpdate(self, newNextId, newNextIP):
		self.connect(self.prevPeer.ip, PORT)
		body = json.dumps({"type": "updateNext", "newNextId": newNextId, "newNextIP": newNextIP})
		self.send(body)
		reply = self.recv(4096)
		# res = json.loads(reply)
		print reply
		print "Setting PREVPEER to ", newNextId, newNextIP 
		self.setPrevPeer(newNextId,newNextIP)
		self.close()
		self.describe()

	def locatePlace(self, ip, id):
		res = ""
		if int(id) == int(self.id) or int(id) == int(self.nextPeer.id) or int(id) == int(self.prevPeer.id):
			res = json.dumps({"status": 500})
			self.connect(ip, PORT)
			self.send(res)
			reply = self.recv(4096)
			self.close()
		elif int(id) > int(self.id) and int(id) < int(self.nextPeer.id) :
			print "It Should Come Here ", self.ip
			res = json.dumps({"status": 200 , "nextPeerIP": self.nextPeer.ip ,"nextPeerID": self.nextPeer.id , "prevPeerIP": self.ip, "prevPeerID": self.id})
			self.connect(ip, PORT)
			self.send(res)
			reply = self.recv(4096)
			print reply
			self.close()
		else:
			self.connect(self.nextPeer.ip, PORT)
			body = json.dumps({"type": "locate", "ip":ip, "id": id})
			self.send(body)
			reply = self.recv(4096)
			print reply
			self.close()

	def getQueuedRecord(self, ip, key):
		print "find ", key, "from ", ip
		if ip == self.ip:
			for record in self.saveQueue:
				item = json.loads(record)
				print "item"
				print item
				if item["key"] == key:
					self.saveQueue.remove(record)
					return record
		else:
			self.connect(ip, PORT)
			body = json.dumps({"type": "giveMeRecord", "key": key})
			self.send(body)
			reply = self.recv(4096)
			# self.records.append(reply)
			# print "RECORDS: "
			# print self.records
			self.close()
			return reply
		
	def save(self, ip, key):
		print self.saveQueue
		if int(key) <= int(self.id) and abs(int(key)-int(self.id)) < abs(int(key)-int(self.prevPeer.id)):
			print "found the place"
			record = self.getQueuedRecord(ip,key)
			print record
			self.records.append(record)
		else:
			self.connect(self.nextPeer.ip, PORT)
			# print "IP: ", ip
			body = json.dumps({"type": "save", "ip":ip, "key": key})
			self.send(body)
			reply = self.recv(4096)
			# print reply
			self.close()
		print self.records

	def messageHandler(self, conn, addr):
		print "Got connection from", addr
		while True:
			data = conn.recv(1024)
			if not data: 
			    break
			body = json.loads(data)
			print body
			if body['type'] == "newNode":
				if not hasattr(self, 'nextPeer'):
					self.setNextPeer(body["id"],addr[0])
				if hasattr(self, 'prevPeer'):
					t = threading.Thread(target = self.warnPrevForUpdate,args = (body["id"],addr[0]))
					t.daemon = True
					t.start()
					self.greetNewNode(conn,addr)
					# start_new_thread(, (body["id"],addr[0]))
				else:
					self.setPrevPeer(body["id"],addr[0])
					conn.sendall("Hello prev!")
				self.describe() ####
			elif body['type'] == "updateNext":
				self.setNextPeer(body["newNextId"],body["newNextIP"])
				# self.introduceToNextPeer()
				conn.sendall("Thank you!")
				self.describe() ####
			elif body['type'] == "locate":
				conn.sendall("ok I'm going to find you a place. From: " + self.ip)
				self.locatePlace(body["ip"], body["id"])
			elif body['type'] == "save":
				conn.sendall("ok I'm going to save it. From: " + self.ip)
				self.save(body["ip"], body["key"])
			elif body['type'] == "giveMeRecord":
				print "GIVE HIM SOMEHTING"
				conn.sendall(self.getQueuedRecord(self.ip, body["key"]))

			# elif body['type'] == "ping":
			# 	print "I am pinged!"

		print "closing connection ... "
		conn.close()

	def commadnHandler(self, cmd):
		print "You have enterd", cmd
		args = cmd.split(' ')
		if args[0] == "save":
			self.saveQueue.append(json.dumps({"key":args[1], "value":args[2]}))
			# print "IP: ", self.ip
			self.save(self.ip, args[1])
		if args[0] == "desc":
			self.describe()

	# def pingNextPeer(self):
	# 		if hasattr(self,"nextPeer"):

	# def pingTwoNextPeer(self):
	# 		if hasattr(self,"twoNextPeer"):	

	# def ping(self):
	# 		start_new_thread(self.pingNextPeer())
	# 		start_new_thread(self.pingTwoNextPeer())

def createDynamicNode(file, selfIP):
	f = open("staticNodes","r")
	lines = f.readlines()
	f.close()
	staticRandom = randint(0,len(lines)-1)
	# print lines
	# print staticRandom
	randID1 = lines[staticRandom][:-1].split(' ')[1]
	randIP1 = lines[staticRandom][:-1].split(' ')[0]

	randID2 = lines[staticRandom + 1 % len(lines)][:-1].split(' ')[1]

	newID = randint(int(randID1),int(randID2))
	
	print newID

	newIP = selfIP
	n = Node(newID,newIP)

	# n.locatePlace(newIP, id)

	n.connect(randIP1, PORT)
	body = json.dumps({"type": "locate", "ip": newIP, "id": newID})
	n.send(body)
	reply = n.recv(4096)
	n.close()
	print reply

	n.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	n.serverSocket.bind(('', PORT))
	n.serverSocket.listen(10)
	n.describe()
	print "Listening on ", PORT
	# n.listen('', PORT)
	# n.locate(randIP1, newID)
	conn, addr = n.accept()
	data = conn.recv(1024)
	print data
	res = json.loads(data)
	conn.sendall("Thank you for finding me a place.")


	if res['status'] == 200:
		n.setNextPeer(res['nextPeerID'], res['nextPeerIP'])
		n.setPrevPeer(res['prevPeerID'], res['prevPeerIP'])
		print "Dynamic set prev and next"
		n.describe()
		n.introduceToNextPeer()
		t =threading.Thread(target = n.listen,args = ('',PORT))
		t.daemon = True
		t.start()
		return n
	else:
		createDynamicNode(file, selfIP)



def main():

	#python node.py ...:
	#args[1]: --static/--dynamic	
	#args[2]: --id    /--file
	#args[3]: idNumber   /file
	#args[4]: (--nextPeerid)
	#args[5]: (nextPeerId)
	#args[6]: (--nextPeerip)
	#args[7]: (nextPeerIP)

	args = sys.argv
	IP = args[len(args)-1]
	print "My IP is ", IP
	print ">>>>>>>>>>>>>>>>>>>>>>>"

	if len(args) == 5:
		if args[1] == "--static":
			n = Node(args[3],IP)
			# n.saveAsStatic()
			t =threading.Thread(target = n.listen,args = ('',PORT))
			t.daemon = True
			t.start()
			return n
		if args[1] == "--dynamic":
			n = createDynamicNode(args[3], IP)
			return n
	else:
		n = Node(args[3], IP)
		n.setNextPeer(args[5],args[7])
		if args[3] == "10" :
			n.setPrevPeer(args[5],args[7])
		# n.saveAsStatic()
		n.introduceToNextPeer()
		t =threading.Thread(target = n.listen,args = ('',PORT))
		t.daemon = True
		t.start()
		return n


if __name__ == '__main__':
	me = main()
	while True:
		cmd = raw_input()
		me.commadnHandler(cmd)


