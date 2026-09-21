from datetime import datetime, timedelta, timezone

from app.core.database import invitations_collection
from tests.helpers import DEFAULT_PASSWORD, invite_and_accept


async def _invite(async_client, headers, email="new@test.com", role="student", name="New Person"):
    resp = await async_client.post("/api/invitations", json={"name": name, "email": email, "role": role}, headers=headers)
    return resp


async def test_admin_creates_invitation_and_gets_link_once(async_client, auth_headers):
    resp = await _invite(async_client, auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "pending"
    assert body["invite_token"] in body["invite_url"]
    assert "/accept-invite?token=" in body["invite_url"]

    # Listing never re-exposes the token.
    listing = await async_client.get("/api/invitations", headers=auth_headers)
    assert listing.status_code == 200
    assert "invite_token" not in listing.json()[0]
    assert "token_hash" not in listing.json()[0]


async def test_token_is_stored_hashed(async_client, auth_headers):
    resp = await _invite(async_client, auth_headers)
    stored = await invitations_collection.find_one({})
    assert stored["token_hash"] != resp.json()["invite_token"]
    assert "invite_token" not in stored


async def test_only_admin_can_invite(async_client, auth_headers):
    _, teacher_headers = await invite_and_accept(async_client, auth_headers, "t@test.com", "teacher")
    resp = await _invite(async_client, teacher_headers, email="x@test.com")
    assert resp.status_code == 403


async def test_admin_cannot_invite_another_admin(async_client, auth_headers):
    """Institute admins are created by the platform Super Admin, never by invitation from inside."""
    resp = await _invite(async_client, auth_headers, role="admin")
    assert resp.status_code == 422


async def test_cannot_invite_existing_account(async_client, auth_headers):
    await invite_and_accept(async_client, auth_headers, "taken@test.com", "student")
    resp = await _invite(async_client, auth_headers, email="taken@test.com")
    assert resp.status_code == 409


async def test_preview_shows_invitee_and_institute(async_client, auth_headers):
    token = (await _invite(async_client, auth_headers, email="peek@test.com", role="teacher", name="Pat Peek")).json()["invite_token"]
    resp = await async_client.get(f"/api/auth/invitations/{token}")
    assert resp.status_code == 200
    assert resp.json() == {
        "name": "Pat Peek", "email": "peek@test.com", "role": "teacher", "institute_name": "Test Institute",
    }


async def test_unknown_token_is_404(async_client):
    assert (await async_client.get("/api/auth/invitations/definitely-not-a-real-token")).status_code == 404
    resp = await async_client.post("/api/auth/accept-invite", json={"token": "definitely-not-a-real-token", "password": DEFAULT_PASSWORD})
    assert resp.status_code == 404


async def test_accept_creates_active_account_and_logs_in(async_client, auth_headers, institute):
    token = (await _invite(async_client, auth_headers, email="fresh@test.com", role="student", name="Fresh Face")).json()["invite_token"]
    resp = await async_client.post("/api/auth/accept-invite", json={"token": token, "password": DEFAULT_PASSWORD, "phone": "555-0100"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["role"] == "student"
    assert body["name"] == "Fresh Face"
    assert body["institute_id"] == str(institute["_id"])

    # The returned token works straight away — no separate approval step.
    me = await async_client.get("/api/courses", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200


async def test_invitee_can_correct_their_name(async_client, auth_headers):
    token = (await _invite(async_client, auth_headers, name="Jon Smyth")).json()["invite_token"]
    resp = await async_client.post("/api/auth/accept-invite", json={"token": token, "password": DEFAULT_PASSWORD, "name": "John Smith"})
    assert resp.json()["name"] == "John Smith"


async def test_link_is_single_use(async_client, auth_headers):
    token = (await _invite(async_client, auth_headers)).json()["invite_token"]
    first = await async_client.post("/api/auth/accept-invite", json={"token": token, "password": DEFAULT_PASSWORD})
    second = await async_client.post("/api/auth/accept-invite", json={"token": token, "password": "AnotherPass1"})
    assert first.status_code == 201
    assert second.status_code == 404


async def test_accept_rejects_short_password(async_client, auth_headers):
    token = (await _invite(async_client, auth_headers)).json()["invite_token"]
    resp = await async_client.post("/api/auth/accept-invite", json={"token": token, "password": "short1"})
    assert resp.status_code == 422


async def test_expired_invitation_is_rejected_with_410(async_client, auth_headers):
    token = (await _invite(async_client, auth_headers)).json()["invite_token"]
    await invitations_collection.update_one({}, {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(days=1)}})

    assert (await async_client.get(f"/api/auth/invitations/{token}")).status_code == 410
    resp = await async_client.post("/api/auth/accept-invite", json={"token": token, "password": DEFAULT_PASSWORD})
    assert resp.status_code == 410

    listing = await async_client.get("/api/invitations", headers=auth_headers)
    assert listing.json()[0]["status"] == "expired"


async def test_revoked_invitation_cannot_be_accepted(async_client, auth_headers):
    created = (await _invite(async_client, auth_headers)).json()
    revoke = await async_client.delete(f"/api/invitations/{created['id']}", headers=auth_headers)
    assert revoke.status_code == 204

    resp = await async_client.post("/api/auth/accept-invite", json={"token": created["invite_token"], "password": DEFAULT_PASSWORD})
    assert resp.status_code == 404
    assert (await async_client.get("/api/invitations", headers=auth_headers)).json()[0]["status"] == "revoked"


async def test_reinviting_same_email_invalidates_the_old_link(async_client, auth_headers):
    first = (await _invite(async_client, auth_headers, email="again@test.com")).json()
    second = (await _invite(async_client, auth_headers, email="again@test.com")).json()

    old = await async_client.post("/api/auth/accept-invite", json={"token": first["invite_token"], "password": DEFAULT_PASSWORD})
    new = await async_client.post("/api/auth/accept-invite", json={"token": second["invite_token"], "password": DEFAULT_PASSWORD})
    assert old.status_code == 404
    assert new.status_code == 201


async def test_regenerate_replaces_link_and_revives_expired_invitation(async_client, auth_headers):
    created = (await _invite(async_client, auth_headers)).json()
    await invitations_collection.update_one({}, {"$set": {"expires_at": datetime.now(timezone.utc) - timedelta(days=1)}})

    regen = await async_client.post(f"/api/invitations/{created['id']}/regenerate", headers=auth_headers)
    assert regen.status_code == 200
    assert regen.json()["status"] == "pending"
    assert regen.json()["invite_token"] != created["invite_token"]

    old = await async_client.post("/api/auth/accept-invite", json={"token": created["invite_token"], "password": DEFAULT_PASSWORD})
    new = await async_client.post("/api/auth/accept-invite", json={"token": regen.json()["invite_token"], "password": DEFAULT_PASSWORD})
    assert old.status_code == 404
    assert new.status_code == 201


async def test_cannot_regenerate_accepted_invitation(async_client, auth_headers):
    created = (await _invite(async_client, auth_headers)).json()
    await async_client.post("/api/auth/accept-invite", json={"token": created["invite_token"], "password": DEFAULT_PASSWORD})
    resp = await async_client.post(f"/api/invitations/{created['id']}/regenerate", headers=auth_headers)
    assert resp.status_code == 409


async def test_admin_is_notified_when_invitation_accepted(async_client, auth_headers):
    await invite_and_accept(async_client, auth_headers, "notify@test.com", "student", name="Nina Notify")
    notifications = await async_client.get("/api/notifications", headers=auth_headers)
    assert any(n["type"] == "invite_accepted" and "Nina Notify" in n["message"] for n in notifications.json())


async def test_invitation_lifecycle_is_audited(async_client, auth_headers):
    await invite_and_accept(async_client, auth_headers, "audited@test.com", "teacher")
    logs = await async_client.get("/api/audit-logs", headers=auth_headers)
    actions = {entry["action"] for entry in logs.json()}
    assert {"invitation.created", "invitation.accepted"} <= actions


async def test_only_admin_can_read_audit_logs(async_client, auth_headers):
    _, teacher_headers = await invite_and_accept(async_client, auth_headers, "snoop@test.com", "teacher")
    assert (await async_client.get("/api/audit-logs", headers=teacher_headers)).status_code == 403
