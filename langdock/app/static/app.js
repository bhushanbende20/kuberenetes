document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const tabChatBtn = document.getElementById("tabChatBtn");
  const tabLangdockBtn = document.getElementById("tabLangdockBtn");
  const tabApiDocsBtn = document.getElementById("tabApiDocsBtn");

  const chatView = document.getElementById("chatView");
  const langdockView = document.getElementById("langdockView");
  const apiDocsView = document.getElementById("apiDocsView");

  const healthDot = document.getElementById("healthDot");
  const healthStatus = document.getElementById("healthStatus");
  const connectionBadge = document.getElementById("connectionBadge");
  const ollamaHost = document.getElementById("ollamaHost");
  const modelSelect = document.getElementById("modelSelect");
  const tempSlider = document.getElementById("tempSlider");
  const tempValue = document.getElementById("tempValue");
  const systemPrompt = document.getElementById("systemPrompt");

  const chatContainer = document.getElementById("chatContainer");
  const welcomeCard = document.getElementById("welcomeCard");
  const chatForm = document.getElementById("chatForm");
  const messageInput = document.getElementById("messageInput");
  const sendBtn = document.getElementById("sendBtn");
  const clearChatBtn = document.getElementById("clearChatBtn");
  const speedMetric = document.getElementById("speedMetric");

  const langdockBaseUrl = document.getElementById("langdockBaseUrl");
  const testHandshakeBtn = document.getElementById("testHandshakeBtn");
  const testResultBox = document.getElementById("testResultBox");
  const testResultBadge = document.getElementById("testResultBadge");
  const testResultLatency = document.getElementById("testResultLatency");
  const testResultOutput = document.getElementById("testResultOutput");

  const mobileToggle = document.getElementById("mobileToggle");
  const sidebar = document.getElementById("sidebar");

  let conversationHistory = [];
  let isGenerating = false;

  // Set default dynamic base URL
  if (langdockBaseUrl) {
    langdockBaseUrl.value = window.location.origin;
  }

  // Mobile sidebar toggle
  if (mobileToggle) {
    mobileToggle.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });
  }

  // Tab switching
  function switchTab(activeBtn, activeView, title) {
    [tabChatBtn, tabLangdockBtn, tabApiDocsBtn].forEach(b => b.classList.remove("active"));
    [chatView, langdockView, apiDocsView].forEach(v => v.classList.remove("active"));
    activeBtn.classList.add("active");
    activeView.classList.add("active");
    document.getElementById("pageTitle").textContent = title;
    if (window.innerWidth <= 850) {
      sidebar.classList.remove("open");
    }
  }

  tabChatBtn.addEventListener("click", () => switchTab(tabChatBtn, chatView, "Qwen 3.5 Interactive Chat"));
  tabLangdockBtn.addEventListener("click", () => switchTab(tabLangdockBtn, langdockView, "Langdock Integration Setup"));
  tabApiDocsBtn.addEventListener("click", () => switchTab(tabApiDocsBtn, apiDocsView, "API Endpoints & Integration"));

  // Temperature slider display
  tempSlider.addEventListener("input", (e) => {
    tempValue.textContent = e.target.value;
  });

  // Auto-resize input
  messageInput.addEventListener("input", () => {
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 180) + "px";
  });

  // Enter to send
  messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Quick prompt buttons
  document.querySelectorAll(".quick-prompt-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      messageInput.value = btn.getAttribute("data-prompt");
      messageInput.style.height = "auto";
      messageInput.style.height = messageInput.scrollHeight + "px";
      messageInput.focus();
    });
  });

  // Clear chat
  clearChatBtn.addEventListener("click", () => {
    conversationHistory = [];
    chatContainer.innerHTML = "";
    if (welcomeCard) {
      chatContainer.appendChild(welcomeCard);
      welcomeCard.style.display = "block";
    }
    speedMetric.textContent = "";
  });

  // Fetch initial config & models
  async function loadConfig() {
    try {
      const res = await fetch("/api/config");
      if (res.ok) {
        const config = await res.json();
        ollamaHost.textContent = config.ollama_url || "http://localhost:11434";
        
        // Populate models
        if (config.available_models && config.available_models.length > 0) {
          modelSelect.innerHTML = "";
          config.available_models.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m;
            opt.textContent = m + (m === config.default_model ? " (Default)" : "");
            if (m === config.default_model) opt.selected = true;
            modelSelect.appendChild(opt);
          });
        }
      }
    } catch (e) {
      console.warn("Could not load config:", e);
    }

    // Health check
    try {
      const hRes = await fetch("/api/health");
      if (hRes.ok) {
        const hData = await hRes.json();
        if (hData.ollama && hData.ollama.status === "healthy") {
          healthDot.classList.add("online");
          healthStatus.textContent = "Ollama Active";
          connectionBadge.textContent = "Ollama Connected";
          connectionBadge.className = "badge badge-success";
        } else {
          healthDot.classList.remove("online");
          healthStatus.textContent = "Ollama Issue";
          connectionBadge.textContent = "Ollama Unreachable";
          connectionBadge.className = "badge";
          connectionBadge.style.background = "rgba(244, 63, 94, 0.2)";
          connectionBadge.style.color = "#fb7185";
        }
      }
    } catch (e) {
      healthDot.classList.remove("online");
      healthStatus.textContent = "Offline";
    }
  }

  loadConfig();

  // Chat Submission & Streaming
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const prompt = messageInput.value.trim();
    if (!prompt || isGenerating) return;

    if (welcomeCard) welcomeCard.style.display = "none";

    // Append user message
    appendMessage("user", prompt);
    conversationHistory.push({ role: "user", content: prompt });
    messageInput.value = "";
    messageInput.style.height = "auto";

    // Prepare assistant placeholder message
    const { messageBody, thinkingContainer, contentContainer, thinkingBox } = createAssistantMessage();
    isGenerating = true;
    sendBtn.disabled = true;
    const startTime = performance.now();
    let tokenCount = 0;

    const payload = {
      model: modelSelect.value,
      messages: conversationHistory,
      stream: true,
      options: {
        temperature: parseFloat(tempSlider.value)
      }
    };

    if (systemPrompt.value.trim()) {
      payload.messages = [
        { role: "system", content: systemPrompt.value.trim() },
        ...conversationHistory
      ];
    }

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let assistantReply = "";
      let thinkingText = "";
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop(); // keep remainder

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const chunk = JSON.parse(line);
            const msg = chunk.message || {};
            
            // Qwen 3.5 reasoning tokens
            if (msg.thinking) {
              thinkingBox.style.display = "block";
              thinkingText += msg.thinking;
              thinkingContainer.textContent = thinkingText;
              tokenCount++;
            }

            // Standard content tokens
            if (msg.content) {
              assistantReply += msg.content;
              contentContainer.innerHTML = formatMarkdown(assistantReply);
              tokenCount++;
            }

            // Scroll to bottom
            chatContainer.scrollTop = chatContainer.scrollHeight;
          } catch (err) {
            console.error("Error parsing stream chunk:", err, line);
          }
        }
      }

      conversationHistory.push({ role: "assistant", content: assistantReply });

      // Performance stats
      const totalTime = ((performance.now() - startTime) / 1000).toFixed(1);
      const speed = totalTime > 0 ? (tokenCount / totalTime).toFixed(1) : 0;
      speedMetric.textContent = `Generated ${tokenCount} tokens in ${totalTime}s (~${speed} tok/s)`;

    } catch (err) {
      contentContainer.innerHTML = `<span style="color: #f43f5e;">⚠️ Error: ${err.message}. Ensure Ollama is running at <code>http://localhost:11434</code></span>`;
    } finally {
      isGenerating = false;
      sendBtn.disabled = false;
      messageInput.focus();
    }
  });

  function appendMessage(role, content) {
    const msgEl = document.createElement("div");
    msgEl.className = `message ${role}`;
    msgEl.innerHTML = `
      <div class="message-avatar">${role === "user" ? "U" : "Q"}</div>
      <div class="message-content">
        <div class="message-sender">${role === "user" ? "You" : "Qwen 3.5"}</div>
        <div class="message-body">${escapeHtml(content)}</div>
      </div>
    `;
    chatContainer.appendChild(msgEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }

  function createAssistantMessage() {
    const msgEl = document.createElement("div");
    msgEl.className = "message assistant";
    msgEl.innerHTML = `
      <div class="message-avatar">Q</div>
      <div class="message-content">
        <div class="message-sender">Qwen 3.5</div>
        <div class="message-body">
          <div class="thinking-box" style="display: none;">
            <div class="thinking-header">
              <span>🧠 Thinking Process</span>
              <span class="toggle-icon">▾</span>
            </div>
            <div class="thinking-content"></div>
          </div>
          <div class="answer-content"><em>Thinking...</em></div>
        </div>
      </div>
    `;
    chatContainer.appendChild(msgEl);

    const thinkingBox = msgEl.querySelector(".thinking-box");
    const thinkingHeader = msgEl.querySelector(".thinking-header");
    const thinkingContainer = msgEl.querySelector(".thinking-content");
    const contentContainer = msgEl.querySelector(".answer-content");

    thinkingHeader.addEventListener("click", () => {
      const isVisible = thinkingContainer.style.display !== "none";
      thinkingContainer.style.display = isVisible ? "none" : "block";
      msgEl.querySelector(".toggle-icon").textContent = isVisible ? "▸" : "▾";
    });

    return {
      messageBody: msgEl.querySelector(".message-body"),
      thinkingBox,
      thinkingContainer,
      contentContainer
    };
  }

  // Lightweight markdown formatter
  function formatMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    // Code blocks ```code```
    html = html.replace(/```([\s\S]*?)```/g, (match, p1) => {
      return `<pre><code>${p1.trim()}</code></pre>`;
    });

    // Inline code `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Langdock Handshake Simulator
  if (testHandshakeBtn) {
    testHandshakeBtn.addEventListener("click", async () => {
      testResultBox.style.display = "block";
      testResultBadge.textContent = "Connecting to /chat/completions...";
      testResultBadge.className = "badge";
      testResultBadge.style.background = "rgba(99, 102, 241, 0.2)";
      testResultBadge.style.color = "#818cf8";
      testResultOutput.textContent = "Sending OpenAI-compatible request from Langdock...";

      const start = performance.now();
      try {
        const res = await fetch("/chat/completions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": "Bearer langdock-ollama-secret"
          },
          body: JSON.stringify({
            model: "qwen3.5:4b",
            messages: [{ role: "user", content: "Reply with 'Langdock Handshake Success!'" }],
            stream: false
          })
        });

        const latency = ((performance.now() - start) / 1000).toFixed(2);
        testResultLatency.textContent = `${latency}s`;

        if (res.ok) {
          const data = await res.json();
          testResultBadge.textContent = "SUCCESS (200 OK)";
          testResultBadge.className = "badge badge-success";
          testResultOutput.textContent = JSON.stringify(data, null, 2);
        } else {
          testResultBadge.textContent = `FAILED (${res.status})`;
          testResultBadge.style.background = "rgba(244, 63, 94, 0.2)";
          testResultBadge.style.color = "#fb7185";
          testResultOutput.textContent = await res.text();
        }
      } catch (err) {
        testResultBadge.textContent = "NETWORK ERROR";
        testResultOutput.textContent = err.message;
      }
    });
  }

  window.copyValue = function(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    navigator.clipboard.writeText(el.value).then(() => {
      const original = el.value;
      el.value = "Copied to clipboard!";
      setTimeout(() => { el.value = original; }, 1200);
    });
  };
});
