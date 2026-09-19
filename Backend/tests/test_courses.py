from tests.helpers import signup_and_approve


async def test_only_admin_can_create_course(async_client, auth_headers):
    _, teacher_headers = await signup_and_approve(async_client, auth_headers, "t1@test.com", "teacher")
    resp = await async_client.post(
        "/api/courses", json={"title": "Algebra", "description": "", "teacher_ids": []}, headers=teacher_headers,
    )
    assert resp.status_code == 403


async def test_admin_can_create_and_assign_course(async_client, auth_headers):
    teacher_id, teacher_headers = await signup_and_approve(async_client, auth_headers, "t2@test.com", "teacher")

    resp = await async_client.post(
        "/api/courses",
        json={"title": "Algebra", "description": "", "teacher_ids": [teacher_id]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    course = resp.json()
    assert course["status"] == "draft"
    assert teacher_id in course["teacher_ids"]

    # Assigned teachers see their courses even while still in draft.
    resp = await async_client.get("/api/courses", headers=teacher_headers)
    assert any(c["id"] == course["id"] for c in resp.json())


async def test_unassigned_teacher_does_not_see_course(async_client, auth_headers):
    _, other_teacher_headers = await signup_and_approve(async_client, auth_headers, "t3@test.com", "teacher")
    await async_client.post(
        "/api/courses", json={"title": "History", "description": "", "teacher_ids": []}, headers=auth_headers,
    )

    resp = await async_client.get("/api/courses", headers=other_teacher_headers)
    assert resp.json() == []


async def test_student_cannot_see_published_course_without_enrollment(async_client, auth_headers):
    _, student_headers = await signup_and_approve(async_client, auth_headers, "s1@test.com", "student")

    course_resp = await async_client.post(
        "/api/courses", json={"title": "Biology", "description": "", "teacher_ids": []}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=auth_headers)

    resp = await async_client.get("/api/courses", headers=student_headers)
    assert resp.json() == []

    detail = await async_client.get(f"/api/courses/{course_id}", headers=student_headers)
    assert detail.status_code == 403


async def test_student_sees_course_after_enrollment(async_client, auth_headers):
    student_id, student_headers = await signup_and_approve(async_client, auth_headers, "s2@test.com", "student")

    course_resp = await async_client.post(
        "/api/courses", json={"title": "Chemistry", "description": "", "teacher_ids": []}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=auth_headers)

    enroll = await async_client.post(
        f"/api/courses/{course_id}/enrollments", json={"student_id": student_id}, headers=auth_headers,
    )
    assert enroll.status_code == 201

    resp = await async_client.get("/api/courses", headers=student_headers)
    assert any(c["id"] == course_id for c in resp.json())


async def test_student_loses_access_after_unenrollment(async_client, auth_headers):
    student_id, student_headers = await signup_and_approve(async_client, auth_headers, "s3@test.com", "student")

    course_resp = await async_client.post(
        "/api/courses", json={"title": "Geography", "description": "", "teacher_ids": []}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=auth_headers)
    await async_client.post(f"/api/courses/{course_id}/enrollments", json={"student_id": student_id}, headers=auth_headers)

    await async_client.delete(f"/api/courses/{course_id}/enrollments/{student_id}", headers=auth_headers)

    resp = await async_client.get("/api/courses", headers=student_headers)
    assert resp.json() == []


async def test_duplicate_enrollment_rejected(async_client, auth_headers):
    student_id, _ = await signup_and_approve(async_client, auth_headers, "s4@test.com", "student")
    course_resp = await async_client.post(
        "/api/courses", json={"title": "Art", "description": "", "teacher_ids": []}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]

    first = await async_client.post(f"/api/courses/{course_id}/enrollments", json={"student_id": student_id}, headers=auth_headers)
    second = await async_client.post(f"/api/courses/{course_id}/enrollments", json={"student_id": student_id}, headers=auth_headers)
    assert first.status_code == 201
    assert second.status_code == 409
