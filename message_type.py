from enum import Enum;

class MessageType(Enum):
    CLIENT_PROPOSE = 0
    ACK_PROPOSE = 1
    PREPARE = 2
    PROMISE = 3
    ACCEPT = 4
    ACCEPTED = 5
    NACK = 6
    DONE = 7
    LEADER_QUERY = 8
    LEADER_INFO = 9
    HEART_BEAT = 10

class MessageClass(Enum):
    CLIENT_MESSAGE = 0
    ACK_PROPOSE_MESSAGE = 1
    PREPARE_MESSAGE = 2
    PROMISE_MESSAGE = 3
    ACCEPT_MESSAGE = 4
    ACCEPTED_MESSAGE = 5 
    NACK_MESSAGE = 6
    DONE_MESSAGE = 7
    LEADER_QUERY_MESSAGE = 8
    LEADER_INFO_MESSAGE = 9
    HEART_BEAT_MESSAGE = 10

class ClientMessage:
    def __init__(self, client_id, client_sequence, message):
        self.client_id = client_id
        self.client_sequence = client_sequence
        self.message = message
        self.message_type = MessageType.CLIENT_PROPOSE.value
    
    def __str__(self):
        return "{0} {1} {2} {3}".format(
            self.message_type, self.client_id, self.client_sequence, self.message);

class AckProposeMessage:
    def __init__(self, sender_id, leader_id, current_slot, client_sequence, message):
        self.sender_id = sender_id;
        self.leader_id = leader_id;
        self.current_slot = current_slot;
        self.client_sequence = client_sequence
        self.message = message
        self.message_type = MessageType.ACK_PROPOSE.value
    
    def __str__(self):
        return "{0} {1} {2} {3} {4} {5}".format(
            self.message_type, self.sender_id, self.leader_id, self.current_slot, self.client_sequence, self.message);

class PrepareMessage:
    def __init__(self, proposer_id, proposal_id, slot):
        self.slot = slot;
        self.proposer_id = proposer_id; #replica_id
        self.proposal_id = proposal_id; #<highest_proposal_id_no, replica_id>
        self.message_type = MessageType.PREPARE.value;
    def __str__(self):
        return "{0} {1} {2} {3} {4}".format(
            self.message_type, self.proposer_id, self.proposal_id[0], self.proposal_id[1], self.slot);

class PromiseMessage:
    def __init__(self, acceptor_id, proposal_id, last_accepted_id, last_accepted_value, proposer_id, slot):
        self.acceptor_id = acceptor_id; #replica_id
        self.proposal_id = proposal_id; #<highest_proposal_id_no, replica_id>
        self.last_accepted_id = last_accepted_id; #<highest_proposal_id_no, replica_id>
        self.last_accepted_value = last_accepted_value; #value
        self.proposer_id = proposer_id; #replica_id
        self.slot = slot;
        self.message_type = MessageType.PROMISE.value;

    def __str__(self):
        (accepted_highest_proposal_id, accepted_replica_id) = (None, None) if self.last_accepted_id is None else self.last_accepted_id
        return "{0} {1} {2} {3} {4} {5} {6} {7} {8}".format(
            self.message_type, self.acceptor_id, self.proposal_id[0], self.proposal_id[1],
            accepted_highest_proposal_id, accepted_replica_id, self.last_accepted_value, 
            self.proposer_id, self.slot);

class AcceptMessage:
    def __init__(self, proposer_id, proposal_id, proposal_value, slot):
        self.proposer_id = proposer_id; #replica_id
        self.proposal_id = proposal_id; #<highest_proposal_id_no, replica_id>
        self.proposal_value = proposal_value; #<client_id, client_sequence, message>
        self.slot = slot;
        self.message_type = MessageType.ACCEPT.value;

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5} {6} {7}".format(
            self.message_type, self.proposer_id, self.proposal_id[0], self.proposal_id[1], self.proposal_value[0], self.proposal_value[1], self.proposal_value[2], self.slot);

class AcceptedMessage:
    def __init__(self, acceptor_id, proposal_id, accepted_value, proposer_id, slot):
        self.acceptor_id = acceptor_id; #replica_id
        self.proposal_id = proposal_id; #<highest_proposal_id_no, replica_id>
        self.accepted_value = accepted_value; #<client_id, client_sequence, message>
        self.proposer_id = proposer_id; #replica_id
        self.slot = slot;
        self.message_type = MessageType.ACCEPTED.value;

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5} {6} {7} {8}".format(
            self.message_type, self.acceptor_id, 
            self.proposal_id[0], self.proposal_id[1], 
            self.accepted_value[0], self.accepted_value[1], self.accepted_value[2],
            self.proposer_id, self.slot);

class NackMessage:
    def __init__(self, acceptor_id, promised_id, proposer_id, proposal_id, slot):
        self.acceptor_id = acceptor_id; #replica_id
        self.promised_id = promised_id; #<highest_proposal_id_no, replica_id>
        self.proposer_id = proposer_id; #replica_id
        self.proposal_id = proposal_id; #<highest_proposal_id_no, replica_id>
        self.slot = slot;
        self.message_type = MessageType.NACK.value;

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5} {6} {7}".format(
            self.message_type, self.acceptor_id, self.promised_id[0], self.promised_id[1], 
            self.proposer_id, self.proposal_id[0], self.proposal_id[1], self.slot);

class DoneMessage: 
    def __init__(self, client_sequence, message, leader_id) : 
        self.client_sequence = client_sequence;
        self.message = message;
        self.leader_id = leader_id;
        self.message_type = MessageType.DONE.value;
    
    def __str__(self):
        return "{0} {1} {2} {3}".format(self.message_type, self.client_sequence, self.message, self.leader_id);

class LeaderQueryMessage: 
    def __init__(self, asker_id, asker_sequence, old_leader_id, is_client=False) : 
        self.asker_id = asker_id;
        self.asker_sequence = asker_sequence;
        self.old_leader_id = old_leader_id;
        self.is_client = is_client;
        self.message_type = MessageType.LEADER_QUERY.value;
    
    def __str__(self):
        return "{0} {1} {2} {3} {4}".format(self.message_type, self.asker_id, self.asker_sequence, self.old_leader_id, self.is_client);

class LeaderInfoMessage: 
    def __init__(self, sender_id, leader_id, current_slot, asker_sequence) : 
        self.sender_id = sender_id;
        self.leader_id = leader_id;
        self.current_slot = current_slot;
        self.asker_sequence = asker_sequence;
        self.message_type = MessageType.LEADER_INFO.value;
    
    def __str__(self):
        return "{0} {1} {2} {3} {4}".format(self.message_type, self.sender_id, self.leader_id, self.current_slot, self.asker_sequence);

class HeartBeatMessage: 
    def __init__(self, id, heart_beat, leader, leader_is_alive, next_leader, slot, first_unchosen_slot, round) : 
        self.id = id;
        self.heart_beat = heart_beat;
        self.leader = leader;
        self.leader_is_alive = leader_is_alive;
        self.next_leader = next_leader;
        self.slot = slot;
        self.first_unchosen_slot = first_unchosen_slot;
        self.round = round;
        self.received_heart_beat = None;
        self.message_type = MessageType.HEART_BEAT.value;
    
    def __str__(self):
        return "{0} {1} {2} {3} {4} {5} {6} {7} {8}".format(
            self.message_type, self.id, self.heart_beat, 
            self.leader, self.leader_is_alive, self.next_leader,
            self.slot, self.first_unchosen_slot ,self.round);

class Resolution:
    def __init__(self, id, accepted_value, slot):
        self.id = id;
        self.accepted_value = accepted_value; #<client_id, client_sequence, message>
        self.slot = slot;

def parse_str_message(message, message_class):
    tokens = message.split(" ");
    #print(tokens)

    if message_class == MessageClass.CLIENT_MESSAGE.value and tokens is not None and len(tokens) == 4:
        #client_id, client_sequence, message
        return ClientMessage(int(tokens[1]), int(tokens[2]), tokens[3]);

    if message_class == MessageClass.ACK_PROPOSE_MESSAGE.value and tokens is not None and len(tokens) == 6:
        #sender_id, leader_id, current_slot, client_sequence, message
        return AckProposeMessage( int(tokens[1]), int(tokens[2]), int(tokens[3]), int(tokens[4]), tokens[5] ) ;
    
    elif message_class == MessageClass.PREPARE_MESSAGE.value and tokens is not None and len(tokens) == 5:
        return PrepareMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), int(tokens[4]));

    elif message_class == MessageClass.PROMISE_MESSAGE.value and tokens is not None and len(tokens) == 9:
        #acceptor_id, proposal_id, last_accepted_id, last_accepted_value, proposer_id, slot
        last_accepted_id = None if (tokens[4] == 'None' and tokens[5] == 'None') else (int(tokens[4]), int(tokens[5]))
        return PromiseMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), last_accepted_id, tokens[6], int(tokens[7]), int(tokens[8]));

    elif message_class == MessageClass.ACCEPT_MESSAGE.value and tokens is not None and len(tokens) == 8:
        #leader_id, proposal_id, proposed_value, slot
        return AcceptMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), (int(tokens[4]), int(tokens[5]), tokens[6]), int(tokens[7]));
    
    elif message_class == MessageClass.ACCEPTED_MESSAGE.value and tokens is not None and len(tokens) == 9:
        #acceptor_id, proposal_id, accepted_value, proposer_id, slot
        return AcceptedMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), (int(tokens[4]), int(tokens[5]), tokens[6]), int(tokens[7]), int(tokens[8]));
    
    elif message_class == MessageClass.DONE_MESSAGE.value and tokens is not None and len(tokens) == 4:
        #client_sequence, message, leader_id
        return DoneMessage( int(tokens[1]), tokens[2], int(tokens[3]) );

    elif message_class == MessageClass.LEADER_QUERY_MESSAGE.value and tokens is not None and len(tokens) == 5:
        #asker_id, asker_sequence, old_leader_id, is_client
        return LeaderQueryMessage( int(tokens[1]), int(tokens[2]), int(tokens[3]), tokens[4] == "True" );
    
    elif message_class == MessageClass.LEADER_INFO_MESSAGE.value and tokens is not None and len(tokens) == 5:
        #sender_id, leader_id, current_slot, asker_sequence
        return LeaderInfoMessage( int(tokens[1]), int(tokens[2]), int(tokens[3]), int(tokens[4]) );

    elif message_class == MessageClass.HEART_BEAT_MESSAGE.value and tokens is not None and len(tokens) == 9:
        #id, heart_beat, leader, leader_is_alive, next_leader, slot, first_unchosen_slot, round
        return HeartBeatMessage( int(tokens[1]), int(tokens[2]), int(tokens[3]), tokens[4] == "True", int(tokens[5]), int(tokens[6]), int(tokens[7]), int(tokens[8]) );