import select
import socket
import time
import json
from threading import Thread

class OneClient:
	def __init__:(self, sock):
			self.tcp = sock
			self.name = ""
			self.intransfer = False
			self.LRT = time.time()
			self.buf = ""

def transfering(sender, receiver):
	while True:
		dta = None
		try:
			dta = sender.tcp.recv(1024)
		except:
			break
		
		if not dta:
			break

		try:
			receiver.tcp.send(dta)
		except:
			break
		
		sender.LRT = time.time()
		receiver.LRT = time.time()

serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv.bind(('0.0.0.0', 5050))
serv.listen(50)
tcp_inputs = [serv]
clients = []

while True:
	r, w, e = select.select(tcp_inputs, [], [], 0.05)
	
	for s in clients:
		if time.time() - s.LRT >= 60.0:
			s.tcp.close()
			tcp_inputs.remove(s.tcp)
			clients.remove(s)
			del(s)

	if not r:
		continue
	
	else:
		for rd in r:
			if rd == serv:
				aclient, addr = serv.accept()
				tcp_inputs.append(aclient)
				cnt = OneClient(aclient)
				clients.append(cnt)
			
			else:
				for s in clients:
					if s.tcp == rd and !s.intransfer:
						dta = None
						try:
							dta = rd.recv(1)
						except:
							rd.close()
							tcp_inputs.remove(rd)
							clients.remove(s)
							del(s)
							continue
						
						if not dta:
							rd.close()
							tcp_inputs.remove(rd)
							clients.remove(s)
							del(s)
							continue
						
						if dta == b'\n':
							try:
								indata = json.loads(s.buf)
							except:
								rd.close()
								tcp_inputs.remove(rd)
								clients.remove(s)
								del(s)
								continue
							
							s.buf = ""
							
							if indata['act'] == "PING":
								s.LRT = time.time()
							
							elif indata['act'] == "LOGIN":
								s.name = indata['name']
								if len(s.name) < 3:
									outdata = {"act": "DENIED", "info": "Name too short"}
									try:
										s.tcp.send(json.dumps(outdata).encode() + b"\n")
									except:
										rd.close()
										tcp_inputs.remove(rd)
										clients.remove(s)
										del(s)
										continue
								
								grant = True
								for y in clients:
									if y != s and len(y.name) > 2:
										if y.name.lower() == s.name.lower():
											grant = False
								
								if grant:
									outdata = {"act": "GRANT"}
									try:
										s.tcp.send(json.dumps(outdata).encode() + b"\n")
									except:
										rd.close()
										tcp_inputs.remove(rd)
										clients.remove(s)
										del(s)
										continue
								
								else:
									outdata = {"act": "DENIED", "info": "Name already exists"}
									try:
										s.tcp.send(json.dumps(outdata).encode() + b"\n")
									except:
										rd.close()
										tcp_inputs.remove(rd)
										clients.remove(s)
										del(s)
										continue

							elif indata['act'] == "SEND":
								grant = False
								for y in clients:
									if y != s and len(y.name) > 2:
										if y.name.lower() == indata['to'].lower():
											grant = True
											break
								
								if grant:
									outdata = {"act": "SEND", "from": s.name, "file": indata['file']}
									try:
										y.tcp.send(json.dumps(outdata).encode() + b"\n")
									except:
										y.tcp.close()
										tcp_inputs.remove(y.tcp)
										clients.remove(y)
										del(y)
										continue

								else:
									outdata = {"act": "DENIED", "info": "Member isnt online"}
									try:
										s.tcp.send(json.dumps(outdata).encode() + b"\n")
									except:
										rd.close()
										tcp_inputs.remove(rd)
										clients.remove(s)
										del(s)
							
							elif indata['act'] == "NOPE":
								grant = False
								for y in clients:
									if y != s and len(y.name) > 2:
										if y.name.lower() == indata['to'].lower():
											grant = True
											break
								
								if grant:
									outdata = {"act": "DENIED", "info": "Member doesnt want this file"}
									try:
										y.tcp.send(json.dumps(outdata).encode + b"\n")
									except:
										y.tcp.close()
										tcp_inputs.remove(y.tcp)
										clients.remove(y)
										del(y)
										continue
							
							elif indata['act'] == "OK":
								grant = False
								for y in clients:
									if y != s and len(y.name) > 2:
										if y.name.lower() == indata['to'].lower():
											grant = True
											break
								
								if grant:
									outdata = {"act": "START"}
									try:
										y.tcp.send(json.dumps(outdata).encode + b"\n")
									except:
										y.tcp.close()
										tcp_inputs.remove(y.tcp)
										clients.remove(y)
										del(y)
										continue

									y.intransfer = True
									s.intransfer = True
									t = Thread(target=transfering, args=(sender=y, receiver=s,))
									t.start()
									
