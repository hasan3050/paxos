import random;
import string;
import sys;
import os;
import json;
import config;
from message_type import *;
from utils import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor;

class ClientDatagramProtocol(DatagramProtocol):
    def __init__(self, id, host, port, replicas, log):
        self.id = id;
        self.host = host;
        self.port = port;
        self.log = log;
        self.history = self.get_init_history();
        self.replicas = replicas;
        self.leader = 0;
        self.sequence = 0;
        self.message = None;
        
    def get_init_history(self): 
        return {"sent":{},"accepted":{}, "last_sequence": 0, "last_leader": 0}

    def has_log_file(self):
        if not os.path.exists(self.log):
            with open(self.log, "w+") as log:
                json.dump( self.get_init_history() , log, indent=4);
        
        return True;

    def load_state(self):
        self.has_log_file();
        with open(self.log, "r") as log:
            try:
                history = json.load(log);
                self.history = history;
                self.sequence = int(self.history["last_sequence"]);
                self.leader = int(self.history["last_leader"]);
            except Exception:
                print("Failed to read log file. Initiating from the beginning");
                self.history = self.get_init_history();
        return
    
    def save_state(self):
        self.has_log_file();
        
        with open(self.log, "w+") as log:
            json.dump(self.history, log, indent=4);
        
        #print(self.history);
        return

    def update_history(self, type, sequence, message):
        if type == "sent" and str(sequence) not in self.history["sent"]:
            self.history["sent"][str(sequence)] = message;
        
        elif type == "accepted":
            if str(sequence) in self.history["sent"] :
                del self.history["sent"][str(sequence)];
            if str(sequence) not in self.history["accepted"] :
                self.history["accepted"][str(sequence)] = message;

        if sequence > int(self.history["last_sequence"]) :
            self.history["last_sequence"] = int(sequence);
        
        self.history["last_leader"] = self.leader;
        self.save_state();
        
    def generate_client_message(self, message = None, sequence = None, char_list = string.digits+string.ascii_letters, size = 1):
        if message is None:
            self.message = ''.join(random.choices(char_list, k=size));
        else:
            self.message = message;
        
        if sequence is None:
            self.sequence += 1;
        else:
            self.sequence = sequence;

        return ClientMessage(self.id, self.sequence, self.message);
    
    def startProtocol(self):
        #self.transport.connect(self.host, self.port);
        print("Client #%d initiated at %s %d" % (self.id, self.host,self.port));
        self.load_state();
        if len(self.history["sent"]):
            first_failed_sent = list(self.history["sent"].items())[0];
            client_message = self.generate_client_message(message = first_failed_sent[1], sequence = int(first_failed_sent[0]));
            self.send_client_message(client_message, self.leader)
        else:
            client_message = self.generate_client_message();
            self.send_client_message(client_message, self.leader)
    
    def datagramReceived(self, data, from_address):
        print("Client received %r from %s:%d" % (data.decode(), from_address[0], from_address[1]));
        if data.decode() is not None:
            message_tokens = data.decode().split(' ');
            message_type = int(message_tokens[0]);

            if message_type == MessageType.DONE.value:
                self.receive_done(data.decode(), from_address);
                
    def _send(self, message, to_id):
        to_address = (self.replicas[to_id][0], self.replicas[to_id][1]);
        self.transport.write( message.encode(), to_address);

    def send_client_message(self, client_message, replica_id):
        self._send(str(client_message), replica_id);
        self.update_history("sent", client_message.client_sequence, client_message.message);
    
    def broadcast_client_message(self, message_type):
        if message_type == MessageType.CLIENT_PROPOSE.value:
            client_message = self.generate_client_message();
        
        for replica_id in self.replicas:
            self.send_client_message(client_message, replica_id);

    def receive_done(self, message, from_address):
        done_message = parse_str_message(message, MessageClass.DONE_MESSAGE.value);
        self.update_history("accepted", done_message.client_sequence, done_message.message);

        if self.sequence < 5 :
            self.broadcast_client_message(MessageType.CLIENT_PROPOSE.value);


def main():
    argv = process_argv(sys.argv);
    host = None;
    port = None;
    id = 0;
    log_filename = '';
    is_in_config = False;

    if "id" in argv and argv["id"].isdigit():
        if int(argv["id"]) in config.clients:
            id = int(argv["id"]);
            is_in_config = True;
    else:
        print("Usage: python3 ./client.py --id <integer> --host <ip address, optional> --port <integer, optional>");
        return -1;
    
    if "host" in argv and is_valid_ip(argv["host"]):
        host = argv["host"];
    elif is_in_config:
        host = config.replicas[id][0];

    if "port" in argv and argv["port"].isdigit():
        port = int(argv["port"]);
    elif is_in_config:
        port = config.clients[id][1];
    
    if "log" in argv:
        log = argv["log"];
    elif is_in_config:
        log = config.clients[id][2];
    else:
        log = "./logs/client_{0}.json".format(id);

    if not is_in_config and (host is None or port is None):
        print("Invalid id, could not found configure info");
        return -1;

    reactor.listenUDP(port, ClientDatagramProtocol(id, host, port, config.replicas, log));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();