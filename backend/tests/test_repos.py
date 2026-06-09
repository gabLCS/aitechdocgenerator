import pytest


class TestCreateRepository:
    def test_create_success(self, client, auth_headers):
        resp = client.post("/repos/", json={
            "url": "https://github.com/owner/my-repo"
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "owner/my-repo"
        assert data["url"] == "https://github.com/owner/my-repo"

    def test_create_short_format(self, client, auth_headers):
        resp = client.post("/repos/", json={
            "url": "owner/short-repo"
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "owner/short-repo"

    def test_create_invalid_url(self, client, auth_headers):
        resp = client.post("/repos/", json={
            "url": "invalid"
        }, headers=auth_headers)
        assert resp.status_code == 400

    def test_create_unauthenticated(self, client):
        resp = client.post("/repos/", json={"url": "https://github.com/x/y"})
        assert resp.status_code == 401


class TestListRepositories:
    def test_list_empty(self, client, auth_headers):
        resp = client.get("/repos/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_repos(self, client, auth_headers, test_repo):
        resp = client.get("/repos/", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["full_name"] == "owner/test-repo"


class TestGetRepository:
    def test_get_by_id(self, client, auth_headers, test_repo):
        resp = client.get(f"/repos/{test_repo.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["full_name"] == "owner/test-repo"

    def test_get_not_found(self, client, auth_headers):
        resp = client.get("/repos/99999", headers=auth_headers)
        assert resp.status_code == 404


class TestDeleteRepository:
    def test_delete_success(self, client, auth_headers, test_repo):
        resp = client.delete(f"/repos/{test_repo.id}", headers=auth_headers)
        assert resp.status_code == 200

    def test_delete_not_found(self, client, auth_headers):
        resp = client.delete("/repos/99999", headers=auth_headers)
        assert resp.status_code == 404
