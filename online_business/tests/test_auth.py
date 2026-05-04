def test_register_buyer(client):
    r = client.post("/auth/register", json={
        "email": "alice@test.com", "username": "alice",
        "password": "securepass", "role": "buyer",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "alice@test.com"
    assert data["role"] == "buyer"
    assert "hashed_password" not in data


def test_register_seller(client):
    r = client.post("/auth/register", json={
        "email": "bob@test.com", "username": "bob",
        "password": "securepass", "role": "seller",
    })
    assert r.status_code == 201
    assert r.json()["role"] == "seller"


def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "username": "dup1", "password": "securepass", "role": "buyer"}
    client.post("/auth/register", json=payload)
    payload["username"] = "dup2"
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 409


def test_register_weak_password(client):
    r = client.post("/auth/register", json={
        "email": "weak@test.com", "username": "weakuser",
        "password": "short", "role": "buyer",
    })
    assert r.status_code == 422


def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@test.com", "username": "loginuser",
        "password": "securepass", "role": "buyer",
    })
    r = client.post("/auth/login", json={"email": "login@test.com", "password": "securepass"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "email": "wrong@test.com", "username": "wronguser",
        "password": "securepass", "role": "buyer",
    })
    r = client.post("/auth/login", json={"email": "wrong@test.com", "password": "badpass"})
    assert r.status_code == 401


def test_get_me(client, buyer):
    r = client.get("/users/me", headers={"Authorization": f"Bearer {buyer}"})
    assert r.status_code == 200
    assert r.json()["email"] == "buyer@test.com"


def test_get_me_unauthenticated(client):
    r = client.get("/users/me")
    assert r.status_code == 403
