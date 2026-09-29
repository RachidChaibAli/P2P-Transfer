import json
import logging
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from backend.manager import ClientSession, ConnectionManager
from backend.names import generate_display_name
from backend.schemas import (
    MAX_MESSAGE_SIZE_BYTES,
    AcceptPairClientMessage,
    ClientState,
    ErrorCode,
    ErrorMessage,
    IncomingRequestMessage,
    LeavePairClientMessage,
    PairAcceptedMessage,
    PairRejectedMessage,
    PeerDisconnectedMessage,
    RejectPairClientMessage,
    RequestPairClientMessage,
    SignalClientMessage,
    SignalMessage,
    WelcomeMessage,
    client_message_adapter,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("p2p-transfer.backend")

app = FastAPI(title="P2P Transfer Signaling Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = ConnectionManager()


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "active_clients": len(manager.sessions),
    }


async def send_error(ws: WebSocket, code: ErrorCode, message: str) -> None:
    logger.warning("Sending error code=%s message=%s", code.value, message)
    err = ErrorMessage(code=code, message=message)
    await ws.send_json(err.model_dump())


async def handle_disconnect(session_id: str) -> None:
    session = manager.unregister(session_id)
    if not session:
        return

    logger.info("Client disconnected: %s (%s)", session.display_name, session.session_id)

    # Notify active partner if paired
    if session.paired_peer_id:
        partner = manager.get_by_id(session.paired_peer_id)
        if partner:
            partner.reset()
            logger.info("Notifying partner %s (%s) of disconnection", partner.display_name, partner.session_id)
            disc = PeerDisconnectedMessage(message="Your peer has disconnected")
            await manager.send_json(partner.session_id, disc.model_dump())

    # Cancel pending request if in negotiation
    elif session.pending_peer_id:
        target = manager.get_by_id(session.pending_peer_id)
        if target:
            target.reset()
            logger.info("Canceling pending request with %s due to disconnect", target.session_id)
            rej = PairRejectedMessage(
                fromSessionId=session.session_id,
                message="Peer disconnected while request was pending",
            )
            await manager.send_json(target.session_id, rej.model_dump())


async def handle_request_pair(session: ClientSession, msg: RequestPairClientMessage) -> None:
    ws = session.websocket
    logger.info("Pairing requested by %s (%s) -> target: '%s'", session.display_name, session.session_id, msg.target)

    if session.state != ClientState.IDLE:
        logger.warning("Rejected pairing request from %s: invalid state '%s'", session.session_id, session.state.value)
        await send_error(ws, ErrorCode.INVALID_STATE, f"Cannot request pairing while in state '{session.state.value}'")
        return

    target_peer = manager.find_peer(msg.target)
    if (
        not target_peer
        or target_peer.session_id == session.session_id
        or target_peer.state != ClientState.IDLE
    ):
        logger.warning(
            "Pairing target '%s' unavailable (exists=%s, self=%s, target_state=%s)",
            msg.target,
            target_peer is not None,
            target_peer.session_id == session.session_id if target_peer else False,
            target_peer.state.value if target_peer else "none",
        )
        await send_error(ws, ErrorCode.PEER_UNAVAILABLE, "Peer is offline, busy, or unavailable")
        return

    session.set_pending(ClientState.OUTGOING_REQUEST, target_peer.session_id)
    target_peer.set_pending(ClientState.INCOMING_REQUEST, session.session_id)

    logger.info("Forwarding incoming_request from %s to %s", session.session_id, target_peer.session_id)
    req_msg = IncomingRequestMessage(
        fromSessionId=session.session_id,
        fromDisplayName=session.display_name,
    )
    await manager.send_json(target_peer.session_id, req_msg.model_dump())


async def handle_accept_pair(session: ClientSession, msg: AcceptPairClientMessage) -> None:
    ws = session.websocket
    logger.info("Accept pair from %s (%s) for initiator %s", session.display_name, session.session_id, msg.fromSessionId)

    if session.state != ClientState.INCOMING_REQUEST or session.pending_peer_id != msg.fromSessionId:
        logger.warning("Accept pair rejected: %s state is '%s', pending is '%s'", session.session_id, session.state.value, session.pending_peer_id)
        await send_error(ws, ErrorCode.INVALID_STATE, "No pending request from this peer to accept")
        return

    initiator = manager.get_by_id(msg.fromSessionId)
    if not initiator or initiator.state != ClientState.OUTGOING_REQUEST:
        session.reset()
        logger.warning("Initiator %s not found or not in outgoing_request state", msg.fromSessionId)
        await send_error(ws, ErrorCode.PEER_UNAVAILABLE, "Peer is offline, busy, or unavailable")
        return

    # Pair both peers
    session.set_paired(initiator.session_id)
    initiator.set_paired(session.session_id)
    logger.info("Successfully paired %s <--> %s", session.display_name, initiator.display_name)

    # Notify initiator (initiator: True)
    init_msg = PairAcceptedMessage(
        peerId=session.session_id,
        peerDisplayName=session.display_name,
        initiator=True,
    )
    await manager.send_json(initiator.session_id, init_msg.model_dump())

    # Notify target (initiator: False)
    target_msg = PairAcceptedMessage(
        peerId=initiator.session_id,
        peerDisplayName=initiator.display_name,
        initiator=False,
    )
    await manager.send_json(session.session_id, target_msg.model_dump())


async def handle_reject_pair(session: ClientSession, msg: RejectPairClientMessage) -> None:
    ws = session.websocket
    logger.info("Reject pair from %s for initiator %s", session.session_id, msg.fromSessionId)

    if session.state != ClientState.INCOMING_REQUEST or session.pending_peer_id != msg.fromSessionId:
        logger.warning("Reject pair invalid state: %s state='%s'", session.session_id, session.state.value)
        await send_error(ws, ErrorCode.INVALID_STATE, "No pending request from this peer to reject")
        return

    initiator = manager.get_by_id(msg.fromSessionId)
    session.reset()

    if initiator and initiator.state == ClientState.OUTGOING_REQUEST:
        initiator.reset()
        logger.info("Notifying initiator %s that request was rejected", initiator.session_id)
        rej = PairRejectedMessage(
            fromSessionId=session.session_id,
            message="Peer declined the connection request",
        )
        await manager.send_json(initiator.session_id, rej.model_dump())


async def handle_signal(session: ClientSession, msg: SignalClientMessage) -> None:
    ws = session.websocket
    if session.state != ClientState.PAIRED or not session.paired_peer_id:
        logger.warning("Signal rejected from %s: client is not in paired state", session.session_id)
        await send_error(ws, ErrorCode.NOT_PAIRED, "Attempted to send a WebRTC signal without an active pair")
        return

    logger.debug("Relaying signal '%s' from %s -> %s", msg.signalType, session.session_id, session.paired_peer_id)
    sig_msg = SignalMessage(
        fromSessionId=session.session_id,
        signalType=msg.signalType,
        payload=msg.payload,
    )
    await manager.send_json(session.paired_peer_id, sig_msg.model_dump())


async def handle_leave_pair(session: ClientSession) -> None:
    logger.info("Client %s (%s) requested leave_pair", session.display_name, session.session_id)
    if session.state == ClientState.PAIRED and session.paired_peer_id:
        partner = manager.get_by_id(session.paired_peer_id)
        session.reset()
        if partner:
            partner.reset()
            logger.info("Notifying partner %s (%s) that peer left", partner.display_name, partner.session_id)
            disc = PeerDisconnectedMessage(message="Your peer left the session")
            await manager.send_json(partner.session_id, disc.model_dump())
    elif session.pending_peer_id:
        partner = manager.get_by_id(session.pending_peer_id)
        session.reset()
        if partner:
            partner.reset()
            logger.info("Canceling pending request with %s on leave_pair", partner.session_id)
            rej = PairRejectedMessage(
                fromSessionId=session.session_id,
                message="Pairing request was cancelled",
            )
            await manager.send_json(partner.session_id, rej.model_dump())
    else:
        session.reset()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    session_id = str(uuid.uuid4())
    display_name = generate_display_name()
    while manager.find_peer(display_name) is not None:
        display_name = generate_display_name()

    session = ClientSession(
        session_id=session_id,
        display_name=display_name,
        websocket=websocket,
    )
    manager.register(session)
    logger.info("New client connected: %s (%s) [Total active: %d]", display_name, session_id, len(manager.sessions))

    # Send Welcome message
    welcome = WelcomeMessage(sessionId=session_id, displayName=display_name)
    await websocket.send_json(welcome.model_dump())

    try:
        while True:
            text_data = await websocket.receive_text()

            # Protect server memory from oversized payload DoS
            if len(text_data.encode("utf-8")) > MAX_MESSAGE_SIZE_BYTES:
                logger.warning(
                    "Oversized message (%d bytes) received from session %s. Exceeds limit of %d bytes.",
                    len(text_data.encode("utf-8")),
                    session_id,
                    MAX_MESSAGE_SIZE_BYTES,
                )
                await send_error(websocket, ErrorCode.INVALID_MESSAGE, "Message payload too large")
                continue

            try:
                raw_data = json.loads(text_data)
                if not isinstance(raw_data, dict):
                    await send_error(websocket, ErrorCode.INVALID_MESSAGE, "Expected JSON object")
                    continue
            except (ValueError, json.JSONDecodeError):
                logger.warning("Received invalid non-JSON payload from session %s", session_id)
                await send_error(websocket, ErrorCode.INVALID_MESSAGE, "Malformed JSON message")
                continue

            try:
                message = client_message_adapter.validate_python(raw_data)
            except ValidationError as val_err:
                logger.warning("Invalid message schema received from %s: %s", session_id, val_err.errors())
                await send_error(websocket, ErrorCode.INVALID_MESSAGE, "Invalid message schema or unknown type")
                continue

            match message:
                case RequestPairClientMessage():
                    await handle_request_pair(session, message)
                case AcceptPairClientMessage():
                    await handle_accept_pair(session, message)
                case RejectPairClientMessage():
                    await handle_reject_pair(session, message)
                case SignalClientMessage():
                    await handle_signal(session, message)
                case LeavePairClientMessage():
                    await handle_leave_pair(session)

    except WebSocketDisconnect:
        await handle_disconnect(session_id)
    except Exception:
        logger.exception("Unexpected error in websocket handler for session %s", session_id)
        await handle_disconnect(session_id)


def main():
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
