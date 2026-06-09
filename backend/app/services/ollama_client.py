import os
import httpx
import json
from ..logging_config import get_custom_logger

logger = get_custom_logger("ollama_client", "ollama_client.log")

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = os.environ.get("OLLAMA_MODEL", "qwen3")

async def generate_text(prompt: str, system_prompt: str = "") -> str:
    """
    Calls the local Ollama instance to generate text.
    """
    logger.info(f"Requesting text generation from Ollama. Model: '{MODEL_NAME}' | Prompt length: {len(prompt)} chars | System prompt length: {len(system_prompt)} chars")
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.3, # Low temp for technical docs
            "top_p": 0.9,
            "num_predict": 4096 # Allow long output
        }
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client: # Long timeout for LLM
        try:
            resp = await client.post(OLLAMA_URL, json=payload)
            resp.raise_for_status()
            result = resp.json()
            response_text = result.get("response", "")
            logger.info(f"Ollama generation completed successfully. Generated text size: {len(response_text)} characters.")
            return response_text
        except httpx.RequestError as e:
            logger.error(f"Ollama connection/request error: {e}")
            return "Error: Could not connect to Ollama. Make sure it is running."
