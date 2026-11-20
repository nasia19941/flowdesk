def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "connected"


def test_register_creates_employee(client):
    response = client.post(
        "/auth/register",
        json={"email": "new@test.dev", "full_name": "New User", "password": "secret123"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["role"] == "employee"
    assert "hashed_password" not in body
    assert "password" not in body


def test_register_duplicate_email_returns_409(client, make_user):
    make_user("taken@test.dev")

    response = client.post(
        "/auth/register",
        json={"email": "taken@test.dev", "full_name": "Other", "password": "secret123"},
    )

    assert response.status_code == 409


def test_login_with_wrong_password_returns_401(client, make_user):
    make_user("user@test.dev")

    response = client.post(
        "/auth/login",
        data={"username": "user@test.dev", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_me_without_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_returns_current_user(client, make_user):
    headers = make_user("me@test.dev")

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["email"] == "me@test.dev"


def test_only_admin_can_list_users(client, users):
    assert client.get("/users", headers=users["employee"]).status_code == 403
    assert client.get("/users", headers=users["admin"]).status_code == 200