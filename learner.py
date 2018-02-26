from message_type import *;
class Learner ():
    def __init__(self, id, quorum_size):
        self.id = id
        self.quorum_size       = quorum_size
        self.acceptors         = {}     # { proposal_id: { accepted_value: { acceptor: slot }}}
        self.final_value       = None   # <client_id, client_sequence, message>
        self.final_acceptors   = None   # Will be a set of acceptor ids once the final value is chosen
        self.final_proposal_id = None
        
    def receive_accepted(self, message): 
        if (not self.final_proposal_id is None) and message.proposal_id < self.final_proposal_id:
            return;

        if self.final_proposal_id is None or message.proposal_id >= self.final_proposal_id:
            if message.proposal_id not in self.acceptors:
                self.acceptors[message.proposal_id] = {}
            if message.accepted_value not in self.acceptors[message.proposal_id]:
                self.acceptors[message.proposal_id][message.accepted_value] = {}
            if message.acceptor_id not in self.acceptors[message.proposal_id][message.accepted_value]:
                self.acceptors[message.proposal_id][message.accepted_value][message.acceptor_id] = message.slot;

            if len (self.acceptors[message.proposal_id][message.accepted_value]) == self.quorum_size:
                self.final_proposal_id = message.proposal_id;
                self.final_value = message.accepted_value;
                self.final_acceptors =  self.acceptors[message.proposal_id][message.accepted_value].keys();

                return Resolution( self.id, self.final_value, message.slot )

