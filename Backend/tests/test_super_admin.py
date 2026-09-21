from tests.helpers import DEFAULT_PASSWORD, create_super_admin, invite_and_accept, login

NEW_INSTITUTE = {
    "name": "Sunrise Coaching",
    "code": "sunrise",
    "admin_name": "Sunita Rao",
    "admin_email": "sunita@sunrise.com",
}


async def test_super_admin_creates_institute_with_first_admin_invite(async_client):
    root = await create_super_admin(async_client)

    resp = await async_client.post("/api/super-admin/institutes", json=NEW_INSTITUTE, headers=root)
    assert resp.status_code == 201
    body = resp.json()
    assert body["institute"]["code"] == "sunrise"
    assert body["admin_invitation"]["role"] == "admin"
    assert body["admin_invitation"]["email"] == "sunita@sunrise.com"

    # The invited admin accepts, lands in the new institute, and can run it.
    accepted = await async_client.post(
        "/api/auth/accept-invite", json={"token": body["admin_invitation"]["invite_token"], "password": DEFAULT_PASSWORD},
    )
    assert accepted.status_code == 201
    assert accepted.json()["role"] == "admin"
    assert accepted.json()["institute_name"] == "Sunrise Coaching"

    admin = await login(async_client, "sunita@sunrise.com")
    assert (await async_client.get("/api/institute", headers=admin)).json()["name"] == "Sunrise Coaching"
    _, teacher_headers = await invite_and_accept(async_client, admin, "teacher@sunrise.com", "teacher")
    assert (await async_client.get("/api/courses", headers=teacher_headers)).json() == []


async def test_new_institute_starts_empty(async_client, auth_headers):
    """A brand-new institute must not inherit anyone else's people or courses."""
    await invite_and_accept(async_client, auth_headers, "existing-student@test.com", "student")
    await async_client.post("/api/courses", json={"title": "Old", "description": "", "teacher_ids": []}, headers=auth_headers)

    root = await create_super_admin(async_client)
    invite = (await async_client.post("/api/super-admin/institutes", json=NEW_INSTITUTE, headers=root)).json()["admin_invitation"]
    await async_client.post("/api/auth/accept-invite", json={"token": invite["invite_token"], "password": DEFAULT_PASSWORD})
    new_admin = await login(async_client, "sunita@sunrise.com")

    assert (await async_client.get("/api/users/students", headers=new_admin)).json() == []
    assert (await async_client.get("/api/courses", headers=new_admin)).json() == []
    assert (await async_client.get("/api/admin/dashboard", headers=new_admin)).json()["total_students"] == 0


async def test_list_institutes_shows_counts(async_client, auth_headers):
    await invite_and_accept(async_client, auth_headers, "s1@test.com", "student")
    await invite_and_accept(async_client, auth_headers, "t1@test.com", "teacher")
    root = await create_super_admin(async_client)

    resp = await async_client.get("/api/super-admin/institutes", headers=root)
    assert resp.status_code == 200
    institute = next(i for i in resp.json() if i["code"] == "test-institute")
    assert (institute["admin_count"], institute["teacher_count"], institute["student_count"]) == (1, 1, 1)


async def test_duplicate_code_and_existing_email_rejected(async_client, auth_headers):
    root = await create_super_admin(async_client)
    await async_client.post("/api/super-admin/institutes", json=NEW_INSTITUTE, headers=root)

    same_code = await async_client.post(
        "/api/super-admin/institutes", json={**NEW_INSTITUTE, "admin_email": "other@sunrise.com"}, headers=root,
    )
    assert same_code.status_code == 409

    taken_email = await async_client.post(
        "/api/super-admin/institutes", json={**NEW_INSTITUTE, "code": "another", "admin_email": "admin@test.com"}, headers=root,
    )
    assert taken_email.status_code == 409


async def test_institute_code_is_validated(async_client):
    root = await create_super_admin(async_client)
    for bad_code in ("Has Spaces", "-leading", "trailing-", "x", "under_score"):
        resp = await async_client.post("/api/super-admin/institutes", json={**NEW_INSTITUTE, "code": bad_code}, headers=root)
        assert resp.status_code == 422, bad_code


async def test_institute_code_is_normalised_to_lowercase(async_client):
    root = await create_super_admin(async_client)
    resp = await async_client.post("/api/super-admin/institutes", json={**NEW_INSTITUTE, "code": "  SunRise "}, headers=root)
    assert resp.status_code == 201
    assert resp.json()["institute"]["code"] == "sunrise"


async def test_institute_admins_cannot_use_super_admin_endpoints(async_client, auth_headers):
    assert (await async_client.get("/api/super-admin/institutes", headers=auth_headers)).status_code == 403
    assert (await async_client.post("/api/super-admin/institutes", json=NEW_INSTITUTE, headers=auth_headers)).status_code == 403


async def test_super_admin_cannot_use_institute_endpoints(async_client):
    root = await create_super_admin(async_client)
    for path in ("/api/courses", "/api/users/students", "/api/institute", "/api/admin/dashboard", "/api/invitations"):
        assert (await async_client.get(path, headers=root)).status_code == 403, path


async def test_super_admin_endpoints_require_authentication(async_client):
    assert (await async_client.get("/api/super-admin/institutes")).status_code == 401
