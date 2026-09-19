DEFAULT_PASSWORD = "Password123"


async def signup_and_approve(async_client, admin_headers, email: str, role: str, name: str = "Test User"):
    """Signs a user up, approves them as admin, logs them in, and returns
    (user_id, auth_headers) ready to use in a test."""
    await async_client.post("/api/auth/signup", json={
        "name": name, "email": email, "password": DEFAULT_PASSWORD, "role": role,
    })

    pending = await async_client.get("/api/users/pending", headers=admin_headers)
    user = next(u for u in pending.json() if u["email"] == email)
    await async_client.post(f"/api/users/{user['id']}/approve", headers=admin_headers)

    login = await async_client.post("/api/auth/login", json={"email": email, "password": DEFAULT_PASSWORD})
    token = login.json()["access_token"]
    return user["id"], {"Authorization": f"Bearer {token}"}
