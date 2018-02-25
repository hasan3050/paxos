from enum import Enum;

class MessageType(Enum):
    CLIENT_PROPOSE = 0
    LEADER_ACK_PROPOSE = 1
    PREPARE = 2
    PROMISE = 3
    ACCEPT = 4
    ACCEPTED = 5
    NACK = 6
    DONE = 7

class MessageClass(Enum):
    CLIENT_MESSAGE = 0
    PREPARE_MESSAGE = 1
    PROMISE_MESSAGE = 2
    ACCEPT_MESSAGE = 3
    ACCEPTED_MESSAGE = 4 
    NACK_MESSAGE = 5
    DONE_MESSAGE = 6

class ClientMessage:
    def __init__(self, client_id, client_sequence, message):
        self.client_id = client_id
        self.client_sequence = client_sequence
        self.message = message
        self.message_type = MessageType.CLIENT_PROPOSE.value
    
    def __str__(self):
        return "{0} {1} {2} {3}".format(
            self.message_type, self.client_id, self.client_sequence, self.message);

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
        self.proposal_value = proposal_value;
        self.slot = slot;
        self.message_type = MessageType.ACCEPT.value;

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5}".format(
            self.message_type, self.proposer_id, self.proposal_id[0], self.proposal_id[1], self.proposal_value, self.slot);

class AcceptedMessage:
    def __init__(self, acceptor_id, proposal_id, accepted_value, proposer_id, slot):
        self.acceptor_id = acceptor_id; #replica_id
        self.proposal_id = proposal_id; #<highest_proposal_id_no, replica_id>
        self.accepted_value = accepted_value;
        self.proposer_id = proposer_id; #replica_id
        
        self.slot = slot;
        self.message_type = MessageType.ACCEPTED.value;

    def __str__(self):
        return "{0} {1} {2} {3} {4} {5} {6}".format(
            self.message_type, self.acceptor_id, 
            self.proposal_id[0], self.proposal_id[1], self.accepted_value, 
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

class Resolution:
    def __init__(self, id, accepted_value, slot):
        self.id = id;
        self.accepted_value = accepted_value;
        self.slot = slot;

def parse_str_message(message, message_class):
    tokens = message.split(" ");
    #print(tokens)

    if message_class == MessageClass.CLIENT_MESSAGE.value and tokens is not None and len(tokens) == 4:
        #client_id, client_sequence, message
        return ClientMessage(int(tokens[1]), int(tokens[2]), tokens[3]);
    
    elif message_class == MessageClass.PREPARE_MESSAGE.value and tokens is not None and len(tokens) == 5:
        return PrepareMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), int(tokens[4]));

    elif message_class == MessageClass.PROMISE_MESSAGE.value and tokens is not None and len(tokens) == 9:
        #acceptor_id, proposal_id, last_accepted_id, last_accepted_value, proposer_id, slot
        last_accepted_id = None if (tokens[4] == 'None' and tokens[5] == 'None') else (int(tokens[4]), int(tokens[5]))
        return PromiseMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), last_accepted_id, tokens[6], int(tokens[7]), int(tokens[8]));

    elif message_class == MessageClass.ACCEPT_MESSAGE.value and tokens is not None and len(tokens) == 6:
        #leader_id, proposal_id, proposed_value, slot
        return AcceptMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), tokens[4], int(tokens[5]));
    
    elif message_class == MessageClass.ACCEPTED_MESSAGE.value and tokens is not None and len(tokens) == 7:
        #acceptor_id, proposal_id, accepted_value, proposer_id, slot
        return AcceptedMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), tokens[4], int(tokens[5]), int(tokens[6]));
    
    elif message_class == MessageClass.DONE_MESSAGE.value and tokens is not None and len(tokens) == 4:
        #client_sequence, message, leader_id
        return DoneMessage( int(tokens[1]), (tokens[2]), int(tokens[3]) );