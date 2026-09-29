# WebSocket Protocol Specification

## 1. Overview
All client-to-server and server-to-client messaging is serialized using JSON over a single WebSocket connection established at `/ws`.

Every message contains a mandatory `type` string attribute indicating the message purpose.

---

## 2. Server-to-Client Messages

### 2.1. `welcome`
Sent immediately after the WebSocket handshake is accepted.
```json
{
  "type": "welcome",
  "sessionId": "c3d4e5f6-7a8b-4c0d-9e1f-2a3b4c5d6e7f",
  "displayName": "Red Strawberry#2233"
}
```

### 2.2. `incoming_request`
Sent to Peer B when Peer A requests to connect with B.
```json
{
  "type": "incoming_request",
  "fromSessionId": "c3d4e5f6-7a8b-4c0d-9e1f-2a3b4c5d6e7f",
  "fromDisplayName": "Red Strawberry#2233"
}
```

### 2.3. `pair_accepted`
Sent to both peers when the target peer accepts the pairing request.
```json
{
  "type": "pair_accepted",
  "peerId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "peerDisplayName": "Blue Mango#7741",
  "initiator": true
}
```
*Note:* The peer with `"initiator": true` is responsible for creating the WebRTC SDP offer.

### 2.4. `pair_rejected`
Sent to the initiator if the target peer rejects the connection request.
```json
{
  "type": "pair_rejected",
  "fromSessionId": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
  "message": "Peer declined the connection request"
}
```

### 2.5. `signal`
Relayed WebRTC signaling message from the paired peer.
```json
{
  "type": "signal",
  "fromSessionId": "c3d4e5f6-7a8b-4c0d-9e1f-2a3b4c5d6e7f",
  "signalType": "offer", 
  "payload": {
    "type": "offer",
    "sdp": "v=0\r\no=- 461173... ..."
  }
}
```
`signalType` can be:
- `"offer"`: WebRTC SDP Offer
- `"answer"`: WebRTC SDP Answer
- `"ice-candidate"`: ICE Candidate information

### 2.6. `peer_disconnected`
Sent to a paired client when their partner disconnects or closes the tab.
```json
{
  "type": "peer_disconnected",
  "message": "Your peer has disconnected"
}
```

### 2.7. `error`
Sent when a client action fails validation or cannot be completed.
```json
{
  "type": "error",
  "code": "PEER_UNAVAILABLE",
  "message": "Peer is offline, busy, or unavailable"
}
```

Common error codes:
- `PEER_UNAVAILABLE`: Target peer is offline, busy, in another session, or unavailable.
- `INVALID_STATE`: Action not allowed in client's current state.
- `NOT_PAIRED`: Attempted to send a WebRTC signal without an active pair.
- `INVALID_MESSAGE`: Malformed message payload or missing required fields.

---

## 3. Client-to-Server Messages

### 3.1. `request_pair`
Sent by Peer A to initiate a connection with Peer B by display name or session ID.
```json
{
  "type": "request_pair",
  "target": "Blue Mango#7741"
}
```

### 3.2. `accept_pair`
Sent by Peer B to accept an incoming pairing request.
```json
{
  "type": "accept_pair",
  "fromSessionId": "c3d4e5f6-7a8b-4c0d-9e1f-2a3b4c5d6e7f"
}
```

### 3.3. `reject_pair`
Sent by Peer B to decline an incoming pairing request.
```json
{
  "type": "reject_pair",
  "fromSessionId": "c3d4e5f6-7a8b-4c0d-9e1f-2a3b4c5d6e7f"
}
```

### 3.4. `signal`
Relays WebRTC SDP offers/answers or ICE candidates to the connected partner.
```json
{
  "type": "signal",
  "signalType": "offer",
  "payload": {
    "type": "offer",
    "sdp": "v=0\r\no=- 461173... ..."
  }
}
```

### 3.5. `leave_pair`
Optional message to manually disconnect from the current partner and return to `idle` state without closing the WebSocket connection.
```json
{
  "type": "leave_pair"
}
```

