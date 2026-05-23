import pytest
from unittest.mock import AsyncMock, patch

from app.services import chat_service


@pytest.fixture(autouse=True)
def clean_sessions():
    chat_service._chat_sessions.clear()
    yield
    chat_service._chat_sessions.clear()


SAMPLE_EVIDENCE = {
    "structure": "app/\n  main.py\n  routers/\n    auth.py\n  models.py",
    "stats": {"file_count": 5, "total_lines": 250},
    "files_content": {
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/')\ndef root():\n    return {'status': 'ok'}",
        "app/routers/auth.py": "from fastapi import APIRouter\nrouter = APIRouter()\n@router.post('/login')\ndef login(): pass",
    }
}


class TestCreateChatSession:
    def test_create_session_returns_id(self):
        sid = chat_service.create_chat_session(repo_name="test/repo")
        assert sid is not None
        assert len(sid) == 36

    def test_create_session_with_evidence(self):
        sid = chat_service.create_chat_session(repo_name="test/repo", evidence=SAMPLE_EVIDENCE)
        session = chat_service._get_session(sid)
        assert session["repo_context"] != ""
        assert "main.py" in session["repo_context"]
        assert "No repository analysis" not in session["repo_context"]

    def test_create_session_without_evidence(self):
        sid = chat_service.create_chat_session(repo_name="no-repo")
        session = chat_service._get_session(sid)
        assert "No repository analysis" in session["repo_context"]

    def test_build_repo_context_from_evidence(self):
        snippet = chat_service.build_repo_context_from_evidence(SAMPLE_EVIDENCE)
        assert "Repository Structure" in snippet
        assert "main.py" in snippet
        assert "files_content" not in snippet  # key should not appear, content should


class TestAddMessage:
    def test_add_user_message(self):
        sid = chat_service.create_chat_session(repo_name="test/repo")
        chat_service.add_message(sid, "user", "Hello!")
        history = chat_service.get_session_history(sid)
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello!"

    def test_message_limit(self):
        sid = chat_service.create_chat_session(repo_name="test/repo")
        for i in range(25):
            chat_service.add_message(sid, "user", f"msg {i}")
        history = chat_service.get_session_history(sid)
        assert len(history) == 20


class TestGetChatReply:
    @pytest.mark.asyncio
    async def test_get_reply_calls_llm_with_evidence(self):
        sid = chat_service.create_chat_session(repo_name="test/repo", evidence=SAMPLE_EVIDENCE)
        chat_service.add_message(sid, "user", "What architecture does this use?")

        with patch("app.services.chat_service.generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "This project uses FastAPI with a router-based architecture."

            reply = await chat_service.get_chat_reply(sid, "What architecture does this use?")
            assert len(mock_gen.call_args[0][0]) > 100  # prompt should be long with context
            mock_gen.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_reply_appends_to_history(self):
        sid = chat_service.create_chat_session(repo_name="test/repo", evidence=SAMPLE_EVIDENCE)

        with patch("app.services.chat_service.generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "Reply text"
            await chat_service.get_chat_reply(sid, "Question?")

        history = chat_service.get_session_history(sid)
        assert len(history) == 2
        assert history[1]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_get_reply_without_evidence_has_honest_prompt(self):
        sid = chat_service.create_chat_session(repo_name="test/repo")

        with patch("app.services.chat_service.generate_text", new_callable=AsyncMock) as mock_gen:
            mock_gen.return_value = "I don't have access to the code."
            await chat_service.get_chat_reply(sid, "What does main.py do?")

        prompt = mock_gen.call_args[0][0]
        assert "No detailed analysis" in prompt


class TestDeleteSession:
    def test_delete_existing_session(self):
        sid = chat_service.create_chat_session(repo_name="test/repo")
        chat_service.delete_session(sid)
        assert sid not in chat_service._chat_sessions

    def test_delete_nonexistent_session(self):
        chat_service.delete_session("nonexistent-id")


class TestListSessions:
    def test_list_empty(self):
        sessions = chat_service.list_sessions()
        assert sessions == []

    def test_list_with_sessions(self):
        chat_service.create_chat_session(repo_name="repo-a")
        chat_service.create_chat_session(repo_name="repo-b")
        sessions = chat_service.list_sessions()
        assert len(sessions) == 2
        assert any(s["repo_name"] == "repo-a" for s in sessions)
