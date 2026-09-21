from app.core.database import institutes_collection, users_collection
from app.core.security import SUPER_ADMIN_ROLE, hash_password
from app.services.institutes import new_institute_doc

DEFAULT_PASSWORD = "Password123"


async def invite_and_accept(async_client, admin_headers, email: str, role: str, name: str = "Test User"):
    """Runs the real onboarding flow: the admin invites `email`, the invitee
    accepts the link and sets a password. Returns (user_id, auth_headers)
    ready to use in a test."""
    resp = await async_client.post(
        "/api/invitations", json={"name": name, "email": email, "role": role}, headers=admin_headers,
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["invite_token"]

    accepted = await async_client.post(
        "/api/auth/accept-invite", json={"token": token, "password": DEFAULT_PASSWORD},
    )
    assert accepted.status_code == 201, accepted.text
    data = accepted.json()
    return data["user_id"], {"Authorization": f"Bearer {data['access_token']}"}


# The existing test modules import this name from the days of public signup +
# admin approval; it now maps onto the invite flow with the same return value.
signup_and_approve = invite_and_accept


async def create_institute(name: str, code: str) -> str:
    """Inserts a second (or third...) institute directly; returns its id."""
    doc = new_institute_doc(name, code)
    result = await institutes_collection.insert_one(doc)
    return str(result.inserted_id)


async def create_admin(async_client, institute_id: str, email: str) -> dict:
    """Inserts an Institute Admin for `institute_id` and returns auth headers."""
    await users_collection.insert_one({
        "institute_id": institute_id,
        "name": f"Admin {email}",
        "email": email,
        "password_hash": hash_password(DEFAULT_PASSWORD),
        "role": "admin",
        "status": "active",
    })
    return await login(async_client, email)


async def create_super_admin(async_client, email: str = "root@platform.com") -> dict:
    await users_collection.insert_one({
        "institute_id": None,
        "name": "Platform Admin",
        "email": email,
        "password_hash": hash_password(DEFAULT_PASSWORD),
        "role": SUPER_ADMIN_ROLE,
        "status": "active",
    })
    return await login(async_client, email)


async def login(async_client, email: str, password: str = DEFAULT_PASSWORD) -> dict:
    resp = await async_client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
