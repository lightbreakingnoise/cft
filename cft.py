import select
import socket
import time
import json
import hashlib
import sys
import os
from os.path import basename
from threading import Thread

global intransfer
global serv
intransfer = False

def pinger():
	global intransfer
	global serv
	while intransfer == False:
		time.sleep(5.0)
		if intransfer == True:
			break
		outdata = {"act": "PING"}
		try:
			serv.send(json.dumps(outdata).encode() + b"\n")
		except:
			sys.exit()

def showperc(perc):
	txt = "["
	for i in range(70):
		if i < perc:
			txt += "="
		else:
			txt += " "
	txt += "]\r"
	sys.stdout.write(txt)

name = input("Enter Name>")

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
	serv.connect(('78.47.41.154', 5050))
except:
	print("Couldnt connect")
	sys.exit()

outdata = {"act": "LOGIN", "name": name}
try:
	serv.send(json.dumps(outdata).encode() + b"\n")
except:
	print("Couldnt send json")
	sys.exit()

t = Thread(target=pinger)
t.start()

f = serv.makefile('r')
indata = json.loads(f.readline())

if indata['act'] == "DENIED":
	print(indata['info'])
	sys.exit()

if len(sys.argv) == 2:
	toname = input("Enter Members Name>")
	
	x = open(sys.argv[1], "rb")
	x.seek(0, os.SEEK_END)
	length = x.tell()
	x.seek(0, os.SEEK_SET)
	m = hashlib.md5()
	m.update(x.read())
	z = m.hexdigest()
	del(m)
	x.close()
	
	outdata = {"act": "SEND", "to": toname, "file": basename(sys.argv[1]), "size": length, "md5": z}
	try:
		serv.send(json.dumps(outdata).encode() + b"\n")
	except:
		print("Couldnt send json")
		sys.exit()
	
	while True:
		r, w, e = select.select([serv], [], [], 0.1)
		if not r:
			continue
		else:
			break

	indata = json.loads(f.readline())
	if indata['act'] == "START":
		print("Start Transfer")
		intransfer = True
		pos = 0
		operc = 0
		x = open(sys.argv[1], "rb")
		while True:
			dta = None
			try:
				dta = x.read(1024)
			except:
				break
			
			if not dta:
				break
			
			serv.send(dta)
			pos += len(dta)
			nperc = round((pos*70.0)/length)
			if nperc != operc:
				operc = nperc
				showperc(nperc)
		
		print("\nfinish")
		x.close()
		serv.close()

else:
	while True:
		r, w, e = select.select([serv], [], [], 0.1)
		
		if not r:
			continue
		
		indata = json.loads(f.readline())
		
		if indata['act'] == "SEND":
			print(indata['from'] + " wants to send " + str(indata['size']) + " bytes in " + indata['file'])
			inp = input("Accept? y/n>")
			if inp == "y":
				outdata = {"act": "OK", "to": indata['from']}
				try:
					serv.send(json.dumps(outdata).encode() + b"\n")
				except:
					sys.exit()
				
				intransfer = True
				pos = 0
				operc = 0
				length = indata['size']
				m = hashlib.md5()
				x = open(indata['file'], "wb")
				while True:
					dta = None
					try:
						dta = serv.recv(1024)
					except:
						break
					
					if not dta:
						break
					
					m.update(dta)
					x.write(dta)
					pos += len(dta)
					nperc = round((pos*70.0)/length)
					if nperc != operc:
						operc = nperc
						showperc(nperc)
				
				x.close()
				serv.close()
				print("\nfinish")
				z = m.hexdigest()
				del(m)
				if z == indata['md5']:
					print("md5 checksum correct")
				else:
					print("md5 checksum incorrect")
				sys.exit()

			else:
				outdata = {"act": "NOPE", "to": indata['from']}
				try:
					serv.send(json.dumps(outdata).encode() + b"\n")
				except:
					sys.exit()
