import sys;
import os;
import json;
import config;
from message_type import MessageType;
from utils import *;
from paxos_instance import *;
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor;

#To Do: verify whether the message.slot != self.slot can cause trouble

class MessagePoolState(Enum):
    NEW = 0
    PROPOSED = 1

class ServerDatagramProtocol(DatagramProtocol):
    def __init__(self, id, host, port, log, replicas):
        self.id = id;
        self.host = host;
        self.port = port;
        self.log = log;
        self.replicas = replicas;
        self.history = self.get_init_history();
        self.heart_beat = 0;
        self.leader = 0;
        self.paxos = PaxosInstance(self.id, int(len(self.replicas)/2)+1, is_leader=(self.id == self.leader));
        self.slot = 0;
        self.first_unchosen_slot = 0;
        self.message_pool = {}; #{slot : (client_message, new/sent)}

    def get_init_history(self): 
        return {
            "accepted":{}, #{client_id : {client_sequence: (message, slot)}}
            "states": {}, # {slot:value}
            "last_leader": 0, 
            "highest_proposal_id": None, #(highest_proposal_id_no, replica_id) 
            "last_promised_id" : None, #(highest_proposal_id_no, replica_id)
            "last_accepted_id" : None, #(highest_proposal_id_no, replica_id)
            "last_accepted_message" : None #(client_id, sequence, value)
            }

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
                self.leader = int(self.history["last_leader"]);
                (self.first_unchosen_slot, self.slot) = self.get_slot_from_history(history["states"]);
                #TO DO: Update paxos variables
            except Exception:
                print("Failed to read log file. Initiating from the beginning");
                self.history = self.get_init_history();

    def startProtocol(self):
        print("Server #%d initiated at %s %d" % (self.id, self.host,self.port));
        self.load_state();
        #print(self.id, self.slot, self.first_unchosen_slot, self.leader);
    
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
        self.has_log_file();
        
        with open(self.log, "w+") as log:
            json.dump(self.history, log, indent=4);
        
        #print(self.history);

    def advance_slot(self, prev_slot, client_message):
        print("replica #{0} has accepted {1} at slot#{2}".format(self.id, client_message.message, prev_slot));
        self.add_to_history_accepted(client_message, prev_slot);
        self.remove_from_message_pool(prev_slot);
        self.slot = prev_slot + 1;
        _is_leader = self.paxos.leader;
        self.paxos = PaxosInstance(self.id, int(len(self.replicas)/2)+1, is_leader= _is_leader);
        if _is_leader:
            self.send_done(client_message);
            self.propose_next_message();
        
    def get_slot_from_history(self, _states = None):
        states = _states; #{slot:value}
        if states is None and self.history["states"] is not None:
            states = self.history["states"];

        state_items = list(states.items());
        state_items = sorted(state_items, key = lambda st_item: int(st_item[0]));
        state_item_size = len(state_items);
        last_item = state_items[ state_item_size - 1] if state_item_size > 0 else None;
        next_slot = (int(last_item[0]) + 1) if last_item is not None else 0;
        unchosen_slot = 0;

        for i in range(0, next_slot+1):
            if str(i) not in states:
                unchosen_slot = i;
                break;
        return (unchosen_slot, next_slot);

    def add_to_message_pool(self, client_message):
        if self.message_pool is None:
            self. message_pool = {};
        if self.slot not in self.message_pool:
            self.message_pool[self.slot] = (client_message, MessagePoolState.NEW.value);
            self.slot += 1; 
    
    def remove_from_message_pool(self, slot):
        if self.message_pool is None or slot not in self.message_pool:
            return;
        else:
            del self.message_pool[slot];
            return;
    
    def get_first_message_from_pool(self):
        if self.message_pool is None or len(self.message_pool) <= 0:
            return None;
        else:
            first_item = list(self.message_pool.items())[0]; #(slot, (client_message, state))
            return first_item;
    
    def add_to_history_accepted(self, client_message, slot):
        if str(client_message.client_id) not in self.history["accepted"]:
            self.history["accepted"][str(client_message.client_id)] = {};
        if str(client_message.client_sequence) not in self.history["accepted"][str(client_message.client_id)]:
            self.history["accepted"][str(client_message.client_id)][str(client_message.client_sequence)] = (client_message.message, str(slot));
        if str(slot) not in self.history["states"]:
            self.history["states"][str(slot)] = client_message.message; 
        self.save_state();
    
    def check_new_client_message(self, client_message):
        if str(client_message.client_id) in self.history["accepted"]:
            if str(client_message.client_sequence) in self.history["accepted"][str(client_message.client_id)]:
                return False;
        
        return True;

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
        
        if self.paxos.leader:
            if self.check_new_client_message(client_message):
                self.add_to_message_pool(client_message);
                print("replica #%d received propose message %r from %s:%d" % (self.id, message, from_address[0], from_address[1]));
                #To do: seperate this from here, poll when the message_pool is ready
                self.propose_next_message();
            else:
                self.send_done(client_message);

    def propose_next_message(self):
        next_message = self.get_first_message_from_pool(); #<slot, (client_message, state)>
        if next_message is None:
            return;
        if self.check_new_client_message(next_message[1][0]) == True:
            if next_message[1][1] == MessagePoolState.PROPOSED.value:
                return;
            if self.paxos.proposed_value is None:
                self.paxos.propose_value(next_message[1][0], next_message[0]);
                #print("in proposed value of the proposer {0}".format(self.paxos.proposed_value));
                self.message_pool[next_message[0]] = (next_message[1][0], MessagePoolState.PROPOSED.value);
            
            #To Do: avoid the prepare state, direct propose
            (replica_id, proposal_id) = self.paxos.prepare();
            prepare_message = PrepareMessage(replica_id, proposal_id, next_message[0]); 
            self.send_prepare(prepare_message);
        else:
            self.remove_from_message_pool(next_message[0]);
            self.propose_next_message();

    def send_ack_propose(self, client_message):
        ack_propose_message = AckProposeMessage(self.id, self.leader, self.slot, client_message.client_sequence, client_message.message);
        self._send(str(ack_propose_message), client_message.client_id, is_client=True);
            
    def send_prepare(self, prepare_message):
        for replica_id in self.replicas:
            self._send(str(prepare_message), replica_id);
    
    def receive_prepare(self, message, from_address):
        #print("replica #%d received prepare message %r" % (self.id, message));
        prepare_message = parse_str_message(message, MessageClass.PREPARE_MESSAGE.value);
        # if prepare_message.slot != self.slot:
        #     print("slot mismatch")
        #     return
        
        m = self.paxos.receive_prepare(prepare_message)
        
        if isinstance(m, PromiseMessage):
            self.save_state();
            #self.save_state(self.slot, self.current_value, m.proposal_id,
            #                m.last_accepted_id, m.last_accepted_value)
            
            self.send_promise(m);
        elif isinstance(m, NackMessage):
            self.send_nack(m);

    def send_promise(self, promise_message):
        #print("replica #%d sent promise message %s" % (self.id, str(promise_message)));
        self._send(str(promise_message), promise_message.proposer_id)

    def receive_promise(self, message, from_address):
        #print("replica #%d received promise message %r" % (self.id, message));
        promise_message = parse_str_message(message, MessageClass.PROMISE_MESSAGE.value)
        
        # if promise_message.slot != self.slot:
        #     return

        m = self.paxos.receive_promise(promise_message)
        
        if isinstance(m, AcceptMessage):
            self.send_accept(m)

    def send_nack(self, nack_message):
        self._send(str(nack_message), nack_message.proposer_id)
    
    def receive_nack(self, message, from_address):
        # print("replica #%d received nack message %r" % (self.id, message));
        #To Do: need to implement receive nack logic
        return

    def send_accept(self, accept_message):
        #print("replica #%d sent accept message %s" % (self.id, str(accept_message)));
        for replica_id in self.replicas:
            self._send( str(accept_message), replica_id);
    
    def receive_accept(self, message, from_address):
        #print("replica #%d received accept message %r" % (self.id, message));

        accept_message = parse_str_message(message, MessageClass.ACCEPT_MESSAGE.value);
        
        # if accept_message.slot != self.slot:
        #     return
        
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

        # if accepted_message.slot != self.slot:
        #     return

        m = self.paxos.receive_accepted(accepted_message)
        
        if isinstance(m, Resolution):
            self.advance_slot( m.slot, ClientMessage(m.accepted_value[0], m.accepted_value[1], m.accepted_value[2]) )

    def send_done(self, client_message = None):
        if client_message is None and len(self.message_pool) > 0:
            client_message = self.message_pool.pop(0);
        
        if client_message is not None:
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