"""
One-time script to create the first Admin account.

Run from the Backend/ folder (with venv activated):
    python -m app.scripts.seed_admin

Change ADMIN_EMAIL / ADMIN_PASSWORD below before running if you want
different credentials, or just log in with these and change the
password later once a "change password" feature exists.
"""

import asyncio
from datetime import datetime, timezone

from app.core.database import users_collection
from app.core.security import hash_password

ADMIN_EMAIL = "admin@coaching.com"
ADMIN_PASSWORD = "Admin@12345"
ADMIN_NAME = "Super Admin"


async def seed_admin():
    existing = await users_collection.find_one({"email": ADMIN_EMAIL})
    if existing:
        print(f"An account with email '{ADMIN_EMAIL}' already exists. Nothing to do.")
        return

    await users_collection.insert_one(
        {
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD),
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
    )
    print("Admin account created successfully.")
    print(f"  Email:    {ADMIN_EMAIL}")
    print(f"  Password: {ADMIN_PASSWORD}")
    print("Log in at http://localhost:3000/login with these credentials.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
