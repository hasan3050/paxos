from message_type import *;

class Acceptor ():
    def __init__(self, id, promised_id=None, accepted_id=None, accepted_value=None):
        self.id             = id
        self.promised_id    = promised_id
        self.accepted_id    = accepted_id
        self.accepted_value = accepted_value

    def receive_prepare(self, message):
        if self.promised_id is None or message.proposal_id >= self.promised_id:
            self.promised_id = message.proposal_id
            return PromiseMessage(self.id, self.promised_id, self.accepted_id, self.accepted_value, message.proposer_id, message.slot)
        else:
            return NackMessage(self.id, self.promised_id, message.proposer_id, message.proposal_id, message.slot);
                    
    def receive_accept(self, message):
        if self.promised_id is None or message.proposal_id >= self.promised_id:
            self.promised_id     = message.proposal_id
            self.accepted_id     = message.proposal_id
            self.accepted_value  = message.proposal_value
            return AcceptedMessage(self.id, self.accepted_id, self.accepted_value, message.proposer_id, message.slot);
        else:
            return NackMessage(self.id, self.promised_id, message.proposer_id, message.proposal_id, message.slot);

