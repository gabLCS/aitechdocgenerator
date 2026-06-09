class TestRegister:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "name": "New User",
            "email": "new@example.com",
            "password": "secret123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert "id" in data
        assert "password" not in data

    def test_register_duplicate_email(self, client, test_user):
        resp = client.post("/auth/register", json={
            "name": "Another",
            "email": "test@example.com",
            "password": "other123",
        })
        assert resp.status_code == 400


class TestLogin:
    def test_login_success(self, client, test_user):
        resp = client.post("/auth/token", data={
            "username": "test@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        resp = client.post("/auth/token", data={
            "username": "test@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client):
        resp = client.post("/auth/token", data={
            "username": "nobody@example.com",
            "password": "somepass",
        })
        assert resp.status_code == 401


class TestMe:
    def test_get_me_authenticated(self, client, auth_headers, test_user):
        resp = client.get("/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_get_me_unauthenticated(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_get_me_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401
