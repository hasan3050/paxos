from enum import Enum;

class MessageType(Enum):
    CLIENT_PROPOSE = 0
    LEADER_ACK_PROPOSE = 1