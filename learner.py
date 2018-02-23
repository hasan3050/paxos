class Learner ():
#     '''
#     This class listens to Accepted messages, determines when the final value is
#     selected, and tracks which peers have accepted the final value.
#     '''
#     class ProposalStatus (object):
#         __slots__ = ['accept_count', 'retain_count', 'acceptors', 'value']
#         def __init__(self, value):
#             self.accept_count = 0
#             self.retain_count = 0
#             self.acceptors    = set()
#             self.value        = value

            
    def __init__(self, id, quorum_size):
        self.id = id
        self.quorum_size       = quorum_size
        self.proposals         = dict() # maps proposal_id => ProposalStatus
        self.acceptors         = dict() # maps from_uid => last_accepted_proposal_id
        self.final_value       = None
        self.final_acceptors   = None   # Will be a set of acceptor UIDs once the final value is chosen
        self.final_proposal_id = None

        
#     def receive_accepted(self, msg):
#         '''
#         Called when an Accepted message is received from an acceptor. Once the final value
#         is determined, the return value of this method will be a Resolution message containing
#         the consentual value. Subsequent calls after the resolution is chosen will continue to add
#         new Acceptors to the final_acceptors set and return Resolution messages.
#         '''
#         if self.final_value is not None:
#             if msg.proposal_id >= self.final_proposal_id and msg.proposal_value == self.final_value:
#                 self.final_acceptors.add( msg.from_uid )
#             return Resolution(self.network_uid, self.final_value)
            
#         last_pn = self.acceptors.get(msg.from_uid)

#         if msg.proposal_id <= last_pn:
#             return # Old message

#         self.acceptors[ msg.from_uid ] = msg.proposal_id
        
#         if last_pn is not None:
#             ps = self.proposals[ last_pn ]
#             ps.retain_count -= 1
#             ps.acceptors.remove(msg.from_uid)
#             if ps.retain_count == 0:
#                 del self.proposals[ last_pn ]

#         if not msg.proposal_id in self.proposals:
#             self.proposals[ msg.proposal_id ] = Learner.ProposalStatus(msg.proposal_value)

#         ps = self.proposals[ msg.proposal_id ]

#         assert msg.proposal_value == ps.value, 'Value mismatch for single proposal!'

#         ps.accept_count += 1
#         ps.retain_count += 1
#         ps.acceptors.add(msg.from_uid)

#         if ps.accept_count == self.quorum_size:
#             self.final_proposal_id = msg.proposal_id
#             self.final_value       = msg.proposal_value
#             self.final_acceptors   = ps.acceptors
#             self.proposals         = None
#             self.acceptors         = None

#             return Resolution( self.network_uid, self.final_value )
