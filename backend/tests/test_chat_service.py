import pytest
from unittest.mock import AsyncMock, patch

from app.services import chat_service

SAMPLE_EVIDENCE = {
    "structure": "app/\n  main.py\n  routers/\n    auth.py\n  models.py",
    "stats": {"file_count": 5, "total_lines": 250},
    "files_content": {
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root():\n    return {'status': 'ok'}",
        "app/routers/auth.py": "from fastapi import APIRouter\nrouter = APIRouter()\n@router.post('/login')\ndef login(): pass",
    }
}


class TestBuildRepoContext:
    def test_with_evidence(self):
        snippet = chat_service.build_repo_context_from_evidence(SAMPLE_EVIDENCE)
        assert "Repository Structure" in snippet
        assert "main.py" in snippet
        assert "files_content" not in snippet

    def test_without_evidence(self):
        snippet = chat_service.build_repo_context_from_evidence({})
        assert snippet == "No evidence available."


class TestCreateChatSession:
    def test_create_session(self, db, test_user, test_repo):
        sid = chat_service.create_chat_session(db, test_user.id, test_repo.id, repo_name="owner/test-repo")
        assert sid is not None
        assert "session_" in sid

    def test_create_session_with_evidence(self, db, test_user, test_repo):
        sid = chat_service.create_chat_session(db, test_user.id, test_repo.id, repo_name="owner/test-repo", evidence=SAMPLE_EVIDENCE)
        assert sid is not None

    def test_create_and_add_message(self, db, test_user, test_repo):
        sid = chat_service.create_chat_session(db, test_user.id, test_repo.id)
        chat_service.add_message(db, sid, "user", "Hello!")
        messages = chat_service.get_session_messages(db, sid)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello!"


class TestGetChatReply:
    @pytest.mark.asyncio
    async def test_get_reply_calls_llm(self, db, test_user, test_repo):
        sid = chat_service.create_chat_session(db, test_user.id, test_repo.id, repo_name="owner/test-repo", evidence=SAMPLE_EVIDENCE)
        chat_service.add_message(db, sid, "user", "What architecture?")

        with patch("app.services.chat_service.generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "FastAPI with routers."
            reply = await chat_service.get_chat_reply(db, sid, "What architecture?", repo_name="owner/test-repo")
            assert reply == "FastAPI with routers."
            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_reply_appends_to_history(self, db, test_user, test_repo):
        sid = chat_service.create_chat_session(db, test_user.id, test_repo.id, repo_name="owner/test-repo", evidence=SAMPLE_EVIDENCE)
        with patch("app.services.chat_service.generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Reply text"
            await chat_service.get_chat_reply(db, sid, "Question?", repo_name="owner/test-repo")
        messages = chat_service.get_session_messages(db, sid)
        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_reply_session_not_found(self, db):
        reply = await chat_service.get_chat_reply(db, "nonexistent", "Hello?")
        assert "not found" in reply


class TestDeleteSession:
    def test_delete_existing_session(self, db, test_user, test_repo):
        sid = chat_service.create_chat_session(db, test_user.id, test_repo.id)
        chat_service.delete_session(db, sid)
        messages = chat_service.get_session_messages(db, sid)
        assert len(messages) == 0

    def test_delete_nonexistent_session(self, db):
        chat_service.delete_session(db, "nonexistent")


class TestListSessions:
    def test_list_empty(self, db, test_user):
        sessions = chat_service.list_sessions(db, test_user.id)
        assert sessions == []

    def test_list_with_sessions(self, db, test_user, test_repo):
        chat_service.create_chat_session(db, test_user.id, test_repo.id, repo_name="repo-a")
        chat_service.create_chat_session(db, test_user.id, test_repo.id, repo_name="repo-b")
        sessions = chat_service.list_sessions(db, test_user.id)
        assert len(sessions) == 2
