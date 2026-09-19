from tests.helpers import signup_and_approve


async def test_teacher_can_add_module_and_resource_to_own_course(async_client, auth_headers):
    teacher_id, teacher_headers = await signup_and_approve(async_client, auth_headers, "m1@test.com", "teacher")
    course_resp = await async_client.post(
        "/api/courses", json={"title": "Course A", "description": "", "teacher_ids": [teacher_id]}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]

    module_resp = await async_client.post(
        f"/api/courses/{course_id}/modules", json={"title": "Week 1", "description": "", "order": 0}, headers=teacher_headers,
    )
    assert module_resp.status_code == 201
    module_id = module_resp.json()["id"]

    resource_resp = await async_client.post(
        f"/api/modules/{module_id}/resources",
        json={"title": "Slides", "description": "", "type": "link", "url": "https://example.com/slides"},
        headers=teacher_headers,
    )
    assert resource_resp.status_code == 201


async def test_teacher_cannot_add_module_to_unassigned_course(async_client, auth_headers):
    _, teacher_headers = await signup_and_approve(async_client, auth_headers, "m2@test.com", "teacher")
    course_resp = await async_client.post(
        "/api/courses", json={"title": "Course B", "description": "", "teacher_ids": []}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]

    resp = await async_client.post(
        f"/api/courses/{course_id}/modules", json={"title": "Week 1", "description": "", "order": 0}, headers=teacher_headers,
    )
    assert resp.status_code == 403


async def test_resource_url_rejects_unsafe_scheme(async_client, auth_headers):
    """Guards the XSS fix: only http(s) or our own /media/ paths are allowed."""
    teacher_id, teacher_headers = await signup_and_approve(async_client, auth_headers, "m3@test.com", "teacher")
    course_resp = await async_client.post(
        "/api/courses", json={"title": "Course C", "description": "", "teacher_ids": [teacher_id]}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    module_resp = await async_client.post(
        f"/api/courses/{course_id}/modules", json={"title": "Week 1", "description": "", "order": 0}, headers=teacher_headers,
    )
    module_id = module_resp.json()["id"]

    resp = await async_client.post(
        f"/api/modules/{module_id}/resources",
        json={"title": "Bad", "description": "", "type": "link", "url": "javascript:alert(1)"},
        headers=teacher_headers,
    )
    assert resp.status_code == 422


async def test_student_without_enrollment_cannot_view_modules(async_client, auth_headers):
    teacher_id, teacher_headers = await signup_and_approve(async_client, auth_headers, "m4@test.com", "teacher")
    _, student_headers = await signup_and_approve(async_client, auth_headers, "m4s@test.com", "student")

    course_resp = await async_client.post(
        "/api/courses", json={"title": "Course D", "description": "", "teacher_ids": [teacher_id]}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=auth_headers)
    await async_client.post(
        f"/api/courses/{course_id}/modules", json={"title": "Week 1", "description": "", "order": 0}, headers=teacher_headers,
    )

    resp = await async_client.get(f"/api/courses/{course_id}/modules", headers=student_headers)
    assert resp.status_code == 403
