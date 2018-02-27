# paxos
---------------------------------------------
Dependency:
"twisted" is required. You can directly "pip install twisted".

---------------------------------------------
Manual Mode:
1) To create a new client, please use: 
"python3 ./client.py --id <integer> --host <ip address, optional> --port <integer, optional> --p <float, optional> --timeout <float, optional> --f <int, optional> --total_message <int, optional>"
'''
id: the identification of client;
-p: randomly drop p% of outgoing messages
-f: the maximum number of failures that can tolerate
-total_message: the number of messages this client will send
'''
For example: "python3 ./server.py --id 0 --host 127.0.0.1 --port 9200 --p 0 --timeout 0.5 &". 
Please note that do not use the same id.

2) Similarly, to create a server client, please use: 
Usage: python3 ./server.py --id <integer, required> " +\
            "--host <ip address, optional> --port <integer, optional> "+\
            "--log <string, optional> --p <float, optional> --timeout <float, optional> " +\
            "--f <integer, optional> --k <integer, optional> --print_heart_beat <true/false, optional>"

'''
-k: skipped slots
'''

For example: "python3 ./server.py --id 0 --host 127.0.0.1 --port 9100 --p 0 --timeout 0.5 &". 
Please note that do not use the same id

---------------------------------------------
Scrip Mode:
There are two ways to start this mode. 
1) Use the bash.
	There are two files in the folder,i.e., the "run_servers.sh" and "run_clients.sh". If you consider this way, you have to make sure that the "config.py" can match the bash file, especially the number of clients and servers. In the "config", each item in "replicas"/"clients" has similar format,
	e.g., {"0:("127.0.0.1", 9100, "./logs/replica_0.json", 0, 0.5)"} denotes {id, host_ip, host_port, log address, p, timeout}

2) Set the "script.py". 

To check the consistency of replicas' logs, you can refer to the "./logs/replica_{0}.json".format(id), where id is the replica id.