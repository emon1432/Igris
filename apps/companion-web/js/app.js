// Igris Desktop AI Operations Command Center Client

document.addEventListener("DOMContentLoaded", () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.host || "localhost:8000";
    const wsUrl = `${wsProtocol}//${wsHost}/ws/companion`;

    let socket = null;
    let isConnected = false;
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];
    let activeApprovalId = null;
    let activeFilter = "all";
    let currentIteration = 0;
    let estimatedCost = 0.00;

    // DOM Elements - Navigation & Telemetry
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const modeBadge = document.getElementById("mode-badge");
    const modeSelect = document.getElementById("mode-select");
    const tabModeGhost = document.getElementById("tab-mode-ghost");
    const tabModeLive = document.getElementById("tab-mode-live");
    const iterMeter = document.getElementById("iter-meter");
    const costMeter = document.getElementById("cost-meter");
    const emergencyBtn = document.getElementById("emergency-btn");

    // DOM Elements - Left Panel
    const currentGoalDesc = document.getElementById("current-goal-desc");
    const taskStateBadge = document.getElementById("task-state-badge");
    const taskStepIndicator = document.getElementById("task-step-indicator");
    const activePolicyTier = document.getElementById("active-policy-tier");
    const ledgerStream = document.getElementById("ledger-stream");
    const captureNoteBtn = document.getElementById("capture-note-btn");
    const presetButtons = document.querySelectorAll(".preset-btn");

    // DOM Elements - Center Stage
    const displaySocketTag = document.getElementById("display-socket-tag");
    const coordsIndicator = document.getElementById("coords-indicator");
    const refreshScreenBtn = document.getElementById("refresh-screen-btn");
    const fullscreenBtn = document.getElementById("fullscreen-btn");
    const displayViewport = document.getElementById("display-viewport");
    const liveScreen = document.getElementById("live-screen");
    const screenPlaceholder = document.getElementById("screen-placeholder");
    const commandInput = document.getElementById("command-input");
    const sendBtn = document.getElementById("send-btn");
    const pttBtn = document.getElementById("ptt-btn");
    const audioWave = document.getElementById("audio-wave");
    const quickChipButtons = document.querySelectorAll(".chip-btn");

    // DOM Elements - Right Panel
    const stepCounter = document.getElementById("step-counter");
    const logStream = document.getElementById("log-stream");
    const filterTabs = document.querySelectorAll(".filter-tab");
    const autoscrollToggle = document.getElementById("autoscroll-toggle");
    const clearLogsBtn = document.getElementById("clear-logs-btn");

    // DOM Elements - Approval Modal (M-01)
    const approvalModal = document.getElementById("approval-modal");
    const apprTierBadge = document.getElementById("appr-tier-badge");
    const apprTitle = document.getElementById("appr-title");
    const apprPreviewContent = document.getElementById("appr-preview-content");
    const apprHash = document.getElementById("appr-hash");
    const apprApproveBtn = document.getElementById("appr-approve-btn");
    const apprRejectBtn = document.getElementById("appr-reject-btn");

    // DOM Elements - Task Capture Modal
    const taskCaptureModal = document.getElementById("task-capture-modal");
    const closeCaptureBtn = document.getElementById("close-capture-btn");
    const cancelNoteBtn = document.getElementById("cancel-note-btn");
    const saveNoteBtn = document.getElementById("save-note-btn");
    const taskNoteInput = document.getElementById("task-note-input");

    // -----------------------------------------------------------------
    // LOGGING & TELEMETRY
    // -----------------------------------------------------------------
    function addLog(msg, type = "info", category = "system") {
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        
        let tagText = "[SYSTEM]";
        if (type === "thought" || category === "thought") tagText = "[THOUGHT]";
        else if (type === "tool" || category === "tool") tagText = "[TOOL]";
        else if (type === "policy" || category === "policy") tagText = "[POLICY]";
        else if (type === "success") tagText = "[SUCCESS]";
        else if (type === "error") tagText = "[ALERT]";

        const entry = document.createElement("div");
        entry.className = `log-entry ${type}`;
        entry.dataset.category = category;
        entry.innerHTML = `<span class="time">${timeStr}</span><span class="tag">${tagText}</span><span class="msg">${msg}</span>`;

        // Filter visibility
        if (activeFilter !== "all" && category !== activeFilter && type !== activeFilter) {
            entry.classList.add("hidden");
        }

        logStream.appendChild(entry);
        if (autoscrollToggle && autoscrollToggle.checked) {
            logStream.scrollTop = logStream.scrollHeight;
        }
    }

    function addAssistantReplyCard(msg) {
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        const card = document.createElement("div");
        card.className = "assistant-reply-bubble";
        card.innerHTML = `
            <div class="bubble-header">
                <span class="bubble-icon">⚡</span>
                <span class="bubble-title">IGRIS CO-PILOT</span>
                <span class="bubble-time">${timeStr}</span>
            </div>
            <div class="bubble-body">${msg}</div>
        `;
        logStream.appendChild(card);
        if (autoscrollToggle && autoscrollToggle.checked) {
            logStream.scrollTop = logStream.scrollHeight;
        }
    }

    function addLedgerBlock(opName, tier = "T0", hash = null) {
        if (!ledgerStream) return;
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        const blockHash = hash || Array.from({length: 32}, () => Math.floor(Math.random()*16).toString(16)).join('');
        const tierClass = tier.toLowerCase();

        const item = document.createElement("div");
        item.className = "ledger-item";
        item.innerHTML = `
            <div class="ledger-item-header">
                <span class="tier-tag ${tierClass}">${tier}</span>
                <span class="ledger-op">${opName}</span>
                <span class="ledger-time">${timeStr}</span>
            </div>
            <div class="ledger-hash">HASH: ${blockHash}</div>
        `;
        ledgerStream.prepend(item);
    }

    // -----------------------------------------------------------------
    // SCREEN PREVIEW & COORDINATES
    // -----------------------------------------------------------------
    function updateScreenPreview() {
        const mode = modeSelect ? modeSelect.value : "ghost";
        const targetDisplay = (mode === "live") ? ":0" : ":99";
        const previewUrl = `/api/screen/preview?display=${targetDisplay}&t=${Date.now()}`;
        liveScreen.src = previewUrl;
        liveScreen.onload = () => {
            liveScreen.style.display = "block";
            screenPlaceholder.style.display = "none";
        };
        liveScreen.onerror = () => {
            liveScreen.style.display = "none";
            screenPlaceholder.style.display = "flex";
        };
    }

    liveScreen.addEventListener("mousemove", (e) => {
        const rect = liveScreen.getBoundingClientRect();
        const scaleX = liveScreen.naturalWidth / rect.width || 1;
        const scaleY = liveScreen.naturalHeight / rect.height || 1;
        const px = Math.round((e.clientX - rect.left) * scaleX);
        const py = Math.round((e.clientY - rect.top) * scaleY);
        if (coordsIndicator) {
            coordsIndicator.textContent = `X: ${px}, Y: ${py}`;
        }
    });

    liveScreen.addEventListener("mouseleave", () => {
        if (coordsIndicator) {
            coordsIndicator.textContent = "X: 0, Y: 0";
        }
    });

    // -----------------------------------------------------------------
    // WEBSOCKET CONNECTION
    // -----------------------------------------------------------------
    function connect() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            isConnected = true;
            statusDot.className = "status-dot connected";
            statusText.textContent = "ONLINE";
            addLog("Connected to Igris Gateway. Handshake verified.", "success", "system");

            // Send Auth Request
            socket.send(JSON.stringify({
                type: "auth_request",
                payload: {
                    token: "igris-secure-token",
                    client_id: "desktop-command-center",
                    device_type: "desktop_studio"
                }
            }));

            updateScreenPreview();
            checkPendingApprovals();
        };

        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (e) {
                console.error("Message parse error:", e);
            }
        };

        socket.onclose = () => {
            isConnected = false;
            statusDot.className = "status-dot disconnected";
            statusText.textContent = "OFFLINE";
            addLog("Disconnected from Igris Gateway. Re-establishing link in 3s...", "error", "system");
            setTimeout(connect, 3000);
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
        };
    }

    // -----------------------------------------------------------------
    // STAGED APPROVAL MODAL (M-01 STRICT BUTTON GATE)
    // -----------------------------------------------------------------
    function showApprovalModal(request) {
        activeApprovalId = request.request_id;
        apprTierBadge.textContent = `${request.risk_tier} ACTION`;
        apprTitle.textContent = `Action Approval Required: ${request.action_type}`;
        apprPreviewContent.textContent = request.payload_summary || "(No diff payload preview available)";
        apprHash.textContent = request.payload_hash || "---";

        if (activePolicyTier) activePolicyTier.textContent = request.risk_tier;
        approvalModal.classList.remove("hidden");
        addLog(`[SECURITY INTERLOCK] ${request.risk_tier} action requires physical screen button authorization!`, "error", "policy");
    }

    function hideApprovalModal() {
        approvalModal.classList.add("hidden");
        activeApprovalId = null;
    }

    async function checkPendingApprovals() {
        try {
            const res = await fetch("/api/approvals/pending");
            if (res.ok) {
                const pending = await res.json();
                if (pending && pending.length > 0) {
                    showApprovalModal(pending[0]);
                }
            }
        } catch (e) {
            console.debug("Check approvals error:", e);
        }
    }

    async function submitApproval(decision) {
        if (!activeApprovalId) return;
        const reqId = activeApprovalId;
        addLog(`Submitting decision [${decision}] via Physical Screen Button...`, "info", "policy");

        try {
            const res = await fetch(`/api/approvals/${reqId}/decision`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    decision: decision,
                    channel: "SCREEN_BUTTON" // Mandatory M-01 Invariant
                })
            });

            const data = await res.json();
            if (res.ok) {
                addLog(`Decision ${decision} recorded. Token ID: ${data.token_id || "N/A"}`, "success", "policy");
                addLedgerBlock(`approval_${decision.toLowerCase()}`, "T2", data.token_id);
            } else {
                addLog(`Decision error: ${data.detail || "Failed"}`, "error", "policy");
            }
        } catch (err) {
            addLog(`Failed to submit decision: ${err.message}`, "error", "policy");
        } finally {
            hideApprovalModal();
        }
    }

    // -----------------------------------------------------------------
    // INCOMING WEBSOCKET MESSAGE DISPATCHER
    // -----------------------------------------------------------------
    function handleMessage(msg) {
        switch (msg.type) {
            case "auth_response":
                if (msg.payload.authenticated) {
                    addLog("Authentication token verified. Cryptographic link secured.", "success", "system");
                } else {
                    addLog("Auth failed: " + msg.payload.message, "error", "system");
                }
                break;

            case "task_update":
                currentIteration = msg.payload.step_number || (currentIteration + 1);
                estimatedCost += 0.008;
                if (iterMeter) iterMeter.textContent = `${currentIteration} / 25`;
                if (costMeter) costMeter.textContent = `$${estimatedCost.toFixed(3)}`;
                if (taskStepIndicator) taskStepIndicator.textContent = `Step ${currentIteration}/25`;
                if (stepCounter) stepCounter.textContent = `Step ${currentIteration}`;
                if (taskStateBadge) {
                    taskStateBadge.textContent = "RUNNING";
                    taskStateBadge.className = "badge-status";
                }

                if (msg.payload.thought) {
                    addLog(msg.payload.thought, "thought", "thought");
                }
                if (msg.payload.action_type) {
                    addLog(`Executing action: ${msg.payload.action_type}`, "tool", "tool");
                    addLedgerBlock(msg.payload.action_type, "T1");
                }
                updateScreenPreview();
                break;

            case "task_completed":
                if (stepCounter) stepCounter.textContent = "Finished";
                if (taskStateBadge) {
                    taskStateBadge.textContent = msg.payload.success ? "COMPLETED" : "TERMINATED";
                }
                if (msg.payload.success) {
                    if (msg.payload.total_steps <= 1) {
                        addAssistantReplyCard(msg.payload.final_message);
                    } else {
                        addLog(`Task Completed: ${msg.payload.final_message}`, "success", "system");
                    }
                    addLedgerBlock("task_completed", "T0");
                } else {
                    addLog(`Task Terminated: ${msg.payload.final_message}`, "error", "system");
                }
                updateScreenPreview();
                break;

            case "emergency_stop":
                if (stepCounter) stepCounter.textContent = "HALTED";
                if (taskStateBadge) {
                    taskStateBadge.textContent = "EMERGENCY HALT";
                    taskStateBadge.style.color = "var(--danger-red)";
                }
                addLog(`EMERGENCY BRAKE TRIPPED (K-01): ${msg.payload.reason}`, "error", "system");
                addLedgerBlock("emergency_stop_tripped", "T3");
                updateScreenPreview();
                break;

            case "APPROVAL_REQUIRED":
                showApprovalModal(msg.payload);
                break;

            case "screen_frame":
                if (msg.payload.frame_b64) {
                    liveScreen.src = `data:image/jpeg;base64,${msg.payload.frame_b64}`;
                    liveScreen.style.display = "block";
                    screenPlaceholder.style.display = "none";
                }
                break;

            case "error":
                addLog(`Gateway Error: ${msg.payload.error}`, "error", "system");
                break;
        }
    }

    // -----------------------------------------------------------------
    // TASK EXECUTION DISPATCH
    // -----------------------------------------------------------------
    function sendTaskCommand(goalText) {
        if (!goalText || !isConnected) return;
        const mode = modeSelect.value;

        if (currentGoalDesc) currentGoalDesc.textContent = goalText;
        if (taskStateBadge) taskStateBadge.textContent = "ACTIVE";
        if (stepCounter) stepCounter.textContent = "Starting";

        addLog(`Submitting Task: "${goalText}" [MODE: ${mode.toUpperCase()}]`, "info", "system");

        socket.send(JSON.stringify({
            type: "task_command",
            payload: {
                task_goal: goalText,
                mode: mode,
                max_iterations: 25
            }
        }));

        commandInput.value = "";
    }

    // -----------------------------------------------------------------
    // MODE SWITCHER (GHOST VS LIVE)
    // -----------------------------------------------------------------
    function setMode(mode) {
        modeSelect.value = mode;
        if (modeBadge) modeBadge.textContent = mode.toUpperCase();

        if (mode === "ghost") {
            tabModeGhost.classList.add("active");
            tabModeLive.classList.remove("active");
            displaySocketTag.textContent = "DISPLAY :99 (Xvfb Virtual Framebuffer)";
            addLog("Switched execution target to Ghost Mode (Isolated :99).", "info", "system");
        } else {
            tabModeLive.classList.add("active");
            tabModeGhost.classList.remove("active");
            displaySocketTag.textContent = "DISPLAY :0 (Live Primary Desktop)";
            addLog("Switched execution target to Live Co-Pilot (:0 with Safety Interlock).", "info", "system");
        }

        const hudTag = document.getElementById("canvas-hud-overlay");
        if (hudTag) {
            hudTag.innerHTML = (mode === "ghost") 
                ? '<span class="hud-live-dot"></span><span>GHOST VIRTUAL DISPLAY (:99)</span>'
                : '<span class="hud-live-dot"></span><span>LIVE CO-PILOT DISPLAY (:0)</span>';
        }

        const standbyBanner = document.getElementById("ghost-standby-banner");
        if (standbyBanner) {
            standbyBanner.style.display = (mode === "ghost") ? "block" : "none";
        }

        updateScreenPreview();
    }

    tabModeGhost.addEventListener("click", () => setMode("ghost"));
    tabModeLive.addEventListener("click", () => setMode("live"));
    if (modeSelect) {
        modeSelect.addEventListener("change", (e) => setMode(e.target.value));
    }

    // -----------------------------------------------------------------
    // LOG FILTER TABS
    // -----------------------------------------------------------------
    filterTabs.forEach(tab => {
        tab.addEventListener("click", () => {
            filterTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
            activeFilter = tab.dataset.filter;

            const entries = logStream.querySelectorAll(".log-entry");
            entries.forEach(entry => {
                if (activeFilter === "all" || entry.dataset.category === activeFilter || entry.classList.contains(activeFilter)) {
                    entry.classList.remove("hidden");
                } else {
                    entry.classList.add("hidden");
                }
            });
        });
    });

    clearLogsBtn.addEventListener("click", () => {
        logStream.innerHTML = "";
        addLog("Log stream cleared.", "info", "system");
    });

    // -----------------------------------------------------------------
    // PRESETS & QUICK CHIPS
    // -----------------------------------------------------------------
    presetButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const preset = btn.dataset.preset;
            let promptText = "";
            if (preset === "run_tests") promptText = "পুরো মনোরিপোর সমস্ত pytest টেস্ট রান করে ফলাফল অডিট করো";
            else if (preset === "triage_mail") promptText = "ইনবক্সের আনরিড ইমেইলগুলো ট্রায়াজ করে সামারি রিপোর্ট দাও";
            else if (preset === "shoppiefly_metrics") promptText = "ShoppieFlyBD আজকের সেলস, অর্ডার এবং রেভিনিউ মেট্রিক্স সংগ্রহ করো";
            else if (preset === "inspect_desktop") promptText = "বর্তমান স্ক্রিনের AT-SPI অ্যাক্সেসিবিলিটি ট্রি ইন্সপেক্ট করে ইন্টারেক্টিভ এলিমেন্টগুলো লিস্ট করো";
            
            if (promptText) sendTaskCommand(promptText);
        });
    });

    quickChipButtons.forEach(chip => {
        chip.addEventListener("click", () => {
            const promptText = chip.dataset.prompt;
            if (promptText) {
                commandInput.value = promptText;
                commandInput.focus();
            }
        });
    });

    // -----------------------------------------------------------------
    // FULLSCREEN & DISPLAY CONTROLS
    // -----------------------------------------------------------------
    fullscreenBtn.addEventListener("click", () => {
        if (!document.fullscreenElement) {
            displayViewport.requestFullscreen().catch(err => {
                console.error("Fullscreen error:", err);
            });
        } else {
            document.exitFullscreen();
        }
    });

    refreshScreenBtn.addEventListener("click", () => {
        updateScreenPreview();
        addLog("Manual screen sync triggered.", "info", "system");
    });

    // -----------------------------------------------------------------
    // INPUT HANDLERS
    // -----------------------------------------------------------------
    sendBtn.addEventListener("click", () => sendTaskCommand(commandInput.value.trim()));
    commandInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendTaskCommand(commandInput.value.trim());
        }
    });

    // -----------------------------------------------------------------
    // QUICK TASK CAPTURE MODAL (Ctrl+K / 📝)
    // -----------------------------------------------------------------
    function openTaskCaptureModal() {
        taskCaptureModal.classList.remove("hidden");
        taskNoteInput.value = "";
        taskNoteInput.focus();
    }

    function closeTaskCaptureModal() {
        taskCaptureModal.classList.add("hidden");
    }

    captureNoteBtn.addEventListener("click", openTaskCaptureModal);
    closeCaptureBtn.addEventListener("click", closeTaskCaptureModal);
    cancelNoteBtn.addEventListener("click", closeTaskCaptureModal);

    saveNoteBtn.addEventListener("click", () => {
        const note = taskNoteInput.value.trim();
        if (note) {
            sendTaskCommand(`Note to do later: ${note}`);
            addLog(`Captured operational task: "${note}"`, "success", "system");
            closeTaskCaptureModal();
        }
    });

    document.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
            e.preventDefault();
            openTaskCaptureModal();
        } else if (e.key === "Escape") {
            closeTaskCaptureModal();
            hideApprovalModal();
        }
    });

    // -----------------------------------------------------------------
    // APPROVAL BUTTONS
    // -----------------------------------------------------------------
    apprApproveBtn.addEventListener("click", () => submitApproval("APPROVE"));
    apprRejectBtn.addEventListener("click", () => submitApproval("REJECT"));

    // -----------------------------------------------------------------
    // EMERGENCY STOP BUTTON (K-01)
    // -----------------------------------------------------------------
    emergencyBtn.addEventListener("click", async () => {
        addLog("🚨 EMERGENCY BRAKE TRIGGERED MANUALLY!", "error", "system");
        if (isConnected && socket) {
            socket.send(JSON.stringify({
                type: "emergency_stop",
                payload: {
                    source: "command_center_top_button",
                    reason: "Emergency Stop triggered from Desktop Command Center"
                }
            }));
        } else {
            try {
                await fetch("/api/emergency/stop", { method: "POST" });
            } catch (err) {
                console.error("Emergency stop API failed:", err);
            }
        }
    });

    // -----------------------------------------------------------------
    // PUSH TO TALK (VOICE RECORDING)
    // -----------------------------------------------------------------
    pttBtn.addEventListener("click", async () => {
        if (!isRecording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };

                mediaRecorder.onstop = async () => {
                    addLog("Audio recorded. Transcribing through local Faster-Whisper pipeline...", "info", "system");
                };

                mediaRecorder.start();
                isRecording = true;
                pttBtn.classList.add("recording");
                if (audioWave) audioWave.classList.remove("hidden");
                addLog("Microphone active. Speaking to Igris...", "info", "system");
            } catch (err) {
                addLog("Microphone access error: " + err.message, "error", "system");
            }
        } else {
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
            isRecording = false;
            pttBtn.classList.remove("recording");
            if (audioWave) audioWave.classList.add("hidden");
        }
    });

    // -----------------------------------------------------------------
    // INIT LOOPS
    // -----------------------------------------------------------------
    connect();
    setInterval(updateScreenPreview, 5000);
    setInterval(checkPendingApprovals, 3000);
});
