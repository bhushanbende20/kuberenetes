#!/usr/bin/env bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=================================================="
echo "🚀 Starting Langdock Ollama (Qwen 3.5) Bridge"
echo "=================================================="

# Check for Python virtual environment
if [ -f "../.venv/bin/python" ]; then
    PYTHON="../.venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
else
    PYTHON="python3"
fi

echo "Using Python: $($PYTHON --version)"

# Verify Ollama is running
echo "Checking Ollama connectivity on http://localhost:11434..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running and accessible."
else
    echo "⚠️ Warning: Ollama does not appear to be running on http://localhost:11434."
    echo "   Please ensure 'ollama serve' is running."
fi

# Run server
export HOST="0.0.0.0"
export PORT="8000"
export OLLAMA_BASE_URL="http://localhost:11434"
export DEFAULT_MODEL="qwen3.5:4b"

echo "Starting server on http://localhost:8000..."
echo "Web UI: http://localhost:8000"
echo "Langdock Endpoint: http://localhost:8000/chat/completions"
echo "Press Ctrl+C to stop."
exec $PYTHON main.py
