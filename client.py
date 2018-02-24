import random;
import string;
import sys;
import config;
from message_type import *;
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

    def generate_client_message(self, char_list = string.digits+string.ascii_letters, size = 1):
        self.message = ''.join(random.choices(char_list, k=size));
        self.sequence += 1;

        return ClientMessage(self.id, self.sequence, self.message);
    
    def startProtocol(self):
        #self.transport.connect(self.host, self.port);
        print("Client #%d initiated at %s %d" % (self.id, self.host,self.port));
        self.broadcast_message(MessageType.CLIENT_PROPOSE.value);
    
    def datagramReceived(self, data, from_address):
        print("Client received %r from %s:%d" % (data.decode(), from_address[0], from_address[1]));
        if data.decode() is not None:
            message_tokens = data.decode().split(' ');
            message_type = int(message_tokens[0]);

            if message_type == MessageType.DONE.value and self.sequence < 5:
                self.broadcast_message(MessageType.CLIENT_PROPOSE.value);

    def send_message(self, client_message, replica):
        to_address = (replica["host"], replica["port"])
        self.transport.write( str(client_message).encode(), to_address);
    
    def broadcast_message(self, message_type):
        if message_type == MessageType.CLIENT_PROPOSE.value:
            client_message = self.generate_client_message();
        
        for replica in self.replica_list:
            self.send_message(str(client_message), replica);

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