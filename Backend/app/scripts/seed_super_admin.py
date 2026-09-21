"""
Creates the platform Super Admin (manages institutes; belongs to none).

Run from the Backend/ folder (with venv activated):
    python -m app.scripts.seed_super_admin --email you@example.com --name "Your Name"

The password is prompted for (hidden) unless SUPER_ADMIN_PASSWORD is set in
the environment. Credentials are deliberately not hard-coded here: this
account can create institutes and is far more sensitive than a normal admin.
"""

import argparse
import asyncio
import getpass
import os
from datetime import datetime, timezone

from app.core.database import users_collection
from app.core.security import SUPER_ADMIN_ROLE, hash_password


async def seed_super_admin(email: str, name: str, password: str) -> None:
    existing = await users_collection.find_one({"email": email})
    if existing:
        if existing["role"] == SUPER_ADMIN_ROLE:
            print(f"Super admin '{email}' already exists. Nothing to do.")
        else:
            print(f"An account with email '{email}' already exists with role '{existing['role']}'. Choose another email.")
        return

    await users_collection.insert_one({
        "institute_id": None,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": SUPER_ADMIN_ROLE,
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    })
    print(f"Super admin '{email}' created.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the platform Super Admin account.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Platform Admin")
    args = parser.parse_args()

    password = os.environ.get("SUPER_ADMIN_PASSWORD") or getpass.getpass("Password (min 8 characters): ")
    if len(password) < 8:
        raise SystemExit("Password must be at least 8 characters.")
    asyncio.run(seed_super_admin(args.email, args.name, password))
