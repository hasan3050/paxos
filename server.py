import sys;
import config;
from message_type import MessageType;
from utils import *;
from paxos_instance import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor;

class ServerDatagramProtocol(DatagramProtocol):
    def __init__(self, id, host, port, log, replicas):
        self.id = id;
        self.host = host;
        self.port = port;
        self.log = log;
        self.replicas = replicas;
        self.paxos = PaxosInstance(self.id, len(self.replicas)/2+1, is_leader=(self.id ==0));
        self.slot = 0;

    def startProtocol(self):
        #self.transport.connect(self.host, self.port);
        print("Server #%d initiated at %s %d" % (self.id, self.host,self.port));
    
    def datagramReceived(self, data, from_address):
        if data.decode() is not None:
            message_tokens = data.decode().split(' ');
            message_type = int(message_tokens[0]);
            
            if message_type == MessageType.CLIENT_PROPOSE.value:
                self.receive_propose(data.decode(), from_address)
            
            elif message_type == MessageType.PREPARE.value:
                self.receive_prepare(data.decode(), from_address);
            
            elif message_type == MessageType.PROMISE.value:
                self.receive_promise(data.decode(), from_address);

            elif message_type == MessageType.NACK.value:
                self.receive_nack(data.decode(), from_address);
                
    def _send(self, message, to_id):
        self.transport.write(message.encode(), (self.replicas[to_id][0],self.replicas[to_id][1]) );
    
    def receive_propose(self, message, from_address):
        if self.paxos.leader:
            #<message_type, client_id, sequence, message, replica_id>
            client_message = parse_str_message(message, MessageClass.CLIENT_MESSAGE.value);
            print("replica #%d received propose message %r from %s:%d" % (self.id, message, from_address[0], from_address[1]));
            #self.transport.write("{0} {1}".format( MessageType.LEADER_ACK_PROPOSE.value, message_tokens[1]).encode(), (self.host, self.port));
            
            (replica_id, proposal_id) = self.paxos.prepare();
            prepare_message = PrepareMessage(replica_id, proposal_id, self.slot); 
            self.send_prepare(prepare_message);

    def send_prepare(self, prepare_message):
        for replica_id in self.replicas:
            self._send(str(prepare_message), replica_id);
    
    def receive_prepare(self, message, from_address):
        print("replica #%d received prepare message %r" % (self.id, message));
        prepare_message = parse_str_message(message, MessageClass.PREPARE_MESSAGE.value);
        if prepare_message.slot != self.slot:
            return
        
        m = self.paxos.receive_prepare(prepare_message)
        
        if isinstance(m, PromiseMessage):
            #self.save_state(self.slot, self.current_value, m.proposal_id,
            #                m.last_accepted_id, m.last_accepted_value)
            
            self.send_promise(m);
        else:
            self.send_nack(from_uid, self.slot, proposal_id, self.promised_id)

    def send_promise(self, promise_message):
        self._send(str(promise_message), promise_message.proposer_id)

    def receive_promise(self, message, from_address):
        print("replica #%d received promise message %r" % (self.id, message));
        # TO DO: need to implement receive promise logic

    def send_nack(self, nack_message, from_address):
        self._send(str(nack_message), nack_message.proposer_id)
    
    def receive_nack(self, message):
        print("replica #%d received nack message %r" % (self.id, message));
        # TO DO: need to implement receive nack logic

    def save_state(self):
        #TO DO: save state to the log file 
        return

    # def send_accept(self, peer_uid, instance_number, proposal_id, proposal_value):
    #     self._send(peer_uid, 'accept', instance_number = instance_number,
    #                                    proposal_id     = proposal_id,
    #                                    proposal_value  = proposal_value)

    # def send_accepted(self, peer_uid, instance_number, proposal_id, proposal_value):
    #     self._send(peer_uid, 'accepted', instance_number = instance_number,
    #                                      proposal_id     = proposal_id,
    #                                      proposal_value  = proposal_value)

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
    
    reactor.listenUDP(port, ServerDatagramProtocol(id, host, port, log_filename, config.replicas));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();