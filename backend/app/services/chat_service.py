import json
import secrets
from typing import Optional, List
from sqlalchemy.orm import Session
from .llm_provider import generate_text
from .. import models
from datetime import datetime, timezone

MAX_HISTORY_MESSAGES = 20
MAX_CONTEXT_CHARS = 12000


def build_repo_context_from_evidence(evidence: dict) -> str:
    snippet = ""

    structure = evidence.get("structure", evidence.get("tree", ""))
    if structure:
        snippet += "Repository Structure:\n"
        snippet += str(structure)[:8000]
        snippet += "\n"

    stats = evidence.get("stats", {})
    if stats:
        snippet += f"\nProject Stats:\n{json.dumps(stats, indent=2)}\n"

    files_content = evidence.get("files_content", {})
    if files_content:
        snippet += "\nKey Files Content:\n"
        for fpath, content in files_content.items():
            if content:
                snippet += f"\n--- {fpath} ---\n{content[:2000]}"

    return snippet[:MAX_CONTEXT_CHARS] if snippet else "No evidence available."


def create_chat_session(
    db: Session,
    user_id: int,
    repository_id: int,
    repo_name: str = "unknown",
    evidence: dict | None = None
) -> str:
    session_id = f"session_{repository_id}_{user_id}_{int(datetime.now(timezone.utc).timestamp())}_{secrets.token_hex(4)}"

    repo_context = build_repo_context_from_evidence(evidence) if evidence else "No repository analysis available."

    chat_session = models.ChatSession(
        id=session_id,
        user_id=user_id,
        repository_id=repository_id,
        repo_name=repo_name,
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)

    return session_id


def add_message(db: Session, session_id: str, role: str, content: str):
    message = models.ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
    )
    db.add(message)
    db.commit()


def get_session_messages(db: Session, session_id: str) -> List[dict]:
    messages = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.session_id == session_id)
        .order_by(models.ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": m.role, "content": m.content} for m in messages]


async def get_chat_reply(
    db: Session, session_id: str, user_message: str, repo_name: str = "unknown"
) -> str:
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if not session:
        return "Error: Session not found."

    add_message(db, session_id, "user", user_message)

    messages = get_session_messages(db, session_id)

    # Build repo context from evidence if available
    repo_context = "No repository analysis available."
    repo = session.repository
    if repo:
        job = (
            db.query(models.AnalysisJob)
            .filter(
                models.AnalysisJob.repository_id == repo.id,
                models.AnalysisJob.status == models.JobStatus.DONE,
            )
            .order_by(models.AnalysisJob.id.desc())
            .first()
        )
        if job and job.evidence_json:
            try:
                evidence = json.loads(job.evidence_json)
                repo_context = build_repo_context_from_evidence(evidence)
            except (json.JSONDecodeError, TypeError):
                repo_context = "Error reading repository analysis."

    if "No repository analysis" not in repo_context:
        system_prompt = f"""You are an expert Software Architect assistant helping a developer understand a codebase.
The repository being discussed is: {repo_name}

Here is the repository context (structure and key files):
{repo_context}

RULES:
- Base your answers on the provided repository context.
- If the user asks about architecture, explain it clearly with examples from the code.
- If the user asks how the project would look in a different architecture (e.g., layered, microservices), provide a detailed proposal.
- If information is not available in the context, say so honestly.
- Use code examples from the repo when relevant.
- Keep answers technical but accessible.
- ALWAYS reference specific files, structures, or code from the context.
"""
    else:
        system_prompt = f"""You are an expert Software Architect assistant.
The repository being discussed is: {repo_name}.

IMPORTANT: No detailed analysis of this repository is available. You do not have access to the source code, structure, or files of this repository.

RULES:
- Be honest that you don't have access to the repository's source code.
- You can discuss general patterns, best practices, and how similar projects are typically structured.
- If the user asks about specific files or code, explain that you need the repository to be analyzed first.
- Suggest the user run an analysis on the repository first.
- Keep answers technical but accessible.
"""

    conversation_messages = [
        {"role": "system", "content": system_prompt}
    ]
    for msg in messages:
        conversation_messages.append(msg)

    full_prompt = _format_conversation(conversation_messages)
    reply = await generate_text(full_prompt, "")

    add_message(db, session_id, "assistant", reply)
    return reply


def _format_conversation(messages: list) -> str:
    result = ""
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        result += f"\n[{role}]: {content}"
    return result


def get_session_history(db: Session, session_id: str) -> List[dict]:
    messages = get_session_messages(db, session_id)
    return messages


def delete_session(db: Session, session_id: str):
    session = db.query(models.ChatSession).filter(models.ChatSession.id == session_id).first()
    if session:
        db.delete(session)
        db.commit()


def list_sessions(db: Session, user_id: int) -> List[dict]:
    sessions = (
        db.query(models.ChatSession)
        .filter(models.ChatSession.user_id == user_id)
        .order_by(models.ChatSession.created_at.desc())
        .all()
    )
    return [
        {
            "id": s.id,
            "repo_name": s.repo_name,
            "message_count": db.query(models.ChatMessage)
            .filter(models.ChatMessage.session_id == s.id)
            .count(),
        }
        for s in sessions
    ]
