import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from .config import settings

logger = logging.getLogger("langdock.ollama")

class OllamaClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        # Generous timeout for local LLM inference
        self.timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=30.0)

    async def check_health(self) -> Dict[str, Any]:
        """Verify connection to Ollama server and list models."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            try:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    has_default = settings.default_model in models
                    return {
                        "status": "healthy",
                        "ollama_url": self.base_url,
                        "available_models": models,
                        "default_model": settings.default_model,
                        "default_model_ready": has_default
                    }
                return {"status": "unhealthy", "code": resp.status_code, "error": resp.text}
            except Exception as e:
                logger.error(f"Ollama health check failed: {e}")
                return {"status": "unreachable", "error": str(e), "ollama_url": self.base_url}

    async def list_models(self) -> List[Dict[str, Any]]:
        """List all models currently installed in Ollama."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
            try:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    return resp.json().get("models", [])
            except Exception as e:
                logger.error(f"Failed to fetch models: {e}")
            return []

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        format_json: bool = False
    ) -> Dict[str, Any]:
        """Non-streaming chat request to Ollama /api/chat."""
        target_model = model or settings.default_model
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "stream": False
        }
        if options:
            payload["options"] = options
        if format_json:
            payload["format"] = "json"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                f"{self.base_url}/api/chat",
                json=payload
            )
            resp.raise_for_status()
            return resp.json()

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Streaming chat request to Ollama /api/chat yielding parsed json lines."""
        target_model = model or settings.default_model
        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "stream": True
        }
        if options:
            payload["options"] = options

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError as err:
                        logger.warning(f"Failed to decode chunk line: {line} ({err})")

ollama_client = OllamaClient()
