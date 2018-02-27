import os
import commands

NumofReplicas = 4
NumofClients = 2

def create_replicas(NumofReplicas = 6):
	_port = 9100
	_id = 0
	_p = 0
	_timeout = 0.5 # second
	_host = "127.0.0.1"

	for server in range(NumofReplicas):
		cmd = "kill $(lsof -t -i:{0}) && python3 ./server.py --id {1} --host {2} --port {3} --p {4} --timeout {5} &".format(_p, _id, _host, _port, _p, _timeout)
		print (os.system(cmd))
		_id += 1
		_port += 2

def create_clients(NumofClients = 2):
	_port = 9200
	_id = 0
	_p = 0
	_timeout = 0.5 # second
	_host = "127.0.0.1"

	for server in range(NumofReplicas):
		cmd = "kill $(lsof -t -i:{0}) && python3 ./client.py --id {1} --host {2} --port {3} --p {4} --timeout {5} &".format(_p, _id, _host, _port, _p, _timeout)
		print (os.system(cmd))
		_id += 1
		_port += 2

def main():
	create_replicas(NumofReplicas)
	print ('start creating clients...')
	create_clients(NumofClients)

main()