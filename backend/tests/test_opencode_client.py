import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

MOCK_LIST_FILES_RESPONSE = {
    "files": [
        "app/main.py",
        "app/routers/auth.py",
        "app/routers/repos.py",
        "app/services/github_fetcher.py",
        "app/models.py",
        "app/schemas.py",
    ]
}

MOCK_ANALYSIS_RESPONSE = {
    "requirements": {
        "functional": [
            "The system shall allow users to register and authenticate.",
            "The system shall allow users to add GitHub repositories.",
            "The system shall analyze repository structure and generate documentation.",
        ],
        "non_functional": [
            "The system shall respond to API requests within 2 seconds.",
            "The system shall support JWT-based authentication.",
            "The system shall handle repositories up to 100MB.",
        ],
    },
    "detected_layers": [
        {"name": "Routers", "description": "API endpoint definitions"},
        {"name": "Services", "description": "Business logic and external integrations"},
        {"name": "Models", "description": "Database ORM models"},
    ],
    "architecture": {
        "pattern": "layered",
        "layers": [
            {"name": "Routers", "description": "API endpoint definitions"},
            {"name": "Services", "description": "Business logic and external integrations"},
            {"name": "Models", "description": "Database ORM models"},
        ],
        "mermaid_diagram": "graph TD\n    A[Routers] --> B[Services]\n    B --> C[Models]",
    },
}


class TestListFiles:
    @pytest.mark.asyncio
    async def test_list_files_returns_file_list(self):
        from app.services.opencode_client import list_files

        with patch("app.services.opencode_client.send_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = MOCK_LIST_FILES_RESPONSE
            result = await list_files("/fake/repo")
            assert len(result) == 6
            assert "app/main.py" in result

    @pytest.mark.asyncio
    async def test_list_files_returns_empty_on_error(self):
        from app.services.opencode_client import list_files

        with patch("app.services.opencode_client.send_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = {"error": "connection refused"}
            result = await list_files("/fake/repo")
            assert result == []

    @pytest.mark.asyncio
    async def test_list_files_with_no_path(self):
        from app.services.opencode_client import list_files

        with patch("app.services.opencode_client.send_command", new_callable=AsyncMock) as mock_cmd:
            mock_cmd.return_value = MOCK_LIST_FILES_RESPONSE
            result = await list_files()
            mock_cmd.assert_called_once()
            assert len(result) == 6


class TestExtractRequirements:
    @pytest.mark.asyncio
    async def test_extract_requirements_from_valid_response(self):
        from app.services.opencode_client import extract_requirements

        result = await extract_requirements(MOCK_ANALYSIS_RESPONSE)
        assert len(result["functional_requirements"]) == 3
        assert len(result["non_functional_requirements"]) == 3

    @pytest.mark.asyncio
    async def test_extract_requirements_from_empty_response(self):
        from app.services.opencode_client import extract_requirements

        result = await extract_requirements({})
        assert result["functional_requirements"] == []
        assert result["non_functional_requirements"] == []

    @pytest.mark.asyncio
    async def test_extract_requirements_from_non_dict(self):
        from app.services.opencode_client import extract_requirements

        result = await extract_requirements("not a dict")
        assert result["functional_requirements"] == []
        assert result["non_functional_requirements"] == []


class TestGenerateArchitecture:
    @pytest.mark.asyncio
    async def test_generate_architecture_from_valid_response(self):
        from app.services.opencode_client import generate_architecture

        result = await generate_architecture(MOCK_ANALYSIS_RESPONSE)
        assert result["pattern"] == "layered"
        assert len(result["layers"]) == 3

    @pytest.mark.asyncio
    async def test_generate_architecture_with_defaults(self):
        from app.services.opencode_client import generate_architecture

        result = await generate_architecture({})
        assert result["pattern"] == "layered"
        assert len(result["layers"]) == 3
        assert result["layers"][0]["name"] == "Presentation"


class TestSendCommand:
    @pytest.mark.asyncio
    async def test_send_command_success(self):
        from app.services.opencode_client import send_command

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "files": ["a.py"]}

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response

        with patch("app.services.opencode_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await send_command("list_files", {"path": "/repo"})
            assert result == {"status": "ok", "files": ["a.py"]}
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_command_connection_error(self):
        from app.services.opencode_client import send_command
        import httpx

        mock_client = AsyncMock()
        mock_client.post.side_effect = httpx.RequestError("connection refused")

        with patch("app.services.opencode_client.httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await send_command("test", {})
            assert "error" in result


class TestFullAnalysisPipeline:
    @pytest.mark.asyncio
    async def test_full_pipeline_success(self):
        from app.services.opencode_client import full_analysis_pipeline

        with (
            patch("app.services.opencode_client.list_files", new_callable=AsyncMock) as mock_list,
            patch("app.services.opencode_client.analyze_python_files", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_list.return_value = ["app/main.py", "app/models.py"]
            mock_analyze.return_value = MOCK_ANALYSIS_RESPONSE

            result = await full_analysis_pipeline(repo_path="/fake/repo")
            assert "files_analyzed" in result
            assert "requirements" in result
            assert "architecture" in result
            assert len(result["requirements"]["functional_requirements"]) == 3

    @pytest.mark.asyncio
    async def test_full_pipeline_no_files(self):
        from app.services.opencode_client import full_analysis_pipeline

        with patch("app.services.opencode_client.list_files", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            result = await full_analysis_pipeline(repo_path="/fake/repo")
            assert "error" in result
