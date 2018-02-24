from message_type import *;
class Learner ():
    class ProposalStatus (object):
        __slots__ = ['accept_count', 'retain_count', 'acceptors', 'value']
        def __init__(self, value):
            self.accept_count = 0
            self.retain_count = 0
            self.acceptors    = set()
            self.value        = value

            
    def __init__(self, id, quorum_size):
        self.id = id
        self.quorum_size       = quorum_size
        self.proposals         = dict() # maps proposal_id to ProposalStatus
        self.acceptors         = dict() # maps replica_id to last_accepted_proposal_id
        self.final_value       = None
        self.final_acceptors   = None   # Will be a set of acceptor ids once the final value is chosen
        self.final_proposal_id = None

        
    def receive_accepted(self, message):
        if self.final_value is not None:
            if ( self.final_proposal_id in None or message.proposal_id >= self.final_proposal_id) and message.accepted_value == self.final_value:
                self.final_acceptors.add( message.acceptor_id )
            
            return Resolution(self.id, self.final_value, message.slot);
            
        last_accepted_proposal_id = self.acceptors.get(message.acceptor_id)

        if last_accepted_proposal_id is not None and message.proposal_id <= last_accepted_proposal_id:
            return # Old message

        self.acceptors[ message.acceptor_id ] = message.proposal_id
        
        if last_accepted_proposal_id is not None and last_accepted_proposal_id in self.proposals:
            proposal_status = self.proposals[ last_accepted_proposal_id ]
            proposal_status.retain_count -= 1
            proposal_status.acceptors.remove(message.acceptor_id)
            if proposal_status.retain_count == 0:
                del self.proposals[ last_accepted_proposal_id ]

        if not message.proposal_id in self.proposals:
            self.proposals[ message.proposal_id ] = Learner.ProposalStatus(message.accepted_value)

        proposal_status = self.proposals[ message.proposal_id ]

        assert message.accepted_value == proposal_status.value, 'Value mismatch for single proposal!'

        proposal_status.accept_count += 1
        proposal_status.retain_count += 1
        proposal_status.acceptors.add(message.acceptor_id)

        if proposal_status.accept_count == self.quorum_size:
            self.final_proposal_id = message.proposal_id
            self.final_value       = message.accepted_value
            self.final_acceptors   = proposal_status.acceptors
            self.proposals         = dict()
            self.acceptors         = dict()

            return Resolution( self.id, self.final_value, message.slot )
