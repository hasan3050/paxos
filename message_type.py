from enum import Enum;

class MessageType(Enum):
    CLIENT_PROPOSE = 0
    LEADER_ACK_PROPOSE = 1
    PREPARE = 2
    PROMISE = 3
    ACCEPT = 4
    ACCEPTED = 5
    NACK = 6

class MessageClass(Enum):
    CLIENT_MESSAGE = 0
    PREPARE_MESSAGE = 1
    
class ClientMessage:
    def __init__(self, client_id, client_sequence, message, replica_id):
        self.client_id = client_id
        self.replica_id = replica_id
        self.client_sequence = client_sequence
        self.message = message
        self.message_type = MessageType.CLIENT_PROPOSE.value
    
    def __str__(self):
        return "{0} {1} {2} {3} {4}".format(
            self.message_type, self.client_id, self.client_sequence, self.message, self.replica_id);

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
    def __init__(self, acceptor_id, promised_id, accepted_id, accepted_value, proposer_id, slot):
        self.acceptor_id = acceptor_id; #replica_id
        self.promised_id = promised_id; #<highest_proposal_id_no, replica_id>
        self.last_accepted_id = accepted_id; #<highest_proposal_id_no, replica_id>
        self.last_accepted_value = accepted_value; #value
        self.proposer_id = proposer_id; #replica_id
        self.slot = slot;
        self.message_type = MessageType.PROMISE.value;

    def __str__(self):
        (accepted_highest_proposal_id, accepted_replica_id) = (None, None) if self.last_accepted_id is None else self.last_accepted_id
        return "{0} {1} {2} {3} {4} {5} {6} {7} {8}".format(
            self.message_type, self.acceptor_id, self.promised_id[0], self.promised_id[1],
            accepted_highest_proposal_id, accepted_replica_id, self.last_accepted_value, 
            self.proposer_id, self.slot);

class AcceptedMessage:
    #TO DO: Modify the accepted message
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


def parse_str_message(message, message_class):
    tokens = message.split(" ");

    if message_class == MessageClass.CLIENT_MESSAGE.value and tokens is not None and len(tokens) == 5:
        return ClientMessage(int(tokens[1]), int(tokens[2]), tokens[3], int(tokens[4]));
    
    elif message_class == MessageClass.PREPARE_MESSAGE.value and tokens is not None and len(tokens) == 5:
        return PrepareMessage( int(tokens[1]), (int(tokens[2]), int(tokens[3])), int(tokens[4]));