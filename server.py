import sys;
import config;
from message_type import MessageType;
from utils import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor;

class ServerDatagramProtocol(DatagramProtocol):
    def __init__(self, id, host, port, log):
        self.id = id;
        self.host = host;
        self.port = port;
        self.log = log;

    def startProtocol(self):
        #self.transport.connect(self.host, self.port);
        print("Server #%d initiated at %s %d" % (self.id, self.host,self.port));
    
    def datagramReceived(self, data, from_address):
        if data.decode() is not None:
            message_tokens = data.decode().split(' ');
            message_type = int(message_tokens[0]);
            
            if message_type == MessageType.CLIENT_PROPOSE.value:
                #<message_type, id, sequence, message>
                print("replica #%d received propose data %r from %s:%d" % (self.id, data.decode(), from_address[0], from_address[1]));
                self.transport.write("{0} {1}".format( MessageType.LEADER_ACK_PROPOSE.value, message_tokens[1]).encode(), (self.host, self.port));

def main():
    argv = process_argv(sys.argv);
    host = None;
    port = None;
    id = 0;
    log_filename = None;
    is_in_config = False;

    if "id" in argv and argv["id"].isdigit():
        if int(argv["id"]) in config.replicas:
            id = int(argv["id"]);
            is_in_config = True;
    else:
        print("Usage: python3 ./server.py --id <integer> --host <ip address, optional> --port <integer, optional> --log <string, optional>");
        return -1;
    
    if "host" in argv and is_valid_ip(argv["host"]):
        host = argv["host"];
    elif is_in_config:
        host = config.replicas[id][0];

    if "port" in argv and argv["port"].isdigit():
        port = int(argv["port"]);
    elif is_in_config:
        port = config.replicas[id][1];
    
    if "log" in argv:
        log_filename = argv["log"];
    elif is_in_config:
        log_filename = config.replicas[id][2];
    else:
        log_filename = "./logs/{0}.log".format(id);

    if not is_in_config and (host is None or port is None):
        print("Invalid id, could not found configure info");
        return -1;
    
    reactor.listenUDP(port, ServerDatagramProtocol(id, host, port, log_filename));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();