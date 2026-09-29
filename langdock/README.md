# Langdock Ollama (Qwen 3.5) Bridge & Interactive Application

A production-ready application and API bridge that connects **Langdock** to your local **Ollama** instance, streaming responses from the **Qwen 3.5** model (`qwen3.5:4b`) located at `http://localhost:11434/api/chat`.

---

## 🏗️ Architecture Overview

```mermaid
flowchart LR
    subgraph ClientLayer["Clients & Platforms"]
        Langdock["Langdock Workspace<br/>(Custom Model / BYOK)"]
        Browser["Interactive Web UI<br/>(http://localhost:8000)"]
        CLI["cURL / Python Scripts"]
    end

    subgraph Bridge["FastAPI Bridge Service (Port 8000)"]
        Auth["Bearer Token Auth / CORS"]
        OpenAIAdapter["Langdock / OpenAI Adapter<br/>POST /chat/completions"]
        NativeProxy["Native Ollama Proxy<br/>POST /api/chat"]
        ThinkingParser["Qwen 3.5 Reasoning Parser<br/>(reasoning_content & SSE)"]
    end

    subgraph OllamaServer["Local Ollama Engine (Port 11434)"]
        ChatAPI["POST /api/chat"]
        QwenModel["Qwen 3.5 (4.7B GGUF)<br/>capabilities: [thinking, completion, tools]"]
    end

    Langdock -->|"OpenAI SSE Stream"| OpenAIAdapter
    Browser -->|"SSE Stream & REST"| NativeProxy
    CLI -->|"cURL"| OpenAIAdapter

    OpenAIAdapter --> Auth
    Auth --> ThinkingParser
    NativeProxy --> ChatAPI
    ThinkingParser --> ChatAPI
    ChatAPI <--> QwenModel
```

---

## ⚡ Quickstart

### 1. Prerequisites
Ensure Ollama is running and has the Qwen model pulled:
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Pull Qwen 3.5 (if not already installed)
ollama run qwen3.5:4b
```

### 2. Run Locally (1 Command)
```bash
cd /Users/apple/Documents/Kubernetes/langdock
./run.sh
```
Or run directly with Python:
```bash
../.venv/bin/python main.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser!

---

## 🔌 Connecting with Langdock

Langdock supports **OpenAI-Compatible Custom Models**:

1. Open your **Langdock** workspace.
2. Navigate to **Settings** &rarr; **Models** (or **Bring Your Own Keys**).
3. Click **"Add Custom Model"** / **"Add Provider (OpenAI Compatible)"**.
4. Configure the following values:
   * **Provider Name:** `Local Qwen (Ollama)`
   * **Base URL:** `http://localhost:8000` *(or your ngrok / k8s ingress URL if Langdock is on the cloud)*
   * **Model ID:** `qwen3.5:4b`
   * **API Key:** `langdock-ollama-secret` *(optional, can be disabled with `REQUIRE_AUTH=false`)*
5. Click **Save** and start chatting with Qwen 3.5 inside Langdock!

> **Cloud Langdock Users**: If using cloud-hosted Langdock (`app.langdock.com`), expose your local bridge using ngrok:
> ```bash
> ngrok http 8000
> ```
> Use the generated `https://<subdomain>.ngrok-free.app` as the Base URL in Langdock.

---

## 🖥️ Interactive Web UI Features

* **⚡ Real-time SSE Streaming:** Tokens stream onto the screen as they are generated.
* **🧠 Thinking Process Accordion:** Qwen 3.5's internal reasoning tokens are parsed and displayed inside a collapsible, animated thinking disclosure.
* **🎛️ Live Parameter Tuning:** Real-time temperature slider, custom system persona, and model selector (auto-discovers models installed in Ollama).
* **🧪 Langdock Simulator Tab:** Built-in handshake tester that simulates Langdock sending OpenAI-compatible requests and checks live responses.

---

## 📡 API Endpoints

### 1. Langdock / OpenAI Custom Model (`POST /chat/completions`)
Matches standard OpenAI format with SSE streaming support:
```bash
curl -N http://localhost:8000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer langdock-ollama-secret" \
  -d '{
    "model": "qwen3.5:4b",
    "messages": [
      {"role": "system", "content": "You are a concise expert."},
      {"role": "user", "content": "Explain Kubernetes in one sentence."}
    ],
    "stream": true,
    "temperature": 0.5
  }'
```

### 2. Native Ollama Proxy (`POST /api/chat`)
Accepts native Ollama payload directly:
```bash
curl -N http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.5:4b",
    "messages": [{"role": "user", "content": "Hello Qwen!"}],
    "stream": true
  }'
```

### 3. Model Discovery (`GET /v1/models` or `GET /api/config`)
```bash
curl http://localhost:8000/v1/models
```

### 4. Health Check (`GET /health`)
```bash
curl http://localhost:8000/health
```

---

## 🐳 Docker & Kubernetes Deployment

### Run via Docker Compose:
```bash
docker-compose up --build -d
```

### Deploy to Kubernetes:
```bash
kubectl apply -f k8s/deployment.yaml
```

---

## 🧪 Testing the Integration

Run the automated test suite from the terminal:
```bash
./test_client.py
```
This tests health checks, model discovery, and streaming verification with token highlighting.
