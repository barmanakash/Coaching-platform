async def test_signup_creates_pending_account(async_client):
    resp = await async_client.post("/api/auth/signup", json={
        "name": "Jane Student", "email": "jane@test.com", "password": "Password123", "role": "student",
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


async def test_login_blocked_while_pending(async_client):
    await async_client.post("/api/auth/signup", json={
        "name": "Jane Student", "email": "jane2@test.com", "password": "Password123", "role": "student",
    })
    resp = await async_client.post("/api/auth/login", json={"email": "jane2@test.com", "password": "Password123"})
    assert resp.status_code == 403
    assert "pending" in resp.json()["detail"].lower()


async def test_signup_rejects_short_password(async_client):
    resp = await async_client.post("/api/auth/signup", json={
        "name": "Jane Student", "email": "jane3@test.com", "password": "short1", "role": "student",
    })
    assert resp.status_code == 422


async def test_signup_rejects_admin_role(async_client):
    """Admin accounts must never be self-registerable."""
    resp = await async_client.post("/api/auth/signup", json={
        "name": "Sneaky", "email": "sneaky@test.com", "password": "Password123", "role": "admin",
    })
    assert resp.status_code == 422


async def test_login_wrong_credentials(async_client):
    resp = await async_client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "whatever1"})
    assert resp.status_code == 401


async def test_duplicate_signup_email_rejected(async_client):
    payload = {"name": "Dupe", "email": "dupe@test.com", "password": "Password123", "role": "student"}
    first = await async_client.post("/api/auth/signup", json=payload)
    second = await async_client.post("/api/auth/signup", json=payload)
    assert first.status_code == 201
    assert second.status_code == 409


async def test_approve_then_login_succeeds(async_client, auth_headers):
    await async_client.post("/api/auth/signup", json={
        "name": "Approved User", "email": "approved@test.com", "password": "Password123", "role": "teacher",
    })
    pending = await async_client.get("/api/users/pending", headers=auth_headers)
    user = next(u for u in pending.json() if u["email"] == "approved@test.com")

    await async_client.post(f"/api/users/{user['id']}/approve", headers=auth_headers)

    login = await async_client.post(
        "/api/auth/login", json={"email": "approved@test.com", "password": "Password123"}
    )
    assert login.status_code == 200
    assert login.json()["role"] == "teacher"
