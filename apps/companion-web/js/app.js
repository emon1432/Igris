// Igris Mobile & Remote Companion Web App Client

document.addEventListener("DOMContentLoaded", () => {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.host || "localhost:8000";
    const wsUrl = `${wsProtocol}//${wsHost}/ws/companion`;

    let socket = null;
    let isConnected = false;
    let isRecording = false;
    let mediaRecorder = null;
    let audioChunks = [];

    // DOM Elements
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const modeBadge = document.getElementById("mode-badge");
    const modeSelect = document.getElementById("mode-select");
    const liveScreen = document.getElementById("live-screen");
    const screenPlaceholder = document.getElementById("screen-placeholder");
    const refreshScreenBtn = document.getElementById("refresh-screen-btn");
    const logStream = document.getElementById("log-stream");
    const stepCounter = document.getElementById("step-counter");
    const commandInput = document.getElementById("command-input");
    const sendBtn = document.getElementById("send-btn");
    const pttBtn = document.getElementById("ptt-btn");
    const emergencyBtn = document.getElementById("emergency-btn");

    function addLog(msg, type = "info") {
        const now = new Date();
        const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`;
        const entry = document.createElement("div");
        entry.className = `log-entry ${type}`;
        entry.innerHTML = `<span class="time">${timeStr}</span><span class="msg">${msg}</span>`;
        logStream.appendChild(entry);
        logStream.scrollTop = logStream.scrollHeight;
    }

    function updateScreenPreview() {
        const previewUrl = `/api/screen/preview?t=${Date.now()}`;
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

    // Connect WebSocket
    function connect() {
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            isConnected = true;
            statusDot.className = "status-dot connected";
            statusText.textContent = "Online";
            addLog("Connected to Igris Gateway.", "success");

            // Send Auth Request
            socket.send(JSON.stringify({
                type: "auth_request",
                payload: {
                    token: "igris-secure-token",
                    client_id: "mobile-pwa",
                    device_type: "mobile"
                }
            }));

            updateScreenPreview();
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
            statusText.textContent = "Offline";
            addLog("Disconnected from server. Retrying in 3s...", "error");
            setTimeout(connect, 3000);
        };

        socket.onerror = (err) => {
            console.error("WebSocket error:", err);
        };
    }

    function handleMessage(msg) {
        switch (msg.type) {
            case "auth_response":
                if (msg.payload.authenticated) {
                    addLog("Authentication verified.", "success");
                } else {
                    addLog("Auth failed: " + msg.payload.message, "error");
                }
                break;

            case "task_update":
                stepCounter.textContent = `Step ${msg.payload.step_number || 1}`;
                addLog(`[${msg.payload.action_type}] ${msg.payload.thought}`);
                updateScreenPreview();
                break;

            case "task_completed":
                stepCounter.textContent = "Finished";
                if (msg.payload.success) {
                    addLog(`Task Completed: ${msg.payload.final_message}`, "success");
                } else {
                    addLog(`Task Terminated: ${msg.payload.final_message}`, "error");
                }
                updateScreenPreview();
                break;

            case "emergency_stop":
                stepCounter.textContent = "HALTED";
                addLog(`EMERGENCY BRAKE TRIPPED: ${msg.payload.reason}`, "error");
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                updateScreenPreview();
                break;

            case "screen_frame":
                if (msg.payload.frame_b64) {
                    liveScreen.src = `data:image/jpeg;base64,${msg.payload.frame_b64}`;
                    liveScreen.style.display = "block";
                    screenPlaceholder.style.display = "none";
                }
                break;

            case "error":
                addLog(`Error: ${msg.payload.error}`, "error");
                break;
        }
    }

    function sendTaskCommand(goalText) {
        if (!goalText || !isConnected) return;
        const mode = modeSelect.value;
        modeBadge.textContent = mode.toUpperCase();

        addLog(`Submitting Task: "${goalText}" (${mode.toUpperCase()})`, "info");
        stepCounter.textContent = "Starting";

        socket.send(JSON.stringify({
            type: "task_command",
            payload: {
                task_goal: goalText,
                mode: mode,
                max_iterations: 15
            }
        }));

        commandInput.value = "";
    }

    // Event Listeners
    sendBtn.addEventListener("click", () => sendTaskCommand(commandInput.value.trim()));
    commandInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") sendTaskCommand(commandInput.value.trim());
    });

    modeSelect.addEventListener("change", () => {
        modeBadge.textContent = modeSelect.value.toUpperCase();
    });

    refreshScreenBtn.addEventListener("click", updateScreenPreview);

    // Emergency Stop Button
    emergencyBtn.addEventListener("click", async () => {
        addLog("Tripping Emergency Stop!", "error");
        if (navigator.vibrate) {
            navigator.vibrate(300);
        }
        if (isConnected && socket) {
            socket.send(JSON.stringify({
                type: "emergency_stop",
                payload: {
                    source: "companion_pwa_button",
                    reason: "Emergency Stop triggered from Mobile UI"
                }
            }));
        } else {
            // Fallback to REST endpoint
            try {
                await fetch("/api/emergency/stop", { method: "POST" });
            } catch (err) {
                console.error("Emergency stop failed:", err);
            }
        }
    });

    // Push to Talk (PTT) Handler
    pttBtn.addEventListener("click", async () => {
        if (!isRecording) {
            // Start recording
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                audioChunks = [];

                mediaRecorder.ondataavailable = (e) => {
                    if (e.data.size > 0) audioChunks.push(e.data);
                };

                mediaRecorder.onstop = async () => {
                    const audioBlob = new Blob(audioChunks, { type: "audio/webm" });
                    addLog("Voice audio recorded. Processing command...", "info");
                    // Can post audioBlob to STT endpoint or transcribe locally
                };

                mediaRecorder.start();
                isRecording = true;
                pttBtn.classList.add("recording");
                addLog("Listening to microphone...", "info");
            } catch (err) {
                addLog("Microphone access denied: " + err.message, "error");
            }
        } else {
            // Stop recording
            if (mediaRecorder && mediaRecorder.state !== "inactive") {
                mediaRecorder.stop();
                mediaRecorder.stream.getTracks().forEach(track => track.stop());
            }
            isRecording = false;
            pttBtn.classList.remove("recording");
        }
    });

    // Initial connection
    connect();
    setInterval(updateScreenPreview, 5000);
});

