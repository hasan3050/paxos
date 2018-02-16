import sys;
from utils import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor;

class ServerDatagramProtocol(DatagramProtocol):
    def __init__(self, host, port):
        self.host = host;
        self.port = port;

    def startProtocol(self):
        self.transport.connect(self.host, self.port);
        print("Server has connected to the host %s %d" % (self.host,self.port));
    
    def datagramReceived(self, data, from_address):
        print("received %r from %s:%d" % (data.decode(), from_address[0], from_address[1]));

def main():
    argv = process_argv(sys.argv);
    host = "127.0.0.1"
    port = 9200;

    if "port" in argv and argv["port"].isdigit():
        port = int(argv["port"]);
    if "host" in argv and is_valid_ip(argv["host"]):
        host = argv["host"];
        
    reactor.listenUDP(port, ServerDatagramProtocol(host,9100));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();