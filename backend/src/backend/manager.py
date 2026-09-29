from dataclasses import dataclass

from fastapi import WebSocket

from backend.schemas import ClientState


@dataclass
class ClientSession:
    session_id: str
    display_name: str
    websocket: WebSocket
    state: ClientState = ClientState.IDLE
    pending_peer_id: str | None = None
    paired_peer_id: str | None = None

    def reset(self) -> None:
        """Reset session to idle state without any pending or active peer."""
        self.state = ClientState.IDLE
        self.pending_peer_id = None
        self.paired_peer_id = None

    def set_paired(self, peer_id: str) -> None:
        """Transition session to paired state with given peer."""
        self.state = ClientState.PAIRED
        self.paired_peer_id = peer_id
        self.pending_peer_id = None

    def set_pending(self, state: ClientState, peer_id: str) -> None:
        """Set a pending pairing state (incoming or outgoing)."""
        self.state = state
        self.pending_peer_id = peer_id


class ConnectionManager:
    def __init__(self) -> None:
        # Maps session_id -> ClientSession
        self.sessions: dict[str, ClientSession] = {}
        # Maps lowercased display_name -> session_id for fast lookup
        self.display_name_to_id: dict[str, str] = {}

    def register(self, session: ClientSession) -> None:
        self.sessions[session.session_id] = session
        self.display_name_to_id[session.display_name.lower()] = session.session_id

    def unregister(self, session_id: str) -> ClientSession | None:
        session = self.sessions.pop(session_id, None)
        if session:
            self.display_name_to_id.pop(session.display_name.lower(), None)
        return session

    def get_by_id(self, session_id: str) -> ClientSession | None:
        return self.sessions.get(session_id)

    def find_peer(self, target: str) -> ClientSession | None:
        """Find a peer session by session_id or case-insensitive display_name."""
        clean_target = target.strip()
        if clean_target in self.sessions:
            return self.sessions[clean_target]
        sid = self.display_name_to_id.get(clean_target.lower())
        return self.sessions.get(sid) if sid else None

    async def send_json(self, session_id: str, data: dict) -> bool:
        """Send JSON payload to peer WebSocket safely without raising exceptions."""
        session = self.get_by_id(session_id)
        if session:
            try:
                await session.websocket.send_json(data)
                return True
            except (RuntimeError, OSError):
                return False
        return False
