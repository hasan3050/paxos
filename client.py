import random;
import string;
import sys;
import config;
from message_type import MessageType;
from utils import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor;

class ClientDatagramProtocol(DatagramProtocol):
    def __init__(self, id, host, port, replica_list):
        self.id = id;
        self.host = host;
        self.port = port;
        self.replica_list = [];
        self.leader = 0;
        self.sequence = 0;

        for rep_id in replica_list:
            replica = replica_list[rep_id];
            self.replica_list.append({"id": rep_id, "host": replica[0], "port": replica[1]});

        self.message = None;

    def generate_message(self, char_list = string.digits+string.ascii_letters, size = 1):
        self.message = ''.join(random.choices(char_list, k=size));
        self.sequence = self.sequence + 1;
    
    def format_message(self, message_type):
        formatted_message = '';
        if message_type == MessageType.CLIENT_PROPOSE.value:
            #<message_type, client_id, sequence, message>
            formatted_message = "{0} {1} {2} {3}".format(message_type, self.id, self.sequence, self.message);
        else:
            #<message_type, client_id, sequence>
            formatted_message = "{0} {1} {2}".format(message_type, self.id, self.sequence);
            
        #print(formatted_message);
        return formatted_message;

    def startProtocol(self):
        #self.transport.connect(self.host, self.port);
        # print("Client has connected to the host %s %d" % (self.host,self.port));
        print("Client #%d initiated at %s %d" % (self.id, self.host,self.port));
        self.broadcast_message(MessageType.CLIENT_PROPOSE.value);
    
    def datagramReceived(self, data, from_address):
        print("received %r from %s:%d" % (data.decode(), from_address[0], from_address[1]));

    def send_message(self, message_type, to_address):
        if self.message is None:
            self.generate_message();
        self.transport.write( self.format_message(message_type).encode(), to_address);
    
    def broadcast_message(self, message_type):
        for replica in self.replica_list:
            self.send_message(message_type, (replica["host"],replica["port"]));

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

    if not is_in_config and (host is None or port is None):
        print("Invalid id, could not found configure info");
        return -1;

    reactor.listenUDP(port, ClientDatagramProtocol(id, host, port, config.replicas));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();