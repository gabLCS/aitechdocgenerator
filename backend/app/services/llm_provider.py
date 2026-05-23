import httpx
from ..logging_config import get_custom_logger

logger = get_custom_logger("llm_provider", "llm_provider.log")

_ACTIVE_PROVIDER = None


async def check_lm_studio() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:1234/v1/models")
            return resp.status_code == 200
    except Exception:
        return False


async def check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def detect_provider() -> str:
    if await check_lm_studio():
        logger.info("LM Studio detected on port 1234")
        return "lm_studio"
    if await check_ollama():
        logger.info("Ollama detected on port 11434")
        return "ollama"
    logger.warning("No LLM provider detected (LM Studio or Ollama)")
    return "none"


def get_active_provider() -> str:
    global _ACTIVE_PROVIDER
    return _ACTIVE_PROVIDER or "not_detected"


async def generate_text(prompt: str, system_prompt: str = "") -> str:
    global _ACTIVE_PROVIDER

    if _ACTIVE_PROVIDER is None:
        _ACTIVE_PROVIDER = await detect_provider()

    if _ACTIVE_PROVIDER == "lm_studio":
        from .lm_studio_client import generate_text as _gen
        return await _gen(prompt, system_prompt)

    if _ACTIVE_PROVIDER == "ollama":
        from .ollama_client import generate_text as _gen
        return await _gen(prompt, system_prompt)

    return "Error: No LLM provider available. Please start LM Studio (port 1234) or Ollama (port 11434) and restart the backend."
