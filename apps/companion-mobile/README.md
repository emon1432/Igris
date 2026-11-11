# Igris Companion Mobile App (`apps/companion-mobile`)

> **Module Role:** Dedicated native mobile client for Igris (Android & iOS).  
> **Tech Stack:** Flutter (Dart) or React Native (Expo) + WebRTC audio streaming + WebSocket command bridge.

---

## 1. Overview & Core Experience
This mobile client enables full remote voice commanding and monitoring of your host Linux workstation while on the go:
* **Hands-Free Background Voice:** Talk directly through Bluetooth earbuds or mobile mic; audio streams to the home PC in real time.
* **Lock-Screen Widget & Push-to-Talk:** Send voice commands without unlocking the device.
* **Live Audio Feedback:** Spoken feedback from Igris streams directly back to your headphones.
* **Peek Screen Mode:** Stream a lightweight, low-bandwidth video/screenshot feed of what Igris is doing on the virtual or primary display.

---

## 2. Core Architecture
1. **WebRTC Ultra-Low Latency Audio Stream:** Sub-second bi-directional voice communication.
2. **Secure Network Transport:** Direct peer-to-peer connection via Tailscale / WireGuard or Cloudflare Tunnel with mTLS.
3. **Background Audio Service:** Maintains connection while the screen is off or the phone is in your pocket.
4. **Push Notifications:** Instant alerts upon completion of long-running workflows or task checkpoints.
