# Open Architectural Decisions & Questions (OPEN_QUESTIONS.md)

> **Document Version:** 1.1.0  
> **Classification:** Architectural Governance & Decision Log  
> **Status:** Operator Decisions Recorded (2026-11-15)

This document tracks architectural decisions, infrastructure tradeoffs, and integration prerequisites. All recorded decisions reflect direct owner approval.

---

## 1. Resolved & Active Questions

| ID | Domain | Question / Decision Required | Owner Decision & Direction | Status |
| :---: | :--- | :--- | :--- | :---: |
| **Q-01** | **Host Infrastructure** | Where should the continuous central gateway and daemon execute? | **Resolved: Local Ubuntu Desktop.** Currently no remote server is purchased. The daemon and services will run locally on the operator's Ubuntu machine (`DISPLAY=:0` / `:99`). VPS migration deferred to post-v1. | **Resolved** |
| **Q-02** | **Backend Language Stack** | Python (FastAPI/Pydantic) vs TypeScript backend? | **Resolved: Standardize on Python 3.10+.** Gateway, Orchestrator, Policy Engine, Ledger, Kill Switch, Cost Meter, and Tool SDK remain 100% Python to maximize cohesion with existing OS/VLM drivers. Web/Mobile UI remains HTML/JS/CSS PWA. | **Resolved** |
| **Q-03** | **Commercial Multi-Tenancy** | Single-operator assistant vs multi-tenant SaaS? | **Resolved: Strictly Single-Operator Personal Assistant** for Khairul Islam Emon (@Khairul Islam Emon). | **Resolved** |
| **Q-04** | **ShoppieFlyBD Analytics API** | Direct MySQL access vs read-only Laravel reporting API? | **Deferred to Phase 5:** Dedicated token-authenticated read-only Laravel reporting endpoints will be prepared prior to Phase 5. | **Deferred (Phase 5)** |
| **Q-05** | **Outbound Messaging Connectors** | Telegram Bot vs WhatsApp Business API vs unofficial WhatsApp? | **Resolved: Telegram Bot.** Selected for real-time mobile push notifications, alerts, and interactive on-screen approval buttons. No unofficial WhatsApp automation. | **Resolved** |
| **Q-06** | **Client AI Data Restrictions** | Specific client repositories requiring `ai_restricted: true`? | **Pending Client Audit:** None selected at this moment. Specific client restrictions will be configured in `packages/registry` as clients are onboarded. | **Pending Selection** |
| **Q-07** | **STT & TTS Dialect Performance** | Mixed Bengali and Banglish recognition quality? | **Validated:** Local Faster-Whisper int8 + Edge-TTS Bengali voice (`bn-BD-NabanitaNeural`) validated with real microphone hardware. Further dialect optimization in Phase 4. | **Validated** |
