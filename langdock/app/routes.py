import time
import uuid
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse, JSONResponse
from .config import settings
from .ollama_client import ollama_client
from .langdock_adapter import (
    convert_langdock_request_to_ollama,
    format_non_streaming_response,
    stream_langdock_sse
)

logger = logging.getLogger("langdock.routes")
router = APIRouter()

def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Validate Bearer token for Langdock custom model requests."""
    if not settings.require_auth:
        return True
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format. Expected 'Bearer <key>'")
    token = parts[1]
    if token != settings.langdock_api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True

# -------------------------------------------------------------
# Langdock Custom Model Endpoints (OpenAI-compatible)
# -------------------------------------------------------------
@router.post("/chat/completions", dependencies=[Depends(verify_token)])
@router.post("/v1/chat/completions", dependencies=[Depends(verify_token)])
async def chat_completions(request: Request):
    """
    Main endpoint called by Langdock when configuring an OpenAI-compatible custom model.
    Translates input to Ollama /api/chat and returns SSE stream or JSON completion.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Malformed JSON body")

    model, messages, options, stream = convert_langdock_request_to_ollama(body, settings.default_model)
    req_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
    
    logger.info(f"Langdock request: model={model}, messages_len={len(messages)}, stream={stream}")

    if stream:
        generator = ollama_client.stream_chat(messages=messages, model=model, options=options)
        return StreamingResponse(
            stream_langdock_sse(generator, req_id, model),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        try:
            ollama_resp = await ollama_client.chat(messages=messages, model=model, options=options)
            return JSONResponse(content=format_non_streaming_response(ollama_resp, req_id, model))
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise HTTPException(status_code=500, detail=f"Ollama inference error: {str(e)}")

@router.get("/v1/models", dependencies=[Depends(verify_token)])
@router.get("/models", dependencies=[Depends(verify_token)])
async def get_models():
    """List available models for Langdock model discovery."""
    raw_models = await ollama_client.list_models()
    formatted = []
    for m in raw_models:
        name = m.get("name")
        created = int(time.time())
        formatted.append({
            "id": name,
            "object": "model",
            "created": created,
            "owned_by": "ollama",
            "permission": [],
            "root": name,
            "parent": None
        })
    return {"object": "list", "data": formatted}

# -------------------------------------------------------------
# Native Ollama Proxy Endpoints & UI Helper Endpoints
# -------------------------------------------------------------
@router.post("/api/chat")
async def native_ollama_chat(request: Request):
    """
    Direct proxy to Ollama /api/chat.
    Accepts native Ollama payload: {"model": "...", "messages": [...], "stream": true}
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    model = body.get("model", settings.default_model)
    messages = body.get("messages", [])
    stream = body.get("stream", True)
    options = body.get("options")

    if stream:
        async def event_generator():
            async for chunk in ollama_client.stream_chat(messages=messages, model=model, options=options):
                import json
                yield f"{json.dumps(chunk)}\n"

        return StreamingResponse(
            event_generator(),
            media_type="application/x-ndjson",
            headers={"Cache-Control": "no-cache"}
        )
    else:
        resp = await ollama_client.chat(messages=messages, model=model, options=options)
        return JSONResponse(content=resp)

@router.get("/api/health")
@router.get("/health")
async def health_check():
    """System health check and Ollama connectivity status."""
    ollama_status = await ollama_client.check_health()
    return {
        "status": "online",
        "service": settings.app_title,
        "version": settings.app_version,
        "auth_required": settings.require_auth,
        "ollama": ollama_status
    }

@router.get("/api/config")
async def get_client_config():
    """Provide public config to the Web UI."""
    models_info = await ollama_client.list_models()
    model_names = [m.get("name") for m in models_info]
    return {
        "default_model": settings.default_model,
        "available_models": model_names,
        "ollama_url": settings.ollama_base_url,
        "require_auth": settings.require_auth,
        "langdock_setup": {
            "suggested_base_url": f"http://localhost:{settings.port}",
            "model_id": settings.default_model,
            "api_key": settings.langdock_api_key if settings.require_auth else "none_required"
        }
    }
