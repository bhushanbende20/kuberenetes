#!/usr/bin/env python3
"""
Test client to verify Langdock Ollama Bridge connectivity, endpoints,
and streaming generation with Qwen 3.5.
"""

import sys
import time
import json
import requests

SERVER_URL = "http://localhost:8000"

def test_health():
    print("🔍 Testing /health endpoint...")
    try:
        r = requests.get(f"{SERVER_URL}/health", timeout=5)
        print(f"Status: {r.status_code}")
        print(json.dumps(r.json(), indent=2))
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Error connecting to server: {e}")
        return False

def test_models():
    print("\n📦 Testing /v1/models endpoint...")
    try:
        r = requests.get(f"{SERVER_URL}/v1/models", timeout=5)
        print(f"Status: {r.status_code}")
        data = r.json()
        models = [m["id"] for m in data.get("data", [])]
        print(f"Available models: {models}")
        return len(models) > 0
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        return False

def test_langdock_streaming():
    print("\n⚡ Testing Langdock SSE streaming via /chat/completions...")
    url = f"{SERVER_URL}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer langdock-ollama-secret"
    }
    payload = {
        "model": "qwen3.5:4b",
        "messages": [
            {"role": "user", "content": "What is 2+2? Answer in one sentence."}
        ],
        "stream": True,
        "temperature": 0.2
    }

    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=120) as r:
            if r.status_code != 200:
                print(f"❌ Failed with status {r.status_code}: {r.text}")
                return False
            
            print("Stream connected! Receiving chunks:\n---")
            for line in r.iter_lines():
                if not line:
                    continue
                decoded = line.decode("utf-8")
                if decoded.startswith("data: "):
                    data_str = decoded[6:].strip()
                    if data_str == "[DONE]":
                        print("\n---\n✅ Received [DONE]")
                        break
                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            reasoning = delta.get("reasoning_content", "")
                            if reasoning:
                                print(f"\033[93m{reasoning}\033[0m", end="", flush=True)
                            if content:
                                print(f"\033[92m{content}\033[0m", end="", flush=True)
                    except Exception:
                        pass
            return True
    except Exception as e:
        print(f"❌ Streaming error: {e}")
        return False

if __name__ == "__main__":
    print("==========================================")
    print("Langdock -> Ollama (Qwen 3.5) Test Suite")
    print("==========================================")
    h_ok = test_health()
    if not h_ok:
        print("\n⚠️ Ensure the server is running on port 8000 (run: python3 main.py)")
        sys.exit(1)
    test_models()
    test_langdock_streaming()
    print("\n🎉 All integration tests completed!")
