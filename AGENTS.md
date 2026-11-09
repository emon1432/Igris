# AGENTS.md - Root AI Agent Directive

> **Universal Workspace Guidance & Multi-PC Continuity Protocol**  
> Repository: `Igris` (Autonomous Linux OS Operator & Co-Pilot)  
> Last Updated: 2026-11-10

---

## 1. Repository Summary

**Igris** হলো একটি লিনাক্স-ফার্স্ট ইউনিভার্সাল অটোনোমাস ওএস অপারেটর (Universal Autonomous OS Operator / Computer Use System)। এটি কোনো নির্দিষ্ট অ্যাপের API-এর ওপর নির্ভরশীল না হয়ে স্ক্রিন ভিশন (Screen Vision), লিনাক্স এক্সেসিবিলিটি ট্রি (AT-SPI), ভার্চুয়াল ডিসপ্লে আইসোলেশন (Xvfb) এবং মাউস-কিবোর্ড সিমুলেশনের মাধ্যমে মানুষের মতো যেকোনো কম্পিউটার টাস্ক সম্পাদন করে।

### Workspace Structure & Module Boundaries

| Directory / Module | Role & Responsibility | Tech Stack / Status |
| :--- | :--- | :--- |
| **`apps/core-engine/`** | মূল ব্যাকএন্ড ডেমন, VLM ভিশন ব্রেইন, ওএস অ্যাকশন ড্রাইভার, অডিও ক্যাচার ও লোকাল ভয়েস পাইপলাইন | **Python 3.10+**, AsyncIO, FastAPI, Pydantic, MSS, PyAutoGUI, Xvfb, AT-SPI, Faster-Whisper, Edge-TTS |
| **`apps/companion-mobile/`** | ডেডিকেটেড মোবাইল ক্লায়েন্ট (বাইরে থেকে ফোনে কথা বলা, হ্যান্ডস-ফ্রি ব্লুটুথ ও রিমোট পিসি কন্ট্রোল) | Planned Mobile App (**Flutter** / **React Native**) with WebRTC & Push-to-Talk |
| **`apps/companion-web/`** | লাইটওয়েট ওয়েব ক্লায়েন্ট (যেকোনো ব্রাউজার থেকে পিসি অ্যাক্সেস ইন্টারফেস) | Planned PWA / Lightweight Web Client with WebSocket bridge |
| **`apps/desktop-overlay/`** | লাইভ কো-পাইলট মোডে স্ক্রিনে লেজার পয়েন্টার ও বাউন্ডিং বক্স ভিজ্যুয়াল ফিডব্যাক ওভারলে | Planned PySide6 / Transparent Canvas Overlay (`DISPLAY=:0`) |
| **`packages/`** | শেয়ার্ড ডেটা টাইপ, RPC কন্ট্রাক্ট এবং প্রটোকল ডেফিনিশন | Modular shared schemas & utilities |
| **`docs/`** | কমপ্লিট সিস্টেম আর্কিটেকচার, রোডম্যাপ, স্পেক্স ও টেকনিক্যাল রিসার্চ | Markdown Documentation & Diagrams |
| **`.agents/memory/`** | মাল্টি-পিসি লিভিং মেমোরি সিস্টেম (`HANDOVER.md`, `DECISIONS.md`, `ARCHITECTURE.md`) | Living state, ADRs, & continuous engineering continuity |
| **`.agents/rules/`** | এজেন্টের কঠোর আচরণ ও নিরাপত্তা নীতিমালা (Safety & Dual-Mode Routing) | Markdown Guardrails |
| **`.agents/skills/`** | ওএস অটোমেশন ও ভার্চুয়াল ডিসপ্লের এক্সিকিউটেবল স্কিলস | Procedural Toolchains & Runbooks |
| **`scripts/`** | সিস্টেম ডিপেন্ডেন্সি ইনস্টলার ও ভার্চুয়াল ডিসপ্লে ম্যানেজমেন্ট স্ক্রিপ্টস | Bash utilities (`setup_system_deps.sh`) |
| **`Igris.code-workspace`** | Multi-root IDE workspace configuration | VS Code / Antigravity IDE configuration |

---

## 2. Multi-PC Memory Protocol (MANDATORY)

যেহেতু ব্যবহারকারী যেকোনো সময় বিভিন্ন ওয়ার্কস্টেশন থেকে কাজ করতে পারেন অথবা নতুন সেশনে এজেন্টের সাথে যুক্ত হতে পারেন, তাই সেশনের ধারাবাহিকতা (Continuity) বজায় রাখতে **সকল AI এজেন্টকে অবশ্যই এই প্রোটোকল মেনে চলতে হবে**:

```
+-----------------------------------------------------------------------------+
|                           AI AGENT SESSION LIFECYCLE                         |
|                                                                             |
|  1. SESSION KICKOFF                                                         |
|     Read: .agents/memory/HANDOVER.md                                        |
|     - Understand active sprint, recent progress, and immediate next steps.  |
|                                                                             |
|  2. ARCHITECTURAL GUARDRAILS                                                |
|     Read & Check: .agents/memory/DECISIONS.md & ARCHITECTURE.md             |
|     - Check ADRs before introducing dependencies, APIs, or architectural    |
|       modifications.                                                        |
|                                                                             |
|  3. EXECUTION                                                               |
|     - Follow module-specific guidelines.                                    |
|     - Keep changes minimal, tested, and aligned with conventions.           |
|                                                                             |
|  4. SESSION WRAP-UP                                                         |
|     Update: .agents/memory/HANDOVER.md                                      |
|     - Record completed work, active files, remaining blockers, and next     |
|       immediate tasks. DO NOT autonomously run git add or git commit.      |
+-----------------------------------------------------------------------------+
```

### Protocol Rules:

1. **Session Kickoff (Mandatory Step 1):**
   - যেকোনো সেশনের শুরুতে এজেন্টকে **অবশ্যই `.agents/memory/HANDOVER.md` ফাইলটি দেখতে হবে**।
   - বর্তমানে কোন স্প্রিন্ট বা ফেজ চলছে, শেষ কী কাজ হয়েছে এবং পরবর্তী ইমিডিয়েট কাজ কী তা বুঝে নিতে হবে।
   - আর্কিটেকচারাল কোনো কাজের ক্ষেত্রে `.agents/memory/ARCHITECTURE.md` ও `DECISIONS.md` দেখে নিতে হবে।

2. **Architectural Guardrails (Pre-decision Step):**
   - কোনো নতুন লাইব্রেরি, ফ্রেমওয়ার্ক বা মূল আর্কিটেকচারাল পরিবর্তন করার পূর্বে `.agents/memory/DECISIONS.md` পরীক্ষা করতে হবে যাতে পূর্ববর্তী সিদ্ধান্তের সাথে সাংঘর্ষিক না হয়।
   - নতুন বড় সিদ্ধান্ত গ্রহণ করা হলে একটি নতুন ADR (`ADR-00X`) যুক্ত করতে হবে।

3. **Session Wrap-Up (Mandatory Final Step):**
   - কোনো কাজ শেষ করার পূর্বে এজেন্টকে **অবশ্যই `.agents/memory/HANDOVER.md` আপডেট করতে হবে**।
   - কী কাজ সম্পন্ন হলো, কোন কোন ফাইল এডিট করা হয়েছে এবং পরবর্তী সেশনের জন্য কী কী কাজ বাকি রইল তা লিপিবদ্ধ করতে হবে।
   - **STRICT GIT CONSTRAINT:** ব্যবহারকারীর স্পষ্ট নির্দেশ ব্যতিরেকে এজেন্ট নিজে থেকে কখনো `git add` বা `git commit` চালাবে না। গিট স্টেজিং ও কমিট সবসময় ব্যবহারকারীর সুস্পষ্ট সম্মতিতে হবে।

4. **Universal Language Invariant (MANDATORY):**
   - সমস্ত `implementation_plan.md`, `learning_proposal.md`, ফিচার রোডম্যাপ, ওয়াকথ্রু এবং ইউজার-ফেসিং ডকুমেন্টস ব্যবহারকারীর পর্যালোচনার জন্য **অবশ্যই বাংলায় (Bengali)** লিখতে হবে।
   - কারিগরি স্পষ্টতার জন্য টেকনিক্যাল কি-ওয়ার্ড (যেমন: API, VLM, Terminal, Bash, WebSockets, WebRTC, Git Push, Accessibility Tree ইত্যাদি) মূল ইংরেজি বানানে অপরিবর্তিত থাকবে।

---

## 3. Adaptive Learning & Proactive Architecture Directive

এজেন্টকে কেবল প্যাসিভ টাস্ক এক্সিকিউটর হিসেবে নয়, বরং একজন প্রো-অ্যাক্টিভ সিনিয়র সফটওয়্যার আর্কিটেক্ট ও পার্টনার হিসেবে কাজ করতে হবে:

1. **প্রো-অ্যাক্টিভলি উন্নত বিকল্প প্রস্তাব করা:**
   - কোনো কাজের সবচেয়ে অপ্টিমাইজড, নিরাপদ ও ক্লিন আর্কিটেকচারাল পথটি ব্যবহারকারীকে কোড করার আগেই তুলে ধরতে হবে।
2. **অটোনোমাস মেমোরি মেইনটেন্যান্স:**
   - চলমান প্রজেক্টের যেকোনো গুরুত্বপূর্ণ সিদ্ধান্ত ও অগ্রগতির সাথে সাথে `.agents/memory/DECISIONS.md` ও `HANDOVER.md` স্বয়ংক্রিয়ভাবে সিঙ্ক রাখবে।
3. **জিরো মাইক্রোম্যানেজমেন্ট (Contextual Adaptation):**
   - লিনাক্স সিস্টেম, ভার্চুয়াল ফ্রেমবাফার ও মাল্টিমোডাল ভিশনের কনটেক্সট বুঝে নিয়ে স্বয়ংক্রিয়ভাবে এন্ড-টু-এন্ড সমাধান প্রস্তুত করবে।

---

## 4. Dual-Mode Execution & Safety Protocols

1. **লাইভ কো-পাইলট মোড (`DISPLAY=:0`):**
   - ব্যবহারকারীর চোখের সামনে কাজ করবে।
   - ব্যবহারকারী ফিজিক্যাল মাউস ১০ পিক্সেলের বেশি সরালে বা `Escape` কি চাপলে এজেন্ট তৎক্ষণাৎ মাউস ছেড়ে দিয়ে থেমে যাবে (`Emergency Override`)।
2. **ঘোস্ট মোড (`DISPLAY=:99` via Xvfb):**
   - ব্যবহারকারীর ব্যাকগ্রাউন্ডে অদৃশ্য স্ক্রিনে কাজ করবে।
   - ব্যবহারকারীর মূল স্ক্রিনে কোনো পপ-আপ বা মাউস ইন্টারাপশন ঘটাবে না।
3. **ধ্বংসাত্মক কমান্ডের সুরক্ষা:**
   - ফাইল পার্মানেন্ট ডিলিট, ওএস কনফিগারেশন পরিবর্তন বা সরাসরি মেইন ব্রাঞ্চে গিট পুশের পূর্বে অবশ্যই মৌখিক বা টেক্সট কনফার্মেশন গ্রহণ করবে।
