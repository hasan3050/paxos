from message_type import *;

class Proposer ():
    leader               = False
    proposed_value       = None 
    proposal_id          = None # <highest_proposal_id_no, id>
    highest_accepted_id  = None
    promises_received    = None #set
    nacks_received       = None #set
    current_prepare_msg  = None #<id, <highest_proposal_id_no, id> >
    current_accept_msg   = None #<id, <highest_proposal_id_no, id>, proposed_value >
    
    def __init__(self, id, quorum_size, is_leader = False):
        self.id = id
        self.leader = is_leader
        self.quorum_size = quorum_size
        self.proposal_id = (0, self.id)
        self.highest_proposal_id = (0, self.id)

    def prepare(self):
        self.leader              = False
        self.promises_received   = set()
        self.nacks_received      = set()
        self.proposal_id         = (self.highest_proposal_id[0] + 1, self.id)
        self.highest_proposal_id = self.proposal_id
        self.current_prepare_msg = (self.id, self.proposal_id)

        return self.current_prepare_msg

    def propose_value(self, value, slot):
        if self.proposed_value is None:
            self.proposed_value = value
            
            if self.leader:
                self.current_accept_msg = AcceptMessage(self.id, self.proposal_id, self.proposed_value, slot)
                return self.current_accept_msg

    def observe_proposal(self, proposal_id):
        if proposal_id > self.highest_proposal_id:
            self.highest_proposal_id = proposal_id

            
    def receive_nack(self, message):
        self.observe_proposal( message.promised_id )
        
        if message.proposal_id == self.proposal_id and self.nacks_received is not None:
            self.nacks_received.add( message.acceptor_id )

            if len(self.nacks_received) == self.quorum_size:
                return self.prepare() # Lost leadership or failed to acquire it

    def receive_promise(self, message):
        self.observe_proposal( message.proposal_id )

        if not self.leader and message.proposal_id == self.proposal_id and message.acceptor_id not in self.promises_received:

            self.promises_received.add( message.acceptor_id )

            if message.last_accepted_id is not None and (self.highest_accepted_id is None or message.last_accepted_id > self.highest_accepted_id):
                self.highest_accepted_id = message.last_accepted_id
                if message.last_accepted_value is not None:
                    self.proposed_value = message.last_accepted_value

            if len(self.promises_received) == self.quorum_size:
                self.leader = True

                if self.proposed_value is not None:
                    self.current_accept_msg = AcceptMessage(self.id, self.proposal_id, self.proposed_value, message.slot)
                    return self.current_accept_msg
