from proposer import Proposer;
from acceptor import Acceptor;
from learner import Learner;

class PaxosInstance (Proposer, Acceptor, Learner):

    def __init__(self, id, quorum_size, is_leader=False, promised_id=None, accepted_id=None, accepted_value=None):
        Proposer.__init__(self, id, quorum_size, is_leader)
        Acceptor.__init__(self, id, promised_id, accepted_id, accepted_value)
        Learner.__init__(self, id, quorum_size)

    def receive_prepare(self, msg):
        self.observe_proposal( msg.proposal_id )
        return super(PaxosInstance,self).receive_prepare(msg)
                    
    def receive_accept(self, msg):
        self.observe_proposal( msg.proposal_id )
        return super(PaxosInstance,self).receive_accept(msg)
