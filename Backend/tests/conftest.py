"""
Pytest fixtures shared by every test module.

IMPORTANT: this points the app at a separate 'coaching_platform_test'
database (same MongoDB server as dev) so tests never touch real data.
The env vars below MUST be set before `app.main` (and therefore
`app.core.config` / `app.core.database`) is imported anywhere.
"""

import os

os.environ["MONGO_DB_NAME"] = "coaching_platform_test"
os.environ["APP_ENV"] = "test"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-not-for-production"

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import db, users_collection, institutes_collection
from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.services.institutes import new_institute_doc

# Login / accept-invite are rate limited in production (brute-force
# protection). The suite signs in far more often than any real user would,
# so the limiter is switched off for tests.
limiter.enabled = False


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    """Wipes every collection in the test database before each test."""
    for name in await db.list_collection_names():
        await db[name].delete_many({})
    yield


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def institute():
    """The institute that `auth_headers`' admin belongs to."""
    doc = new_institute_doc("Test Institute", "test-institute")
    result = await institutes_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


@pytest_asyncio.fixture
async def auth_headers(async_client, institute):
    """A ready-to-use Institute Admin account + Authorization header."""
    await users_collection.insert_one({
        "institute_id": str(institute["_id"]),
        "name": "Test Admin",
        "email": "admin@test.com",
        "password_hash": hash_password("TestAdmin123"),
        "role": "admin",
        "status": "active",
    })
    resp = await async_client.post(
        "/api/auth/login", json={"email": "admin@test.com", "password": "TestAdmin123"}
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
