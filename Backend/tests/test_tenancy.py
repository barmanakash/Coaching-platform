"""
Tenant isolation (PRD section 4): one institute must never see or change
another institute's data, enforced by the backend regardless of what the
frontend shows.

Institute A is the default `institute` fixture (admin = `auth_headers`);
institute B is created here. Each has an admin, a teacher and a student.
"""

from types import SimpleNamespace

import pytest_asyncio

from app.core.security import create_access_token
from app.websocket.manager import ConnectionManager
from tests.helpers import create_admin, create_institute, invite_and_accept


@pytest_asyncio.fixture
async def tenants(async_client, auth_headers, institute):
    b_id = await create_institute("Other Institute", "other-institute")
    admin_b = await create_admin(async_client, b_id, "admin-b@test.com")

    teacher_a_id, teacher_a = await invite_and_accept(async_client, auth_headers, "teacher-a@test.com", "teacher")
    student_a_id, student_a = await invite_and_accept(async_client, auth_headers, "student-a@test.com", "student")
    teacher_b_id, teacher_b = await invite_and_accept(async_client, admin_b, "teacher-b@test.com", "teacher")
    student_b_id, student_b = await invite_and_accept(async_client, admin_b, "student-b@test.com", "student")

    return SimpleNamespace(
        a_id=str(institute["_id"]), b_id=b_id,
        admin_a=auth_headers, admin_b=admin_b,
        teacher_a_id=teacher_a_id, teacher_a=teacher_a,
        student_a_id=student_a_id, student_a=student_a,
        teacher_b_id=teacher_b_id, teacher_b=teacher_b,
        student_b_id=student_b_id, student_b=student_b,
    )


async def _make_course(async_client, headers, teacher_ids=(), title="Course", publish=False):
    resp = await async_client.post(
        "/api/courses", json={"title": title, "description": "", "teacher_ids": list(teacher_ids)}, headers=headers,
    )
    assert resp.status_code == 201, resp.text
    course_id = resp.json()["id"]
    if publish:
        await async_client.patch(f"/api/courses/{course_id}", json={"status": "published"}, headers=headers)
    return course_id


# ---------- People ----------

async def test_admin_user_lists_only_show_own_institute(async_client, tenants):
    a_students = await async_client.get("/api/users/students", headers=tenants.admin_a)
    a_teachers = await async_client.get("/api/users/teachers", headers=tenants.admin_a)
    b_students = await async_client.get("/api/users/students", headers=tenants.admin_b)
    b_teachers = await async_client.get("/api/users/teachers", headers=tenants.admin_b)

    assert {u["id"] for u in a_students.json()} == {tenants.student_a_id}
    assert {u["id"] for u in a_teachers.json()} == {tenants.teacher_a_id}
    assert {u["id"] for u in b_students.json()} == {tenants.student_b_id}
    assert {u["id"] for u in b_teachers.json()} == {tenants.teacher_b_id}


async def test_admin_cannot_modify_another_institutes_users(async_client, tenants):
    patch = await async_client.patch(f"/api/users/{tenants.student_a_id}", json={"name": "Hacked"}, headers=tenants.admin_b)
    delete = await async_client.delete(f"/api/users/{tenants.student_a_id}", headers=tenants.admin_b)
    assert patch.status_code == 404
    assert delete.status_code == 404

    survivors = await async_client.get("/api/users/students", headers=tenants.admin_a)
    assert [u["name"] for u in survivors.json()] == ["Test User"]


async def test_dashboard_counts_are_per_institute(async_client, tenants):
    await invite_and_accept(async_client, tenants.admin_a, "student-a2@test.com", "student")
    a = await async_client.get("/api/admin/dashboard", headers=tenants.admin_a)
    b = await async_client.get("/api/admin/dashboard", headers=tenants.admin_b)
    assert a.json()["total_students"] == 2
    assert b.json()["total_students"] == 1


# ---------- Courses & enrollment ----------

async def test_courses_are_invisible_and_immutable_across_institutes(async_client, tenants):
    course_id = await _make_course(async_client, tenants.admin_a, title="A's Course")

    assert (await async_client.get("/api/courses", headers=tenants.admin_b)).json() == []
    assert (await async_client.get(f"/api/courses/{course_id}", headers=tenants.admin_b)).status_code == 404
    patch = await async_client.patch(f"/api/courses/{course_id}", json={"title": "Stolen"}, headers=tenants.admin_b)
    assert patch.status_code == 404
    assert (await async_client.delete(f"/api/courses/{course_id}", headers=tenants.admin_b)).status_code == 404

    still_there = await async_client.get(f"/api/courses/{course_id}", headers=tenants.admin_a)
    assert still_there.json()["title"] == "A's Course"


async def test_cannot_assign_another_institutes_teacher_to_a_course(async_client, tenants):
    resp = await async_client.post(
        "/api/courses", json={"title": "X", "description": "", "teacher_ids": [tenants.teacher_a_id]}, headers=tenants.admin_b,
    )
    assert resp.status_code == 400

    course_id = await _make_course(async_client, tenants.admin_b, teacher_ids=[tenants.teacher_b_id])
    patch = await async_client.patch(
        f"/api/courses/{course_id}", json={"teacher_ids": [tenants.teacher_a_id]}, headers=tenants.admin_b,
    )
    assert patch.status_code == 400


async def test_cannot_enroll_across_institutes(async_client, tenants):
    course_a = await _make_course(async_client, tenants.admin_a)
    course_b = await _make_course(async_client, tenants.admin_b)

    # A's admin can't enroll B's student, and B's admin can't touch A's course.
    assert (await async_client.post(
        f"/api/courses/{course_a}/enrollments", json={"student_id": tenants.student_b_id}, headers=tenants.admin_a,
    )).status_code == 404
    assert (await async_client.post(
        f"/api/courses/{course_a}/enrollments", json={"student_id": tenants.student_b_id}, headers=tenants.admin_b,
    )).status_code == 404
    assert (await async_client.post(
        f"/api/courses/{course_b}/enrollments", json={"student_id": tenants.student_a_id}, headers=tenants.admin_b,
    )).status_code == 404
    assert (await async_client.get(f"/api/courses/{course_a}/enrollments", headers=tenants.admin_b)).status_code == 404


# ---------- Learning content ----------

async def test_modules_and_resources_are_isolated(async_client, tenants):
    course_a = await _make_course(async_client, tenants.admin_a, teacher_ids=[tenants.teacher_a_id])
    module = (await async_client.post(
        f"/api/courses/{course_a}/modules", json={"title": "Week 1", "description": "", "order": 0}, headers=tenants.teacher_a,
    )).json()

    assert (await async_client.get(f"/api/courses/{course_a}/modules", headers=tenants.admin_b)).status_code == 404
    assert (await async_client.get(f"/api/courses/{course_a}/modules", headers=tenants.teacher_b)).status_code == 404
    assert (await async_client.patch(
        f"/api/modules/{module['id']}", json={"title": "Hijacked"}, headers=tenants.admin_b,
    )).status_code == 404
    assert (await async_client.post(
        f"/api/modules/{module['id']}/resources",
        json={"title": "Bad", "description": "", "type": "link", "url": "https://example.com"},
        headers=tenants.admin_b,
    )).status_code == 404
    assert (await async_client.delete(f"/api/modules/{module['id']}", headers=tenants.admin_b)).status_code == 404


async def test_doubts_are_isolated(async_client, tenants):
    course_a = await _make_course(async_client, tenants.admin_a, teacher_ids=[tenants.teacher_a_id], publish=True)
    await async_client.post(
        f"/api/courses/{course_a}/enrollments", json={"student_id": tenants.student_a_id}, headers=tenants.admin_a,
    )
    doubt = (await async_client.post(
        "/api/doubts", json={"subject": "Q", "question": "Why?", "course_id": course_a}, headers=tenants.student_a,
    )).json()

    assert (await async_client.get("/api/doubts", headers=tenants.admin_b)).json() == []
    assert (await async_client.get("/api/doubts", headers=tenants.teacher_b)).json() == []
    assert (await async_client.get(f"/api/doubts/{doubt['id']}", headers=tenants.admin_b)).status_code == 404
    assert (await async_client.post(
        f"/api/doubts/{doubt['id']}/replies", json={"message": "hi"}, headers=tenants.admin_b,
    )).status_code == 404


async def test_a_student_cannot_raise_a_doubt_on_another_institutes_course(async_client, tenants):
    course_b = await _make_course(async_client, tenants.admin_b, publish=True)
    resp = await async_client.post(
        "/api/doubts", json={"subject": "Q", "question": "Why?", "course_id": course_b}, headers=tenants.student_a,
    )
    assert resp.status_code == 404


async def test_classes_are_isolated(async_client, tenants):
    course_a = await _make_course(async_client, tenants.admin_a, teacher_ids=[tenants.teacher_a_id])
    cls = (await async_client.post(
        "/api/classes",
        json={"course_id": course_a, "title": "Live", "description": "", "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=tenants.teacher_a,
    )).json()

    assert (await async_client.get("/api/classes", headers=tenants.admin_b)).json() == []
    assert (await async_client.get(f"/api/classes/{cls['id']}", headers=tenants.admin_b)).status_code == 404
    assert (await async_client.post(f"/api/classes/{cls['id']}/start", headers=tenants.admin_b)).status_code == 404
    assert (await async_client.delete(f"/api/classes/{cls['id']}", headers=tenants.admin_b)).status_code == 404

    # ...and B's admin can't schedule a class on A's course.
    resp = await async_client.post(
        "/api/classes",
        json={"course_id": course_a, "title": "Sneaky", "description": "", "scheduled_at": "2030-01-01T10:00:00Z"},
        headers=tenants.admin_b,
    )
    assert resp.status_code == 404


# ---------- Chat ----------

async def test_chat_contacts_only_include_own_institute(async_client, tenants):
    contacts = await async_client.get("/api/conversations/contacts", headers=tenants.student_a)
    assert [c["id"] for c in contacts.json()] == [tenants.teacher_a_id]


async def test_cannot_start_or_read_conversations_across_institutes(async_client, tenants):
    cross = await async_client.post("/api/conversations", json={"other_user_id": tenants.teacher_b_id}, headers=tenants.student_a)
    assert cross.status_code == 404

    own = await async_client.post("/api/conversations", json={"other_user_id": tenants.teacher_a_id}, headers=tenants.student_a)
    assert own.status_code == 201
    conv_id = own.json()["id"]

    assert (await async_client.get(f"/api/conversations/{conv_id}/messages", headers=tenants.teacher_b)).status_code == 403
    assert (await async_client.get("/api/conversations", headers=tenants.teacher_b)).json() == []


async def test_presence_never_crosses_institutes():
    class FakeSocket:
        def __init__(self):
            self.sent = []

        async def accept(self):
            pass

        async def send_json(self, message):
            self.sent.append(message)

    mgr = ConnectionManager()
    a1, a2, b1 = FakeSocket(), FakeSocket(), FakeSocket()
    await mgr.connect("user-a1", a1, "inst-a")
    await mgr.connect("user-a2", a2, "inst-a")
    await mgr.connect("user-b1", b1, "inst-b")

    assert set(mgr.online_user_ids("inst-a")) == {"user-a1", "user-a2"}
    assert mgr.online_user_ids("inst-b") == ["user-b1"]

    await mgr.broadcast_to_institute("inst-a", {"type": "presence"}, exclude_user_id="user-a1")
    assert a2.sent and not a1.sent and not b1.sent

    mgr.disconnect("user-a1", a1)
    assert "user-a1" not in mgr.online_user_ids("inst-a")


# ---------- Invitations & audit logs ----------

async def test_invitations_are_isolated(async_client, tenants):
    invite = (await async_client.post(
        "/api/invitations", json={"name": "Private Person", "email": "private@a.com", "role": "student"}, headers=tenants.admin_a,
    )).json()

    b_list = await async_client.get("/api/invitations", headers=tenants.admin_b)
    assert "private@a.com" not in str(b_list.json())
    assert (await async_client.delete(f"/api/invitations/{invite['id']}", headers=tenants.admin_b)).status_code == 404
    assert (await async_client.post(f"/api/invitations/{invite['id']}/regenerate", headers=tenants.admin_b)).status_code == 404

    # A's invitation is untouched and still usable.
    ok = await async_client.post("/api/auth/accept-invite", json={"token": invite["invite_token"], "password": "Password123"})
    assert ok.status_code == 201


async def test_invited_users_join_the_inviting_institute_only(async_client, tenants):
    assert (await async_client.get("/api/institute", headers=tenants.teacher_a)).json()["id"] == tenants.a_id
    assert (await async_client.get("/api/institute", headers=tenants.teacher_b)).json()["id"] == tenants.b_id


async def test_audit_logs_are_isolated(async_client, tenants):
    await async_client.post(
        "/api/invitations", json={"name": "Only In A", "email": "only-in-a@a.com", "role": "student"}, headers=tenants.admin_a,
    )
    a_logs = await async_client.get("/api/audit-logs", headers=tenants.admin_a)
    b_logs = await async_client.get("/api/audit-logs", headers=tenants.admin_b)
    assert "only-in-a@a.com" in str(a_logs.json())
    assert "only-in-a@a.com" not in str(b_logs.json())


# ---------- Token handling ----------

async def test_token_claims_are_not_trusted(async_client, tenants):
    """Role and institute come from the database, so a hand-made token claiming
    to be an admin of another institute gets nothing."""
    forged = create_access_token({"sub": tenants.teacher_a_id, "role": "admin", "institute_id": tenants.b_id})
    headers = {"Authorization": f"Bearer {forged}"}

    assert (await async_client.get("/api/users/students", headers=headers)).status_code == 403
    # The teacher's real institute is still A, whatever the token says.
    assert (await async_client.get("/api/institute", headers=headers)).json()["id"] == tenants.a_id
