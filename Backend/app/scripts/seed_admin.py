"""
One-time script to create the first Institute Admin account, attached to
the "Default Institute" (created automatically if needed).

Run from the Backend/ folder (with venv activated):
    python -m app.scripts.seed_admin

Change ADMIN_EMAIL / ADMIN_PASSWORD below before running if you want
different credentials, or just log in with these and change the
password later once a "change password" feature exists.

Teachers and students are invited from this admin's dashboard. Additional
institutes (each with their own admin) are created by the platform Super
Admin — see app/scripts/seed_super_admin.py.
"""

import asyncio
from datetime import datetime, timezone

from app.core.database import users_collection
from app.core.security import hash_password
from app.services.institutes import get_or_create_default_institute

ADMIN_EMAIL = "admin@coaching.com"
ADMIN_PASSWORD = "Admin@12345"
ADMIN_NAME = "Institute Admin"


async def seed_admin():
    institute = await get_or_create_default_institute()
    institute_id = str(institute["_id"])

    existing = await users_collection.find_one({"email": ADMIN_EMAIL})
    if existing:
        if not existing.get("institute_id"):
            # Account from before multi-tenancy: attach it to the default institute.
            await users_collection.update_one({"_id": existing["_id"]}, {"$set": {"institute_id": institute_id}})
            print(f"Existing account '{ADMIN_EMAIL}' attached to '{institute['name']}'.")
        else:
            print(f"An account with email '{ADMIN_EMAIL}' already exists. Nothing to do.")
        return

    await users_collection.insert_one(
        {
            "institute_id": institute_id,
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "password_hash": hash_password(ADMIN_PASSWORD),
            "role": "admin",
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
    )
    print("Admin account created successfully.")
    print(f"  Institute: {institute['name']}")
    print(f"  Email:     {ADMIN_EMAIL}")
    print(f"  Password:  {ADMIN_PASSWORD}")
    print("Log in at http://localhost:3000/login with these credentials.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
