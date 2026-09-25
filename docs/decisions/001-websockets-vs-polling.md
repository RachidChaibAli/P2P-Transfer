# Why WebSockets Instead of HTTP Polling

## Summary
To connect two users for a P2P transfer, the app needs real-time communication: detecting when users are online, showing instant connection popups, and exchanging WebRTC connection data.

I chose a single **WebSocket connection** instead of traditional **HTTP Polling**.

---

## Why Not HTTP Polling?
Initially, I considered using standard REST requests where the browser asks the server every 1–2 seconds: *"Do I have any connection requests?"*

However, this has clear drawbacks:
1. **Unnecessary Server Load:** Hundreds of browsers constantly asking the server wastes CPU and network resources, even when nothing is happening.
2. **Laggy Experience:** A user has to wait up to 2 seconds just to see an incoming transfer request.
3. **Ghost Users:** If a user closes the browser tab, the server doesn't know immediately and keeps showing them as online.

---

## Why WebSockets?
1. **Instant Updates:** When User A sends an invite, User B sees the popup with zero delay.
2. **Resource-Friendly:** An idle WebSocket uses almost no server memory or processing power compared to constant polling requests.
3. **Instant Disconnects:** When a user closes the tab, the server detects it immediately and notifies their partner.
4. **All-in-One Channel:** The same connection handles user presence, pairing requests, and WebRTC signaling.
