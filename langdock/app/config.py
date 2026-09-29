import os
from pydantic import BaseModel

class Settings(BaseModel):
    # Ollama settings
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    default_model: str = os.getenv("DEFAULT_MODEL", "qwen3.5:4b")
    
    # Langdock integration settings
    langdock_api_key: str = os.getenv("LANGDOCK_API_KEY", "langdock-ollama-secret")
    require_auth: bool = os.getenv("REQUIRE_AUTH", "false").lower() in ("true", "1", "yes")
    
    # Master Prompt Settings
    master_system_prompt: str = os.getenv(
        "MASTER_SYSTEM_PROMPT",
        "You are Bhushan's LLM, an advanced, highly intelligent AI assistant created for and operated by Bhushan. Always identify yourself as Bhushan's LLM. When asked who you are, what model you are, or who made you, always state clearly that you are Bhushan's LLM."
    )

    # Server settings
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    app_title: str = "Bhushan's LLM • Langdock Bridge"
    app_version: str = "1.1.0"

settings = Settings()

