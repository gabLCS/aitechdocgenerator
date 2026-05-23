import httpx
import json
from typing import Optional

OPENCODE_API_URL = "http://localhost:7000/api/opencode"

async def send_command(command: str, params: dict | None = None) -> dict:
    payload = {
        "command": command,
        "params": params or {}
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            resp = await client.post(OPENCODE_API_URL, json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            print(f"OpenCode API connection error: {e}")
            return {"error": f"Could not connect to OpenCode API at {OPENCODE_API_URL}"}
        except httpx.HTTPStatusError as e:
            print(f"OpenCode API HTTP error: {e}")
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}


async def list_files(repo_path: str | None = None) -> list:
    params = {"path": repo_path} if repo_path else {}
    result = await send_command("list_files", params)
    if "error" in result:
        return []
    return result.get("files", [])


async def analyze_python_files(file_paths: list, repo_path: str | None = None) -> dict:
    params = {
        "file_paths": file_paths,
        "repo_path": repo_path or ""
    }
    return await send_command("analyze_python_files", params)


async def extract_requirements(analysis_result: dict) -> dict:
    functional = []
    non_functional = []

    if isinstance(analysis_result, dict):
        reqs = analysis_result.get("requirements", {})
        functional = reqs.get("functional", [])
        non_functional = reqs.get("non_functional", [])

    return {
        "functional_requirements": functional,
        "non_functional_requirements": non_functional
    }


async def generate_architecture(analysis_result: dict) -> dict:
    if isinstance(analysis_result, dict):
        arch = analysis_result.get("architecture", {})
        if not arch:
            layers_detected = analysis_result.get("detected_layers", [])
            arch = {
                "pattern": "layered",
                "layers": layers_detected if layers_detected else [
                    {"name": "Presentation", "description": "UI/API layer"},
                    {"name": "Business Logic", "description": "Core processing"},
                    {"name": "Data Access", "description": "Persistence layer"},
                ],
                "mermaid_diagram": ""
            }
        return arch

    return {
        "pattern": "layered",
        "layers": [
            {"name": "Presentation", "description": "UI/API layer"},
            {"name": "Business Logic", "description": "Core processing"},
            {"name": "Data Access", "description": "Persistence layer"},
        ],
        "mermaid_diagram": ""
    }


async def full_analysis_pipeline(repo_path: str | None = None, file_paths: list | None = None) -> dict:
    if file_paths is None:
        file_paths = await list_files(repo_path)

    if not file_paths:
        return {"error": "No Python files found to analyze"}

    analysis = await analyze_python_files(file_paths, repo_path)

    if "error" in analysis:
        return analysis

    requirements = await extract_requirements(analysis)
    architecture = await generate_architecture(analysis)

    return {
        "files_analyzed": file_paths,
        "requirements": requirements,
        "architecture": architecture,
        "raw_analysis": analysis
    }
