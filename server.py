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
        self.leader = 0;
        self.paxos = PaxosInstance(self.id, int(len(self.replicas)/2)+1, is_leader=(self.id ==0));
        self.slot = 0;
        self.message_pool = []; #(ClientMessage)

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

            elif message_type == MessageType.ACCEPT.value:
                self.receive_accept(data.decode(), from_address);

            elif message_type == MessageType.ACCEPTED.value:
                self.receive_accepted(data.decode(), from_address);

            elif message_type == MessageType.NACK.value:
                self.receive_nack(data.decode(), from_address);
            
            elif message_type == MessageType.LEADER_QUERY.value:
                self.receive_leader_query(data.decode(), from_address);

    def save_state(self):
        #TO DO: save state to the log file 
        return

    def advance_slot(self, new_slot, new_value):
        print("replica #{0} has accepted {1} at slot#{2}".format(self.id, new_value, new_slot));
        self.save_state();
        _is_leader = self.paxos.leader;
        self.paxos = PaxosInstance(self.id, int(len(self.replicas)/2)+1, is_leader= _is_leader);
        self.slot = new_slot;
        self.send_done();
        return

    def _send(self, message, to_id, is_client=False):
        if is_client == False:
            (host,port) = (self.replicas[to_id][0],self.replicas[to_id][1]) 
        if is_client == True:
            (host, port) = (config.clients[to_id][0],config.clients[to_id][1])
        self.transport.write(message.encode(), (host,port) );
    
    def receive_propose(self, message, from_address):
        
        #<message_type, client_id, sequence, message, replica_id>
        client_message = parse_str_message(message, MessageClass.CLIENT_MESSAGE.value);
        self.send_ack_propose(client_message);    
        
        if self.leader == self.id:
            self.message_pool.append(client_message)
            print("replica #%d received propose message %r from %s:%d" % (self.id, message, from_address[0], from_address[1]));
            
            if self.paxos.proposed_value is None:
                self.paxos.propose_value(client_message.message, self.slot);
            (replica_id, proposal_id) = self.paxos.prepare();
            prepare_message = PrepareMessage(replica_id, proposal_id, self.slot); 
            self.send_prepare(prepare_message);

    def send_ack_propose(self, client_message):
        ack_propose_message = AckProposeMessage(self.id, self.leader, self.slot, client_message.client_sequence, client_message.message);
        self._send(str(ack_propose_message), client_message.client_id, is_client=True);
            
    def send_prepare(self, prepare_message):
        for replica_id in self.replicas:
            self._send(str(prepare_message), replica_id);
    
    def receive_prepare(self, message, from_address):
        #print("replica #%d received prepare message %r" % (self.id, message));
        prepare_message = parse_str_message(message, MessageClass.PREPARE_MESSAGE.value);
        if prepare_message.slot != self.slot:
            return
        
        m = self.paxos.receive_prepare(prepare_message)
        
        if isinstance(m, PromiseMessage):
            self.save_state();
            #self.save_state(self.slot, self.current_value, m.proposal_id,
            #                m.last_accepted_id, m.last_accepted_value)
            
            self.send_promise(m);
        elif isinstance(m, NackMessage):
            self.send_nack(m);

    def send_promise(self, promise_message):
        self._send(str(promise_message), promise_message.proposer_id)

    def receive_promise(self, message, from_address):
        #print("replica #%d received promise message %r" % (self.id, message));
        
        promise_message = parse_str_message(message, MessageClass.PROMISE_MESSAGE.value)
        
        if promise_message.slot != self.slot:
            return

        m = self.paxos.receive_promise(promise_message)
        
        if isinstance(m, AcceptMessage):
            self.send_accept(m)

    def send_nack(self, nack_message):
        self._send(str(nack_message), nack_message.proposer_id)
    
    def receive_nack(self, message, from_address):
        # print("replica #%d received nack message %r" % (self.id, message));
        # TO DO: need to implement receive nack logic
        return

    def send_accept(self, accept_message):
        for replica_id in self.replicas:
            self._send( str(accept_message), replica_id);
    
    def receive_accept(self, message, from_address):
        #print("replica #%d received accept message %r" % (self.id, message));

        accept_message = parse_str_message(message, MessageClass.ACCEPT_MESSAGE.value);
        
        if accept_message.slot != self.slot:
            return
        
        m = self.paxos.receive_accept(accept_message)
        
        if isinstance(m, AcceptedMessage):
            self.save_state();
            # self.save_state(self.instance_number, self.current_value, self.promised_id,
            #                 proposal_id, proposal_value)
            self.send_accepted(m);
        elif isinstance(m, NackMessage):
            self.send_nack(m);

    def send_accepted(self, accepted_message):
        for replica_id in self.replicas:
            self._send( str(accepted_message), replica_id); 

    def receive_accepted(self, message, from_address):
        #print("replica #%d received accepted message %r" % (self.id, message));
        
        accepted_message = parse_str_message(message, MessageClass.ACCEPTED_MESSAGE.value);

        if accepted_message.slot != self.slot:
            return

        m = self.paxos.receive_accepted(accepted_message)
        
        if isinstance(m, Resolution):
            self.advance_slot( self.slot + 1, m.accepted_value )

    def send_done(self):
        if len(self.message_pool) > 0:
            client_message = self.message_pool.pop(0);
            done_message = DoneMessage(client_message.client_sequence, client_message.message, self.id);
            self._send( str(done_message), client_message.client_id, is_client=True)
    
    def receive_leader_query(self, message, from_address):
        leader_query = parse_str_message(message, MessageClass.LEADER_QUERY_MESSAGE.value);
        self.send_leader_info(leader_query.asker_id, leader_query.asker_sequence, leader_query.is_client);
    
    def send_leader_info(self, asker_id, asker_sequence, is_client = False):
        leader_info = LeaderInfoMessage(self.id, self.leader, self.slot, asker_sequence);
        self._send(str(leader_info), asker_id, is_client);
        

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
        log_filename = "./logs/replica_{0}.json".format(id);

    if not is_in_config and (host is None or port is None):
        print("Invalid id, could not found configure info");
        return -1;
    
    reactor.listenUDP(port, ServerDatagramProtocol(id, host, port, log_filename, config.replicas));

reactor.callWhenRunning(main)
reactor.run();

if __name__ == "__main__":
    main();