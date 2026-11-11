# System Architecture Specification (`ARCHITECTURE.md`)

> **Protocol Rule:** This document serves as the master architectural reference for Igris. Any major subsystem addition or architectural modification must be reflected here.

---

## 1. End-to-End System Topology

```mermaid
flowchart TD
    subgraph Clients ["1. Clients & Input Channels"]
        MIC["Desktop Microphone (Wake-Word + STT)"]
        MOBILE["Mobile Companion (WebRTC / Tailscale)"]
        CLI["CLI Controller"]
    end

    subgraph CoreEngine ["2. Igris Core Engine (apps/core-engine)"]
        ORCHESTRATOR["Central Task Orchestrator"]
        ROUTER["Dual-Mode Router (Live vs. Ghost)"]
        VLM_BRAIN["VLM Reasoning Core (ReAct Loop)"]
        STATE_MGR["Runtime State & Context Manager"]
    end

    subgraph PerceptionLayer ["3. Perception Layer (Eyes & Ears)"]
        MSS_CAP["Frame Grabber (MSS)"]
        ATSPI_INSP["AT-SPI UI Accessibility Inspector"]
        AUDIO_SINK["PipeWire / PulseAudio Virtual Loopback"]
    end

    subgraph ActionLayer ["4. OS Action Drivers (The Hands)"]
        XVFB_MGR["Xvfb Virtual Display Manager (:99)"]
        INPUT_SIM["Input Simulator (xdotool / ydotool)"]
        BASH_RUNNER["Async Bash Shell Engine"]
    end

    subgraph FeedbackLayer ["5. Feedback & Overlays"]
        HUD["Desktop Laser Overlay (apps/desktop-overlay)"]
        TTS["Voice Synthesis (Edge-TTS / Piper)"]
    end

    MIC --> ORCHESTRATOR
    MOBILE --> ORCHESTRATOR
    CLI --> ORCHESTRATOR

    ORCHESTRATOR <--> STATE_MGR
    ORCHESTRATOR --> ROUTER

    ROUTER -->|Live Mode :0| INPUT_SIM
    ROUTER -->|Ghost Mode :99| XVFB_MGR
    ROUTER -->|CLI Fast Path| BASH_RUNNER

    INPUT_SIM --> MSS_CAP
    MSS_CAP --> VLM_BRAIN
    ATSPI_INSP --> VLM_BRAIN
    AUDIO_SINK --> VLM_BRAIN

    VLM_BRAIN --> ORCHESTRATOR

    INPUT_SIM -->|Visual Feedback| HUD
    ORCHESTRATOR --> TTS
    TTS --> MIC
    TTS --> MOBILE
```

---

## 2. Dual-Mode Execution Mechanics

### 2.1 Live Co-Pilot Mode (`DISPLAY=:0`)
* **Target:** Primary physical display for visual collaboration.
* **Safety Interlock:**
  - Background thread monitors physical mouse coordinates.
  - If the user moves the mouse ($\Delta d > 10\text{px}$), `agent.pause()` triggers immediately and yields input control.
* **Visual Feedback:**
  - `apps/desktop-overlay` projects a transient, non-intrusive laser ring or bounding box on the target coordinate before dispatching clicks.

### 2.2 Ghost Mode (`DISPLAY=:99`)
* **Target:** Isolated virtual framebuffer managed by Xvfb.
* **Isolation Guarantees:**
  - Isolated from active windows and user interactions on `:0`.
  - Application commands spawned under `DISPLAY=:99 <cmd> &`.
  - Input events and frame captures routed exclusively through the `:99` display socket.

---

## 3. Autonomous Reasoning Loop (ReAct Loop)

```
[User Task] ───> 1. Observe (Screen Frame + AT-SPI Tree)
                       │
                       ▼
                 2. Reason (Plan Next Action: Click / Type / Scroll / Bash)
                       │
                       ▼
                 3. Act (Dispatch to Virtual or Primary Display)
                       │
                       ▼
                 4. Verify (Compare Result Frame against Target State)
                       │
      [Pending] ◄──────┴──────► [Completed] ───> Voice / Notification Feedback
```

---

## 4. Coordinate Translation & Target Resolution

Models output normalized coordinates in the $[0, 1000]$ range. Translation to display pixels:

$$X_{actual} = \left\lfloor \frac{X_{norm}}{1000} \times \text{Display Width} \right\rfloor$$
$$Y_{actual} = \left\lfloor \frac{Y_{norm}}{1000} \times \text{Display Height} \right\rfloor$$

When AT-SPI accessibility elements are available within the bounding neighborhood, the component center is resolved deterministically:
$$\text{Target Center} = \left( x + \frac{w}{2}, y + \frac{h}{2} \right)$$
