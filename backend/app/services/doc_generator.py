import json
from .llm_provider import generate_text
from .opencode_client import full_analysis_pipeline
from ..logging_config import get_custom_logger

logger = get_custom_logger("doc_generator", "doc_generator.log")

SYSTEM_PROMPT = """
You are an expert Senior Software Architect and Technical Writer.
Your task is to analyze the provided "Evidence Package" of a software repository and generate a comprehensive Technical Documentation.
You MUST output the result in strict Markdown format.
Do NOT invent features that are not present. If you are unsure, state that it is "inferred" or "not found".
Use a professional, technical tone.
"""

USER_PROMPT_TEMPLATE = """
Here is the Evidence Package for the repository:
{evidence_json}

Please generate the following documentation:

# 1. Functional Requirements
List the main features and functionalities based on the README and code structure.

# 2. Non-Functional Requirements
Infer security, performance, scalability, and observability requirements based on the libraries and configurations found.

# 3. Architecture (Diagrams)
- Describe the likely Architecture (MVC, Layered, Microservices).
- Provide a Mermaid.js flowchart diagram (ONLY use type `graph TD`). Do NOT use any other diagram type.
  The diagram MUST be inside a fenced code block with `mermaid` like this:
  ```mermaid
  graph TD
    A["User"] --> B["System"]
    B --> C["Database"]
  ```
- Provide a second Mermaid.js flowchart diagram (ONLY type `graph TD`) showing the internal components.
  Example:
  ```mermaid
  graph TD
    A["Module1"] --> B["Module2"]
    B --> C["Module3"]
  ```

IMPORTANT RULES for Mermaid diagrams:
- ONLY use `graph TD` as the diagram type.
- NEVER use `componentDiagram`, `C4Context`, `flowchart`, `sequenceDiagram`, or any other type.
- The system can ONLY render `graph TD` diagrams.
- Each diagram must be inside its own ```mermaid code block.
- ALWAYS use double-quoted labels: `A["Label with (special) chars"]` instead of `A[Label]`.
  This avoids syntax errors with parentheses, ampersands, and other special characters.

# 4. Stack & Technologies
List languages, frameworks, databases, and build tools detected.

# 5. Project Summary
A brief executive summary of what the project does.

"""

async def generate_documentation(evidence: dict, repo_path: str = None) -> str:
    logger.info(f"Starting generate_documentation. Aggregated evidence keys: {list(evidence.keys())}")

    opencode_data = {}
    try:
        opencode_data = await full_analysis_pipeline(repo_path=repo_path)
    except Exception as e:
        logger.warning(f"OpenCode analysis skipped: {e}")

    if not opencode_data or "error" in opencode_data:
        evidence_str = json.dumps(evidence, indent=2)
        prompt = USER_PROMPT_TEMPLATE.format(evidence_json=evidence_str)
        logger.info(f"Sending prompt to LM Studio. Prompt payload size: {len(prompt)} characters.")
        doc_markdown = await generate_text(prompt, SYSTEM_PROMPT)
        logger.info(f"Generated documentation. Markdown size: {len(doc_markdown)} characters.")
        return doc_markdown

    requirements = opencode_data.get("requirements", {})
    architecture = opencode_data.get("architecture", {})

    functional_reqs = requirements.get("functional_requirements", [])
    non_functional_reqs = requirements.get("non_functional_requirements", [])
    layers = architecture.get("layers", [])
    mermaid_str = architecture.get("mermaid_diagram", "")

    evidence_str = json.dumps(evidence, indent=2)

    enriched_prompt = f"""
Here is the Evidence Package for the repository:
{evidence_str}

The following analysis was pre-computed by OpenCode API:

## Pre-identified Functional Requirements
{json.dumps(functional_reqs, indent=2)}

## Pre-identified Non-Functional Requirements
{json.dumps(non_functional_reqs, indent=2)}

## Detected Architecture Layers
{json.dumps(layers, indent=2)}

## Architecture Diagram (Mermaid)
```mermaid
{mermaid_str}
```

Please generate the complete documentation using BOTH the evidence and the pre-computed analysis:

# 1. Functional Requirements
Incorporate the pre-identified functional requirements above and add any additional ones found in the evidence.

# 2. Non-Functional Requirements
Incorporate the pre-identified non-functional requirements above and add any additional ones inferred from the evidence.

# 3. Architecture (Diagrams)
- Use the detected architecture layers and mermaid diagram as a base.
- ONLY use `graph TD` for Mermaid diagrams. Do NOT use any other diagram type.
- ALWAYS use double-quoted labels: `A["Label with (special) chars"]` instead of `A[Label]`.

# 4. Stack & Technologies
List languages, frameworks, databases, and build tools detected.

# 5. Project Summary
A brief executive summary of what the project does.

"""

    logger.info(f"Sending enriched prompt to LM Studio. Prompt payload size: {len(enriched_prompt)} characters.")
    doc_markdown = await generate_text(enriched_prompt, SYSTEM_PROMPT)
    logger.info(f"Generated documentation. Markdown size: {len(doc_markdown)} characters.")
    return doc_markdown
