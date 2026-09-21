from tests.helpers import create_admin, create_institute, invite_and_accept


async def test_any_member_can_read_institute_profile(async_client, auth_headers):
    _, teacher_headers = await invite_and_accept(async_client, auth_headers, "t@test.com", "teacher")
    resp = await async_client.get("/api/institute", headers=teacher_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Test Institute"
    assert body["code"] == "test-institute"
    assert body["academic"]["grading"][0] == {"grade": "A+", "min_percent": 90.0}


async def test_admin_updates_profile_and_academic_config(async_client, auth_headers):
    resp = await async_client.patch("/api/institute", headers=auth_headers, json={
        "name": "Bright Future Academy",
        "address": "12 Main Road",
        "phone": "+91 99999 00000",
        "email": "hello@bright-academy.com",
        "website": "https://bright-academy.com",
        "description": "JEE and NEET coaching",
        "academic": {
            "academic_year": "2026-27",
            "subjects": ["Physics", "Chemistry", "Maths"],
            "classes": ["11", "12"],
            "departments": ["Science"],
            "grading": [{"grade": "Pass", "min_percent": 40}, {"grade": "Fail", "min_percent": 0}],
        },
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Bright Future Academy"
    assert body["academic"]["subjects"] == ["Physics", "Chemistry", "Maths"]

    # Persisted, and visible to the rest of the institute.
    _, student_headers = await invite_and_accept(async_client, auth_headers, "s@test.com", "student")
    seen = (await async_client.get("/api/institute", headers=student_headers)).json()
    assert seen["name"] == "Bright Future Academy"
    assert seen["academic"]["academic_year"] == "2026-27"
    assert [b["grade"] for b in seen["academic"]["grading"]] == ["Pass", "Fail"]


async def test_partial_update_leaves_other_fields_alone(async_client, auth_headers):
    await async_client.patch("/api/institute", json={"address": "Old Address", "phone": "123"}, headers=auth_headers)
    await async_client.patch("/api/institute", json={"phone": "456"}, headers=auth_headers)
    body = (await async_client.get("/api/institute", headers=auth_headers)).json()
    assert body["address"] == "Old Address"
    assert body["phone"] == "456"


async def test_fields_can_be_cleared_with_empty_strings(async_client, auth_headers):
    await async_client.patch("/api/institute", json={"website": "https://x.com", "email": "a@x.com"}, headers=auth_headers)
    resp = await async_client.patch("/api/institute", json={"website": "", "email": ""}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["website"] == ""
    assert resp.json()["email"] == ""


async def test_only_admin_can_update_institute(async_client, auth_headers):
    _, teacher_headers = await invite_and_accept(async_client, auth_headers, "t2@test.com", "teacher")
    resp = await async_client.patch("/api/institute", json={"name": "Nope"}, headers=teacher_headers)
    assert resp.status_code == 403


async def test_empty_update_is_rejected(async_client, auth_headers):
    assert (await async_client.patch("/api/institute", json={}, headers=auth_headers)).status_code == 400


async def test_unsafe_urls_are_rejected(async_client, auth_headers):
    bad_logo = await async_client.patch("/api/institute", json={"logo_url": "javascript:alert(1)"}, headers=auth_headers)
    bad_site = await async_client.patch("/api/institute", json={"website": "javascript:alert(1)"}, headers=auth_headers)
    assert bad_logo.status_code == 422
    assert bad_site.status_code == 422

    ok = await async_client.patch("/api/institute", json={"logo_url": "/media/abc/image/logo.png"}, headers=auth_headers)
    assert ok.status_code == 200


async def test_invalid_email_is_rejected(async_client, auth_headers):
    resp = await async_client.patch("/api/institute", json={"email": "not-an-email"}, headers=auth_headers)
    assert resp.status_code == 422


async def test_grading_scale_must_cover_zero_percent(async_client, auth_headers):
    resp = await async_client.patch(
        "/api/institute", json={"academic": {"grading": [{"grade": "A", "min_percent": 80}]}}, headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_grading_grades_must_be_unique(async_client, auth_headers):
    resp = await async_client.patch("/api/institute", json={"academic": {"grading": [
        {"grade": "A", "min_percent": 50}, {"grade": "a", "min_percent": 0},
    ]}}, headers=auth_headers)
    assert resp.status_code == 422


async def test_academic_lists_are_trimmed_and_deduplicated(async_client, auth_headers):
    resp = await async_client.patch("/api/institute", json={"academic": {
        "subjects": ["  Physics ", "physics", "", "Chemistry"],
    }}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["academic"]["subjects"] == ["Physics", "Chemistry"]


async def test_updating_one_institute_does_not_touch_another(async_client, auth_headers):
    other_id = await create_institute("Other Institute", "other-institute")
    other_admin = await create_admin(async_client, other_id, "other-admin@test.com")

    await async_client.patch("/api/institute", json={"name": "Renamed A"}, headers=auth_headers)

    other = (await async_client.get("/api/institute", headers=other_admin)).json()
    assert other["name"] == "Other Institute"
    assert other["id"] == other_id
