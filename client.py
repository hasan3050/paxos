import random;
import string;
import sys;
import os;
import json;
import config;
from message_type import *;
from utils import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, task;

class ClientDatagramProtocol(DatagramProtocol):
    def __init__(self, id, host, port, replicas, log, p = 0, timeout = 0.5, f=1, total_message = 100):
        self.id = id;
        self.host = host;
        self.port = port;
        self.log = log;
        self.history = self.get_init_history();
        self.replicas = replicas;
        self.quorum_size = 2*f+1;#int(len(self.replicas)/2)+1;
        self.leader = 0;
        self.sequence = 0;
        self.message = None;
        self.leader_ask_sequence = 0;
        self.leader_ask_response = {};
        self.p = p;
        self.total_message = total_message;
        self.client_message_watch = None
        self.leader_ask_watch = None
        self.client_message_timeout = timeout #in second
        self.leader_ask_timeout = timeout #in second
        
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
        if len(self.history["sent"]) > 0:
            self.send_unresolved_client_message();
        else:
            client_message = self.generate_client_message();
            self.send_client_message(client_message, self.leader)
        # self.broadcast_leader_query_message();
    
    def datagramReceived(self, data, from_address):
        #print("Client received %r from %s:%d" % (data.decode(), from_address[0], from_address[1]));
        if data.decode() is not None:
            message_tokens = data.decode().split(' ');
            message_type = int(message_tokens[0]);

            if message_type == MessageType.ACK_PROPOSE.value:
                self.receive_ack_propose(data.decode(), from_address);

            if message_type == MessageType.DONE.value:
                self.receive_done(data.decode(), from_address);
                print("Client #%d has received done message %r from %s:%d" % ( self.id, data.decode(), from_address[0], from_address[1]));

            if message_type == MessageType.LEADER_INFO.value:
                self.receive_leader_info(data.decode(), from_address);
                
    def _send(self, message, to_id):
        random_number = random.random();
        if self.p < random_number:
            to_address = (self.replicas[to_id][0], self.replicas[to_id][1]);
            #print("sending this message {0} to {1}:{2}".format(message, to_address[0], to_address[1]))
            self.transport.write( message.encode(), to_address);
    
    def broadcast_leader_query_message(self):
        self.stop_client_message_watch();
        self.stop_leader_ask_watch();

        self.leader_ask_sequence += 1;
        self.leader_ask_response = {};
        leader_query_message = LeaderQueryMessage(self.id, self.leader_ask_sequence, self.leader, True);
        for replica_id in self.replicas:
            self._send(str(leader_query_message), replica_id);
        
        self.start_leader_ask_watch();

    def receive_leader_info(self, message, from_address):
        leader_info = parse_str_message(message, MessageClass.LEADER_INFO_MESSAGE.value);
        if leader_info.asker_sequence < self.leader_ask_sequence:
            return;
        
        if int(leader_info.leader_id) not in self.leader_ask_response:
            self.leader_ask_response[int(leader_info.leader_id)] = 1;
        else:
            self.leader_ask_response[int(leader_info.leader_id)] += 1;

        if self.leader_ask_response[int(leader_info.leader_id)] == self.quorum_size: 
            self.leader = int(leader_info.leader_id);
            self.leader_ask_sequence += 1;
            self.leader_ask_response = {};
            self.stop_leader_ask_watch();
            self.send_unresolved_client_message();
        return;

    def send_client_message(self, client_message, replica_id):
        #print("current leader is {0}".format(self.leader));
        self.stop_client_message_watch();
        self._send(str(client_message), replica_id);
        self.update_history("sent", client_message.client_sequence, client_message.message);
        self.start_client_message_watch();
    
    def send_unresolved_client_message(self):
        if len(self.history["sent"]) > 0:
            first_failed_sent = list(self.history["sent"].items())[0];
            client_message = self.generate_client_message(message = first_failed_sent[1], sequence = int(first_failed_sent[0]));
            self.send_client_message(client_message, self.leader);

    def start_client_message_watch(self):
        self.stop_client_message_watch();
        self.client_message_watch = reactor.callLater(self.client_message_timeout, self.resolve_client_message_timeout);

    def stop_client_message_watch(self):
        if self.client_message_watch is not None and self.client_message_watch.active():
            self.client_message_watch.cancel();
            self.client_message_watch = None;

    def start_leader_ask_watch(self):
        self.stop_leader_ask_watch();
        self.leader_ask_watch = reactor.callLater(self.leader_ask_timeout, self.resolve_leader_ask_timeout);

    def stop_leader_ask_watch(self):
        if self.leader_ask_watch is not None and self.leader_ask_watch.active():
            self.leader_ask_watch.cancel();
            self.leader_ask_watch = None;

    def resolve_client_message_timeout(self):
        self.stop_leader_ask_watch();
        self.stop_client_message_watch();
        self.broadcast_leader_query_message();

    def resolve_leader_ask_timeout(self):
        self.stop_leader_ask_watch();
        self.stop_client_message_watch();
        self.broadcast_leader_query_message();
    # def broadcast_client_message(self):
    #     client_message = self.generate_client_message();
        
    #     for replica_id in self.replicas:
    #         self.send_client_message(client_message, replica_id);

    def receive_ack_propose(self, message, from_address):
        #print("Client #{0} got ack for propose for {1} from {2}".format(self.id, message, from_address[1]))
        ack_propose = parse_str_message(message, MessageClass.ACK_PROPOSE_MESSAGE.value);
        if ack_propose.client_sequence >= self.sequence and ack_propose.sender_id != ack_propose.leader_id:
            self.leader = int(ack_propose.leader_id);
            client_message = self.generate_client_message(self.message, self.sequence);
            self.send_client_message(client_message, self.leader);

    def receive_done(self, message, from_address):
        done_message = parse_str_message(message, MessageClass.DONE_MESSAGE.value);
        self.update_history("accepted", done_message.client_sequence, done_message.message);

        if self.sequence < self.total_message :
            client_message = self.generate_client_message();
            self.send_client_message(client_message, self.leader);


def main():
    argv = process_argv(sys.argv);
    host = None;
    port = None;
    id = 0;
    log_filename = '';
    is_in_config = False;
    p = 0;
    f = 1;
    timeout = 0.5;
    total_message = 100;

    if "id" in argv and argv["id"].isdigit():
        if int(argv["id"]) in config.clients:
            id = int(argv["id"]);
            is_in_config = True;
    else:
        print("Usage: python3 ./client.py --id <integer> --host <ip address, optional> --port <integer, optional> --p <float, optional> --timeout <float, optional> --f <int, optional> --total_message <int, optional>" );
        return -1;
    
    if "host" in argv and is_valid_ip(argv["host"]):
        host = argv["host"];
    elif is_in_config:
        host = config.replicas[id][0];

    if "port" in argv and argv["port"].isdigit():
        port = int(argv["port"]);
    elif is_in_config:
        port = config.clients[id][1];

    if "p" in argv and is_number(argv["p"]):
        p = float(argv["p"]);
    elif is_in_config:
        p = float(config.clients[id][3]);

    if "timeout" in argv and is_number(argv["timeout"]):
        timeout = float(argv["timeout"]);
    elif is_in_config:
        timeout = float(config.clients[id][4]);
    
    if "log" in argv:
        log = argv["log"];
    elif is_in_config:
        log = config.clients[id][2];
    else:
        log = "./logs/client_{0}.json".format(id);

    if "f" in argv and is_number(argv["f"]):
        f = int(argv["f"]);
    elif is_in_config:
        f = int(config.f);

    if "total_message" in argv and is_number(argv["total_message"]):
        total_message = int(argv["total_message"]);
    elif is_in_config:
        total_message = int(config.total_message);

    if not is_in_config and (host is None or port is None):
        print("Invalid id, could not found configure info");
        return -1;

    reactor.listenUDP(port, ClientDatagramProtocol(id, host, port, config.replicas, log, p, timeout, f, total_message));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();