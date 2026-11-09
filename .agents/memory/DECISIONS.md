# Architecture Decision Records (`DECISIONS.md`)

> **Protocol Rule:** Before introducing new architectural patterns, external frameworks/libraries, or API schema changes, consult this record. When proposing significant architectural changes, record a new decision below.

---

## Decision Index

| ID | Title | Date | Status | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **ADR-001** | [Autonomous OS Operator Paradigm over Application-Specific APIs](#adr-001-autonomous-os-operator-paradigm-over-application-specific-apis) | 2026-11-10 | **Accepted** | Core Architecture / Brain |
| **ADR-002** | [Living Memory & Multi-PC Continuity Protocol](#adr-002-living-memory--multi-pc-continuity-protocol) | 2026-11-10 | **Accepted** | Entire Repository / `.agents` |
| **ADR-003** | [Dual-Mode Execution Model: Live Co-Pilot vs. Ghost Virtual Lab](#adr-003-dual-mode-execution-model-live-co-pilot-vs-ghost-virtual-lab) | 2026-11-10 | **Accepted** | OS Automation & Display |
| **ADR-004** | [Multi-App Monorepo Workspace Architecture](#adr-004-multi-app-monorepo-workspace-architecture) | 2026-11-10 | **Accepted** | Repository Layout |
| **ADR-005** | [Hybrid Perception Strategy: VLM Spatial Vision & Linux AT-SPI Tree](#adr-005-hybrid-perception-strategy-vlm-spatial-vision--linux-at-spi-tree) | 2026-11-10 | **Accepted** | Perception Layer |
| **ADR-006** | [Universal Language Invariant for Documentation & Plans](#adr-006-universal-language-invariant-for-documentation--plans) | 2026-11-10 | **Accepted** | Communication & Docs |

---

## ADR-001: Autonomous OS Operator Paradigm over Application-Specific APIs

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
একটি পূর্ণাঙ্গ ডিজিটাল অ্যাসিস্ট্যান্টের জন্য প্রতিটি অ্যাপের (যেমন: WhatsApp, Gmail, Zoom, Photoshop, VS Code) আলাদা আলাদা API ইন্টিগ্রেশন তৈরি করা অবাস্তব এবং রক্ষণাবেক্ষণ অত্যন্ত জটিল। কোনো থার্ড পার্টি প্ল্যাটফর্ম তাদের API পরিবর্তন করলে সিস্টেম ভেঙে পড়তে পারে।

### Decision
Igris নির্দিষ্ট কোনো অ্যাপ্লিকেশনের API-এর ওপর নির্ভরশীল হবে না। বরং একজন মানুষের মতো কম্পিউটার অপারেট করার ক্ষমতা (Universal Autonomous OS Operator / Computer Use) অর্জন করবে:
1. স্ক্রিনের ভিজ্যুয়াল ও UI উপাদান অনুধাবন করা।
2. মাউস মুভমেন্ট, ক্লিক, ড্র্যাগ এবং কিবোর্ড টাইপিংয়ের মাধ্যমে যেকোনো GUI অ্যাপ অপারেট করা।
3. ব্যাকগ্রাউন্ড ফাইল ও ডেভেলপার টাস্কের জন্য Terminal / Bash শেল কমান্ড সরাসরি এক্সিকিউট করা।

### Consequences
- **ইতিবাচক:** নতুন যেকোনো সফটওয়্যার ও সাইটের জন্য কোনো নতুন কোড ছাড়াই Igris কাজ করতে পারবে।
- **নেতিবাচক:** স্ক্রিন রিকগনিশন ও কো-অর্ডিনেট ম্যাপিংয়ে সামান্য লেটেন্সি থাকতে পারে, যা অপ্টিমাইজড VLM ক্যাশিং এবং AT-SPI বাস দিয়ে সমাধান করা হবে।

---

## ADR-002: Living Memory & Multi-PC Continuity Protocol

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
ডেভেলপমেন্ট প্রক্রিয়া চলাকালীন সেশন শেষ হওয়া বা একাধিক পিসি থেকে কাজ করার কারণে কনটেক্সট হারিয়ে যাওয়ার ঝুঁকি থাকে। নতুন সেশনে এজেন্টকে পুনরায় সব ব্যাখ্যা করতে হলে সময় নষ্ট হয়।

### Decision
প্রজেক্টে একটি স্বয়ংক্রিয় **Living Memory Protocol** প্রতিষ্ঠা করা হয়েছে:
1. প্রতি সেশনের শুরুতে এজেন্ট `.agents/memory/HANDOVER.md`, `DECISIONS.md` এবং `ARCHITECTURE.md` পড়ে কনটেক্সট গ্রহণ করবে।
2. সেশন শেষে অবশ্যই `HANDOVER.md` ফাইলে কাজের অগ্রগতি ও পরবর্তী ধাপ লিপিবদ্ধ করবে।
3. ব্যবহারকারীর স্পষ্ট নির্দেশ ছাড়া এজেন্ট নিজে থেকে `git commit` চালাবে না।

---

## ADR-003: Dual-Mode Execution Model: Live Co-Pilot vs. Ghost Virtual Lab

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
সাধারণ GUI অটোমেশন সিস্টেমে মাউস কার্সর নড়াচড়া করায় ব্যবহারকারী যখন ভিডিও দেখছেন বা কোডিং করছেন তখন কনফ্লিক্ট তৈরি হয়। আবার ক্রিয়েটিভ কাজের সময় ব্যবহারকারী চান এজেন্ট তার চোখের সামনে লাইভ কাজ করুক।

### Decision
Igris দুটি স্বতন্ত্র মোডে কাজ করবে:
1. **লাইভ কো-পাইলট মোড (`DISPLAY=:0`):** ব্যবহারকারীর অ্যাক্টিভ স্ক্রিনে কাজ করবে। ইমার্জেন্সি ওভাররাইড হিসেবে ব্যবহারকারী মাউস নাড়ালে তাৎক্ষণিকভাবে কন্ট্রোল ব্যবহারকারীকে ফিরিয়ে দেবে।
2. **ঘোস্ট মোড (`DISPLAY=:99` via Xvfb):** সম্পূর্ণ অদৃশ্য ভার্চুয়াল স্ক্রিনে ব্যাকগ্রাউন্ডে কাজ করবে। ব্যবহারকারীর মূল স্ক্রিন সম্পূর্ণ ইন্টারাপশন-মুক্ত থাকবে।

---

## ADR-004: Multi-App Monorepo Workspace Architecture

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
Igris-এর ভবিষ্যৎ পরিধি বিশাল: এতে একটি ব্যাকএন্ড ইঞ্জিন, একটি লাইভ ভিজ্যুয়াল HUD ওভারলে, এবং বাইরে থেকে ব্যবহারের জন্য একটি মোবাইল রিমোট ক্লায়েন্ট রয়েছে। এগুলোকে একটি সিঙ্গেল ফোল্ডার স্ক্রিপ্টে রাখলে ভবিষ্যতে আর্কিটেকচারাল জট তৈরি হবে।

### Decision
প্রজেক্টটিকে একটি পরিষ্কার Multi-App Monorepo কাঠামোয় সাজানো হয়েছে:
- `apps/core-engine/`: পাইথন ব্যাকএন্ড ডেমন, VLM ও ওএস ড্রাইভার।
- `apps/companion-web/`: মোবাইল রিমোট ক্লায়েন্ট (PWA / WebRTC)।
- `apps/desktop-overlay/`: লাইভ স্ক্রিন লেজার HUD ওভারলে।
- `packages/`: শেয়ার্ড প্রটোকল ও স্কিমা।
- `docs/`: গভীর প্রযুক্তিগত ডকুমেন্টেশন।

---

## ADR-005: Hybrid Perception Strategy: VLM Spatial Vision & Linux AT-SPI Tree

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
শুধুমাত্র স্ক্রিনশট ও VLM দিয়ে বাটন শনাক্ত করলে রেজোলিউশন স্কেলিং ও ড্রিপটের কারণে ২-৫ পিক্সেল মিসক্লিক হতে পারে।

### Decision
একটি হাইব্রিড পারসেপশন স্ট্যাক ব্যবহার করা হবে:
1. **ম্যাক্রো ভিশন:** VLM পুরো স্ক্রিনের লেআউট এবং উইন্ডো স্টেট শনাক্ত করবে।
2. **মাইক্রো প্রিসিশন:** লিনাক্স AT-SPI Accessibility বাস থেকে বাটনের এক্সাক্ট বাউন্ডিং বক্স `(x, y, w, h)` বের করে ১০০% নির্ভুল জায়গায় ক্লিক নিশ্চিত করা হবে।

---

## ADR-006: Universal Language Invariant for Documentation & Plans

### Status
**Accepted** (2026-11-10)

### Context & Problem Statement
ব্যবহারকারী নির্দেশ দিয়েছেন যে সকল প্ল্যানিং, ডকুমেন্টেশন ও কনভারসেশন বাংলায় হতে হবে, তবে টেকনিক্যাল স্পষ্টতার জন্য কিওয়ার্ড ইংরেজি থাকবে।

### Decision
প্রজেক্টের সকল `implementation_plan.md`, `HANDOVER.md`, `ARCHITECTURE.md` এবং আর্কিটেকচারাল ডকুমেন্টেশন বাংলায় প্রস্তুত করা হবে। কেবল Technical Keywords (যেমন: API, VLM, Terminal, Bash, WebSockets, Git ইত্যাদি) মানসম্মত ইংরেজি বানানে অক্ষত থাকবে।
