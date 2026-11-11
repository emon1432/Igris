# Project Igris

> **Linux-First Universal Autonomous OS Operator & Co-Pilot**

---

## 1. Overview
**Igris** is an autonomous Computer Use agent engineered for Linux. Instead of relying on rigid, app-specific APIs, Igris operates like a human user by combining Screen Vision (VLM), the Linux Accessibility Tree (AT-SPI), Virtual Display Isolation (Xvfb), and mouse/keyboard event injection to execute arbitrary desktop workflows.

---

## 2. Dual-Mode Execution Architecture

* **Live Co-Pilot Mode (Foreground / Astra Style):**
  - Operates directly on the user's active screen (`DISPLAY=:0`).
  - Ideal for real-time collaboration during creative tasks (e.g., image manipulation in GIMP/Photoshop, UI review in Figma, or live code debugging).
  - **Emergency Override:** Moving the physical mouse or pressing `Escape` immediately releases control back to the user.

* **Ghost Mode (Background / Isolated Virtual Lab):**
  - Operates inside an invisible virtual framebuffer (`DISPLAY=:99` via Xvfb).
  - Completes background tasks (e.g., messaging on WhatsApp, organizing files, parsing emails, background test runs) with zero disruption to the user's active desktop, movies, or gaming.

---

## 3. Workspace Architecture (Multi-App Monorepo)

```text
/home/emon1432/Documents/Igris/
├── AGENTS.md                       # Root AI agent directive & multi-PC protocol
├── GEMINI.md                       # Language & communication guidelines
├── Igris.code-workspace            # Multi-root IDE workspace configuration
│
├── .agents/                        # Agent living memory, guardrails, & runbooks
│   ├── memory/                     # Multi-PC continuity memory
│   │   ├── HANDOVER.md             # Active sprint status & task handover
│   │   ├── DECISIONS.md            # Architecture Decision Records (ADRs)
│   │   └── ARCHITECTURE.md         # Full system architecture blueprint
│   ├── rules/                      # Safety & mode routing policies
│   └── skills/                     # Virtual display & screen perception skills
│
├── apps/                           # Modular application suite
│   ├── core-engine/                # Python backend daemon, VLM brain, & OS drivers
│   ├── companion-mobile/           # Dedicated mobile client (Flutter / React Native)
│   ├── companion-web/              # Lightweight web client (PWA / WebSockets)
│   └── desktop-overlay/            # Live mode laser pointer & HUD overlay
│
├── docs/                           # Technical documentation & research
│   ├── architecture/               # Dual-mode engine specifications
│   ├── roadmap/                    # 5-phase execution roadmap
│   ├── specs/                      # Safety & display isolation specs
│   └── research/                   # Linux desktop automation research
│
├── packages/                       # Shared data types & RPC protocol schemas
└── scripts/                        # Development & system setup scripts
    └── setup_system_deps.sh        # Linux OS automation package installer
```

---

## 4. Multi-PC Living Memory Protocol
To ensure continuity across multiple machines and AI sessions:
1. **Session Kickoff:** Read `.agents/memory/HANDOVER.md` to understand active priorities.
2. **Architectural Guardrails:** Consult `.agents/memory/DECISIONS.md` before making design changes.
3. **Session Wrap-Up:** Update `HANDOVER.md` with modified files and immediate next steps.

---

## 5. Installation & Getting Started

### 5.1 Install System Dependencies (Linux)
```bash
./scripts/setup_system_deps.sh
```

### 5.2 Set Up Core Engine
```bash
cd apps/core-engine
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 5.3 Test Execution
```bash
# Run in Ghost Mode (Background virtual display)
python -m igris.cli --mode ghost

# Run in Live Co-Pilot Mode (Primary display)
python -m igris.cli --mode live
```
