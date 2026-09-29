from enum import Enum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter


class ClientState(str, Enum):
    IDLE = "idle"
    OUTGOING_REQUEST = "outgoing_request"
    INCOMING_REQUEST = "incoming_request"
    PAIRED = "paired"


class ErrorCode(str, Enum):
    PEER_UNAVAILABLE = "PEER_UNAVAILABLE"
    INVALID_STATE = "INVALID_STATE"
    NOT_PAIRED = "NOT_PAIRED"
    INVALID_MESSAGE = "INVALID_MESSAGE"


# --- Server-to-Client Messages ---

class WelcomeMessage(BaseModel):
    type: str = "welcome"
    sessionId: str
    displayName: str


class IncomingRequestMessage(BaseModel):
    type: str = "incoming_request"
    fromSessionId: str
    fromDisplayName: str


class PairAcceptedMessage(BaseModel):
    type: str = "pair_accepted"
    peerId: str
    peerDisplayName: str
    initiator: bool


class PairRejectedMessage(BaseModel):
    type: str = "pair_rejected"
    fromSessionId: str
    message: str = "Peer declined the connection request"


# Maximum allowed raw WebSocket text message size (64 KB) - prevents memory exhaustion DoS
MAX_MESSAGE_SIZE_BYTES = 64 * 1024

SignalType = Literal["offer", "answer", "ice-candidate"]


class SignalMessage(BaseModel):
    type: str = "signal"
    fromSessionId: str
    signalType: SignalType
    payload: Any


class PeerDisconnectedMessage(BaseModel):
    type: str = "peer_disconnected"
    message: str = "Your peer has disconnected"


class ErrorMessage(BaseModel):
    type: str = "error"
    code: ErrorCode
    message: str


# --- Client-to-Server Messages (Validated with Pydantic) ---

class RequestPairClientMessage(BaseModel):
    type: Literal["request_pair"]
    target: str = Field(min_length=1, max_length=100)


class AcceptPairClientMessage(BaseModel):
    type: Literal["accept_pair"]
    fromSessionId: str = Field(min_length=1, max_length=100)


class RejectPairClientMessage(BaseModel):
    type: Literal["reject_pair"]
    fromSessionId: str = Field(min_length=1, max_length=100)


class SignalClientMessage(BaseModel):
    type: Literal["signal"]
    signalType: SignalType
    payload: Any


class LeavePairClientMessage(BaseModel):
    type: Literal["leave_pair"]


ClientIncomingMessage = Annotated[
    RequestPairClientMessage | AcceptPairClientMessage | RejectPairClientMessage | SignalClientMessage | LeavePairClientMessage,
    Field(discriminator="type"),
]

client_message_adapter: TypeAdapter[ClientIncomingMessage] = TypeAdapter(ClientIncomingMessage)
