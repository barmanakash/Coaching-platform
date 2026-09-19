from tests.helpers import signup_and_approve


async def test_student_cannot_raise_doubt_on_unenrolled_course(async_client, auth_headers):
    _, student_headers = await signup_and_approve(async_client, auth_headers, "sd1@test.com", "student")
    course_resp = await async_client.post(
        "/api/courses", json={"title": "Physics", "description": "", "teacher_ids": []}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]

    resp = await async_client.post(
        "/api/doubts",
        json={"subject": "Help", "question": "Why does this happen?", "course_id": course_id},
        headers=student_headers,
    )
    assert resp.status_code == 403


async def test_full_doubt_lifecycle(async_client, auth_headers):
    teacher_id, teacher_headers = await signup_and_approve(async_client, auth_headers, "sd_teacher@test.com", "teacher")
    student_id, student_headers = await signup_and_approve(async_client, auth_headers, "sd_student@test.com", "student")

    course_resp = await async_client.post(
        "/api/courses",
        json={"title": "Physics", "description": "", "teacher_ids": [teacher_id]},
        headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=auth_headers)
    await async_client.post(f"/api/courses/{course_id}/enrollments", json={"student_id": student_id}, headers=auth_headers)

    create_resp = await async_client.post(
        "/api/doubts",
        json={"subject": "Newton's laws", "question": "Why does F=ma?", "course_id": course_id},
        headers=student_headers,
    )
    assert create_resp.status_code == 201
    doubt = create_resp.json()
    assert doubt["status"] == "OPEN"

    # Teacher sees it in their scoped list.
    teacher_list = await async_client.get("/api/doubts", headers=teacher_headers)
    assert any(d["id"] == doubt["id"] for d in teacher_list.json())

    # Teacher's reply auto-flips status to IN_PROGRESS.
    reply_resp = await async_client.post(
        f"/api/doubts/{doubt['id']}/replies", json={"message": "Because of inertia."}, headers=teacher_headers,
    )
    assert reply_resp.status_code == 200
    assert reply_resp.json()["status"] == "IN_PROGRESS"
    assert len(reply_resp.json()["replies"]) == 1

    # Student can mark it resolved.
    resolve_resp = await async_client.patch(
        f"/api/doubts/{doubt['id']}/status", json={"status": "RESOLVED"}, headers=student_headers,
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"


async def test_unrelated_teacher_cannot_view_doubt(async_client, auth_headers):
    teacher_id, _ = await signup_and_approve(async_client, auth_headers, "dt_owner@test.com", "teacher")
    _, other_teacher_headers = await signup_and_approve(async_client, auth_headers, "dt_other@test.com", "teacher")
    student_id, student_headers = await signup_and_approve(async_client, auth_headers, "dt_student@test.com", "student")

    course_resp = await async_client.post(
        "/api/courses", json={"title": "Math", "description": "", "teacher_ids": [teacher_id]}, headers=auth_headers,
    )
    course_id = course_resp.json()["id"]
    await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=auth_headers)
    await async_client.post(f"/api/courses/{course_id}/enrollments", json={"student_id": student_id}, headers=auth_headers)

    doubt_resp = await async_client.post(
        "/api/doubts", json={"subject": "Q", "question": "Q?", "course_id": course_id}, headers=student_headers,
    )
    doubt_id = doubt_resp.json()["id"]

    resp = await async_client.get(f"/api/doubts/{doubt_id}", headers=other_teacher_headers)
    assert resp.status_code == 403
