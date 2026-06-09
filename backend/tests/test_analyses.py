from unittest.mock import patch, AsyncMock
from app import models


class TestStartAnalysis:
    def test_start_analysis_creates_job(self, client, auth_headers, test_repo):
        with patch("app.routers.analyses.run_analysis_pipeline", new_callable=AsyncMock) as mock_pipeline:
            resp = client.post(f"/analyses/?repository_id={test_repo.id}", headers=auth_headers, json={})
            assert resp.status_code == 200
            data = resp.json()
            assert data["repository_id"] == test_repo.id
            assert data["status"] == "PENDING"
            mock_pipeline.assert_called_once()

    def test_start_analysis_repo_not_found(self, client, auth_headers):
        resp = client.post("/analyses/?repository_id=99999", headers=auth_headers, json={})
        assert resp.status_code == 404

    def test_start_analysis_unauthenticated(self, client):
        resp = client.post("/analyses/?repository_id=1", json={})
        assert resp.status_code == 401


class TestGetAnalysisStatus:
    def test_get_status(self, client, auth_headers, test_repo, db):
        job = models.AnalysisJob(repository_id=test_repo.id, status=models.JobStatus.RUNNING)
        db.add(job)
        db.commit()

        resp = client.get(f"/analyses/{job.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "RUNNING"

    def test_get_status_not_found(self, client, auth_headers):
        resp = client.get("/analyses/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestGetSteps:
    def test_get_steps_empty(self, client, auth_headers, test_repo, db):
        job = models.AnalysisJob(repository_id=test_repo.id)
        db.add(job)
        db.commit()

        resp = client.get(f"/analyses/{job.id}/steps", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["steps"] == []

    def test_get_steps_with_content(self, client, auth_headers, test_repo, db):
        import json
        job = models.AnalysisJob(
            repository_id=test_repo.id,
            steps_json=json.dumps([
                {"timestamp": "2026-01-01T00:00:00Z", "message": "Step one"},
                {"timestamp": "2026-01-01T00:01:00Z", "message": "Step two"},
            ])
        )
        db.add(job)
        db.commit()

        resp = client.get(f"/analyses/{job.id}/steps", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()["steps"]) == 2


class TestGetDocument:
    def test_get_document_success(self, client, auth_headers, test_repo, db):
        job = models.AnalysisJob(repository_id=test_repo.id, status=models.JobStatus.DONE)
        db.add(job)
        db.commit()
        doc = models.Document(job_id=job.id, content_md="# Hello\nThis is a test.")
        db.add(doc)
        db.commit()

        resp = client.get(f"/analyses/{job.id}/document", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["markdown"] == "# Hello\nThis is a test."

    def test_get_document_not_found(self, client, auth_headers, test_repo, db):
        job = models.AnalysisJob(repository_id=test_repo.id)
        db.add(job)
        db.commit()

        resp = client.get(f"/analyses/{job.id}/document", headers=auth_headers)
        assert resp.status_code == 404
