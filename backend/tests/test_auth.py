def test_user_registration(client):
    payload = {
        "full_name": "Forensic Analyst Baker",
        "email": "baker@cybertrace.ai",
        "password": "SecurePassword123!",
        "role": "INVESTIGATOR"
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "baker@cybertrace.ai"
    assert "id" in data


def test_user_login_success(client, admin_user):
    payload = {
        "email": admin_user.email,
        "password": "Password123!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_user_login_invalid_password(client, admin_user):
    payload = {
        "email": admin_user.email,
        "password": "WrongPassword!"
    }
    response = client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


def test_unauthorized_access(client):
    response = client.get("/api/dashboard/overview")
    assert response.status_code == 401


def test_get_current_user_profile(client, auth_headers):
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test_admin@cybertrace.ai"
