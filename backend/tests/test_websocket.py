import pytest
from backend.main import app, manager
from starlette.testclient import TestClient


@pytest.fixture(autouse=True)
def clean_manager():
    manager.sessions.clear()
    manager.display_name_to_id.clear()
    yield
    manager.sessions.clear()
    manager.display_name_to_id.clear()


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["active_clients"] == 0


def test_websocket_connect_and_welcome():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "welcome"
        assert "sessionId" in msg
        assert "displayName" in msg


def test_pairing_and_signaling_flow():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws_a, client.websocket_connect("/ws") as ws_b:
        # 1. Welcome messages
        welcome_a = ws_a.receive_json()
        welcome_b = ws_b.receive_json()

        assert welcome_a["type"] == "welcome"
        assert welcome_b["type"] == "welcome"

        # 2. Peer A requests pair with Peer B using display name
        ws_a.send_json({
            "type": "request_pair",
            "target": welcome_b["displayName"]
        })

        # 3. Peer B receives incoming_request
        incoming = ws_b.receive_json()
        assert incoming["type"] == "incoming_request"
        assert incoming["fromSessionId"] == welcome_a["sessionId"]
        assert incoming["fromDisplayName"] == welcome_a["displayName"]

        # 4. Peer B accepts
        ws_b.send_json({
            "type": "accept_pair",
            "fromSessionId": welcome_a["sessionId"]
        })

        # 5. Both peers receive pair_accepted
        accepted_a = ws_a.receive_json()
        accepted_b = ws_b.receive_json()

        assert accepted_a["type"] == "pair_accepted"
        assert accepted_a["peerId"] == welcome_b["sessionId"]
        assert accepted_a["initiator"] is True

        assert accepted_b["type"] == "pair_accepted"
        assert accepted_b["peerId"] == welcome_a["sessionId"]
        assert accepted_b["initiator"] is False

        # 6. WebRTC Signaling relay test (SDP offer from A to B)
        ws_a.send_json({
            "type": "signal",
            "signalType": "offer",
            "payload": {"type": "offer", "sdp": "fake_sdp"}
        })

        signal_b = ws_b.receive_json()
        assert signal_b["type"] == "signal"
        assert signal_b["fromSessionId"] == welcome_a["sessionId"]
        assert signal_b["signalType"] == "offer"
        assert signal_b["payload"] == {"type": "offer", "sdp": "fake_sdp"}


def test_pairing_rejection():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws_a, client.websocket_connect("/ws") as ws_b:
        welcome_a = ws_a.receive_json()
        welcome_b = ws_b.receive_json()

        ws_a.send_json({
            "type": "request_pair",
            "target": welcome_b["sessionId"]
        })

        incoming = ws_b.receive_json()
        assert incoming["type"] == "incoming_request"

        ws_b.send_json({
            "type": "reject_pair",
            "fromSessionId": welcome_a["sessionId"]
        })

        rejected_a = ws_a.receive_json()
        assert rejected_a["type"] == "pair_rejected"
        assert rejected_a["fromSessionId"] == welcome_b["sessionId"]


def test_peer_unavailable_generic_error():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws_a, client.websocket_connect("/ws") as ws_b, client.websocket_connect("/ws") as ws_c:
        ws_a.receive_json()
        welcome_b = ws_b.receive_json()
        welcome_c = ws_c.receive_json()

        # 1. Non-existent peer -> PEER_UNAVAILABLE
        ws_a.send_json({
            "type": "request_pair",
            "target": "NonExistentPeer#9999"
        })
        err1 = ws_a.receive_json()
        assert err1["type"] == "error"
        assert err1["code"] == "PEER_UNAVAILABLE"
        assert "offline, busy, or unavailable" in err1["message"]

        # 2. Pair B and C so B becomes busy
        ws_b.send_json({
            "type": "request_pair",
            "target": welcome_c["sessionId"]
        })
        ws_c.receive_json()  # incoming_request
        ws_c.send_json({
            "type": "accept_pair",
            "fromSessionId": welcome_b["sessionId"]
        })
        ws_b.receive_json()  # pair_accepted
        ws_c.receive_json()  # pair_accepted

        # 3. Peer A tries to pair with B (busy) -> Same generic PEER_UNAVAILABLE
        ws_a.send_json({
            "type": "request_pair",
            "target": welcome_b["sessionId"]
        })
        err2 = ws_a.receive_json()
        assert err2["type"] == "error"
        assert err2["code"] == "PEER_UNAVAILABLE"
        assert "offline, busy, or unavailable" in err2["message"]


def test_invalid_client_message_rejected_by_pydantic():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # welcome

        # Send unknown type
        ws.send_json({"type": "unknown_action", "foo": "bar"})
        err1 = ws.receive_json()
        assert err1["type"] == "error"
        assert err1["code"] == "INVALID_MESSAGE"

        # Send known type with missing required field
        ws.send_json({"type": "request_pair"})
        err2 = ws.receive_json()
        assert err2["type"] == "error"
        assert err2["code"] == "INVALID_MESSAGE"


def test_signal_type_validation():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws_a, client.websocket_connect("/ws") as ws_b:
        welcome_a = ws_a.receive_json()
        welcome_b = ws_b.receive_json()

        # Pair peers
        ws_a.send_json({"type": "request_pair", "target": welcome_b["sessionId"]})
        ws_b.receive_json()  # incoming_request
        ws_b.send_json({"type": "accept_pair", "fromSessionId": welcome_a["sessionId"]})
        ws_a.receive_json()  # pair_accepted
        ws_b.receive_json()  # pair_accepted

        # Invalid signalType
        ws_a.send_json({"type": "signal", "signalType": "invalid_type", "payload": {}})
        err = ws_a.receive_json()
        assert err["type"] == "error"
        assert err["code"] == "INVALID_MESSAGE"


def test_oversized_payload_rejected():
    client = TestClient(app)
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()  # welcome

        # Payload over 64 KB
        huge_data = "x" * (70 * 1024)
        ws.send_text(huge_data)
        err = ws.receive_json()
        assert err["type"] == "error"
        assert err["code"] == "INVALID_MESSAGE"
        assert "too large" in err["message"].lower()




