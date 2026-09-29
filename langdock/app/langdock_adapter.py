import json
import time
import uuid
from typing import Dict, Any, List, AsyncGenerator, Tuple, Optional

from .config import settings

def convert_langdock_request_to_ollama(payload: Dict[str, Any], default_model: str) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any], bool]:
    """
    Translates an incoming Langdock (OpenAI-compatible) chat completion request
    into Ollama /api/chat parameters, ensuring Bhushan's LLM master prompt is applied.
    """
    model = payload.get("model") or default_model
    incoming_messages = payload.get("messages", [])
    stream = payload.get("stream", False)
    
    # Enforce Bhushan's LLM master prompt
    has_system = False
    messages: List[Dict[str, Any]] = []
    for m in incoming_messages:
        if m.get("role") == "system":
            has_system = True
            content = m.get("content", "")
            # Prepend master prompt so identity is always preserved
            messages.append({
                "role": "system",
                "content": f"{settings.master_system_prompt}\n\nContext: {content}" if content else settings.master_system_prompt
            })
        else:
            messages.append(m)

    if not has_system:
        messages.insert(0, {
            "role": "system",
            "content": settings.master_system_prompt
        })

    options: Dict[str, Any] = {}
    if "temperature" in payload and payload["temperature"] is not None:
        options["temperature"] = float(payload["temperature"])
    if "max_tokens" in payload and payload["max_tokens"] is not None:
        options["num_predict"] = int(payload["max_tokens"])
    elif "max_completion_tokens" in payload and payload["max_completion_tokens"] is not None:
        options["num_predict"] = int(payload["max_completion_tokens"])
    if "top_p" in payload and payload["top_p"] is not None:
        options["top_p"] = float(payload["top_p"])
    if "frequency_penalty" in payload and payload["frequency_penalty"] is not None:
        options["repeat_penalty"] = 1.0 + float(payload["frequency_penalty"])

    return model, messages, options, stream

def format_sse_chunk(
    req_id: str,
    model: str,
    content: Optional[str] = None,
    reasoning_content: Optional[str] = None,
    finish_reason: Optional[str] = None
) -> str:
    """Creates a standard OpenAI/Langdock SSE data chunk."""
    delta: Dict[str, Any] = {}
    if content:
        delta["content"] = content
    if reasoning_content:
        # Standard reasoning field recognized by Langdock, vLLM, and OpenWebUI
        delta["reasoning_content"] = reasoning_content
        
    chunk = {
        "id": req_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason
            }
        ]
    }
    return f"data: {json.dumps(chunk)}\n\n"

def format_non_streaming_response(
    ollama_resp: Dict[str, Any],
    req_id: str,
    model: str
) -> Dict[str, Any]:
    """Converts a complete Ollama /api/chat response to Langdock OpenAI format."""
    message = ollama_resp.get("message", {})
    content = message.get("content", "")
    thinking = message.get("thinking", "")
    
    prompt_tokens = ollama_resp.get("prompt_eval_count", 0)
    completion_tokens = ollama_resp.get("eval_count", 0)
    
    response_msg: Dict[str, Any] = {
        "role": "assistant",
        "content": content
    }
    if thinking:
        response_msg["reasoning_content"] = thinking

    return {
        "id": req_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": response_msg,
                "finish_reason": "stop" if ollama_resp.get("done") else None
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    }

async def stream_langdock_sse(
    ollama_generator: AsyncGenerator[Dict[str, Any], None],
    req_id: str,
    model: str,
    include_reasoning: bool = True
) -> AsyncGenerator[str, None]:
    """
    Transforms raw Ollama stream chunks into standard SSE lines for Langdock.
    """
    first_chunk = True
    # First chunk: send initial role
    role_chunk = {
        "id": req_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}]
    }
    yield f"data: {json.dumps(role_chunk)}\n\n"

    in_thinking_mode = False
    
    async for chunk in ollama_generator:
        msg = chunk.get("message", {})
        content = msg.get("content", "")
        thinking = msg.get("thinking", "")
        done = chunk.get("done", False)

        # Handle thinking stream from Qwen 3.5
        if thinking and include_reasoning:
            yield format_sse_chunk(req_id, model, reasoning_content=thinking)

        # Handle standard content stream
        if content:
            yield format_sse_chunk(req_id, model, content=content)

        if done:
            yield format_sse_chunk(req_id, model, finish_reason="stop")
            yield "data: [DONE]\n\n"
            break
