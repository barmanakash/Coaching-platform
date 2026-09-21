from tests.helpers import DEFAULT_PASSWORD, invite_and_accept


async def test_public_signup_is_disabled(async_client):
    """Onboarding is admin-invite-only: there must be no self-service signup endpoint."""
    resp = await async_client.post("/api/auth/signup", json={
        "name": "Jane Student", "email": "jane@test.com", "password": "Password123", "role": "student",
    })
    assert resp.status_code in (404, 405)


async def test_login_wrong_credentials(async_client):
    resp = await async_client.post("/api/auth/login", json={"email": "nobody@test.com", "password": "whatever1"})
    assert resp.status_code == 401


async def test_login_returns_institute_details(async_client, auth_headers, institute):
    resp = await async_client.post("/api/auth/login", json={"email": "admin@test.com", "password": "TestAdmin123"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "admin"
    assert body["institute_id"] == str(institute["_id"])
    assert body["institute_name"] == "Test Institute"


async def test_invited_user_can_log_in(async_client, auth_headers, institute):
    await invite_and_accept(async_client, auth_headers, "invited@test.com", "teacher")

    login = await async_client.post(
        "/api/auth/login", json={"email": "invited@test.com", "password": DEFAULT_PASSWORD}
    )
    assert login.status_code == 200
    assert login.json()["role"] == "teacher"
    assert login.json()["institute_id"] == str(institute["_id"])


async def test_deactivated_user_is_locked_out_immediately(async_client, auth_headers):
    """A token must stop working the moment the admin deactivates the account,
    not when the token eventually expires."""
    teacher_id, teacher_headers = await invite_and_accept(async_client, auth_headers, "leaver@test.com", "teacher")
    assert (await async_client.get("/api/courses", headers=teacher_headers)).status_code == 200

    deactivate = await async_client.patch(
        f"/api/users/{teacher_id}", json={"status": "inactive"}, headers=auth_headers,
    )
    assert deactivate.status_code == 200

    assert (await async_client.get("/api/courses", headers=teacher_headers)).status_code == 401
    login = await async_client.post("/api/auth/login", json={"email": "leaver@test.com", "password": DEFAULT_PASSWORD})
    assert login.status_code == 403


async def test_deleted_user_token_stops_working(async_client, auth_headers):
    student_id, student_headers = await invite_and_accept(async_client, auth_headers, "gone@test.com", "student")
    await async_client.delete(f"/api/users/{student_id}", headers=auth_headers)
    assert (await async_client.get("/api/courses", headers=student_headers)).status_code == 401


async def test_admin_cannot_deactivate_or_delete_self(async_client, auth_headers):
    me = await async_client.post("/api/auth/login", json={"email": "admin@test.com", "password": "TestAdmin123"})
    my_id = me.json()["user_id"]

    deactivate = await async_client.patch(f"/api/users/{my_id}", json={"status": "inactive"}, headers=auth_headers)
    delete = await async_client.delete(f"/api/users/{my_id}", headers=auth_headers)
    assert deactivate.status_code == 400
    assert delete.status_code == 400


async def test_missing_or_garbage_token_rejected(async_client):
    assert (await async_client.get("/api/courses")).status_code == 401
    assert (await async_client.get("/api/courses", headers={"Authorization": "Bearer not-a-token"})).status_code == 401
