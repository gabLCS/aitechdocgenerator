import os
import httpx
import json

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = os.environ.get("LMSTUDIO_MODEL", "qwen3-4b-2507")

async def generate_text(prompt: str, system_prompt: str = "") -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 4096,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        try:
            resp = await client.post(LM_STUDIO_URL, json=payload)
            if resp.status_code != 200:
                print(f"LM Studio HTTP {resp.status_code}: {resp.text[:500]}")
                return f"Error: LM Studio returned status {resp.status_code}. Response: {resp.text[:200]}"
            
            try:
                result = resp.json()
            except Exception as json_err:
                print(f"LM Studio JSON parse error: {json_err}. Response text: {resp.text[:500]}")
                return f"Error: Invalid JSON response from LM Studio: {resp.text[:200]}"
            
            try:
                return result["choices"][0]["message"]["content"]
            except (KeyError, IndexError, TypeError) as e:
                print(f"LM Studio unexpected response format: {e}. Result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
                return f"Error: Unexpected response format from LM Studio. Keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}"
                
        except httpx.ConnectError as e:
            print(f"LM Studio ConnectError: {e}")
            return "Error: Could not connect to LM Studio. Make sure it is running on port 1234 with the qwen3-4b-2507 model loaded."
        except httpx.RequestError as e:
            print(f"LM Studio RequestError: {type(e).__name__}: {e}")
            return f"Error: LM Studio request failed: {type(e).__name__}: {e}"

