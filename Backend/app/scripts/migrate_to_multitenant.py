"""
One-time migration: Version 1.0 (single institute) -> Version 2.0 (multi-tenant).

Creates a "Default Institute" (if it doesn't exist yet) and stamps its id
onto every existing document that has no institute_id: users, courses,
modules, resources, enrollments, classes, doubts, conversations, messages,
notifications, assignments and submissions. Existing admins become the
Institute Admins of that institute. Then (re)creates indexes.

Safe to run more than once — documents that already have an institute_id
are left untouched.

Run from the Backend/ folder (with venv activated):

    python -m app.scripts.migrate_to_multitenant --dry-run   # just report what would change
    python -m app.scripts.migrate_to_multitenant             # do it

Back up your database first if it holds anything you care about
(e.g. `mongodump --db coaching_platform`).
"""

import argparse
import asyncio

from app.core.database import TENANT_COLLECTIONS, ensure_indexes, institutes_collection
from app.core.security import SUPER_ADMIN_ROLE
from app.services.institutes import DEFAULT_INSTITUTE_CODE, get_or_create_default_institute

MISSING_INSTITUTE = {"$or": [{"institute_id": {"$exists": False}}, {"institute_id": None}]}


def _query_for(collection_name: str) -> dict:
    if collection_name == "users":
        # Platform super admins intentionally belong to no institute.
        return {"$and": [MISSING_INSTITUTE, {"role": {"$ne": SUPER_ADMIN_ROLE}}]}
    return MISSING_INSTITUTE


async def migrate(dry_run: bool) -> None:
    if dry_run:
        existing = await institutes_collection.find_one({"code": DEFAULT_INSTITUTE_CODE})
        institute_id = str(existing["_id"]) if existing else "<to be created>"
        print(f"[dry run] Default institute: {'exists' if existing else 'would be created'} ({institute_id})")
    else:
        institute = await get_or_create_default_institute()
        institute_id = str(institute["_id"])
        print(f"Default institute ready: '{institute['name']}' (id={institute_id})")

    total = 0
    for name, collection in TENANT_COLLECTIONS.items():
        query = _query_for(name)
        if dry_run:
            count = await collection.count_documents(query)
        else:
            result = await collection.update_many(query, {"$set": {"institute_id": institute_id}})
            count = result.modified_count
        total += count
        print(f"  {name:<14} {count:>6} document(s) {'would be ' if dry_run else ''}assigned")

    if dry_run:
        print(f"[dry run] {total} document(s) would change. Nothing was written.")
        return

    await ensure_indexes()
    print(f"Done. {total} document(s) assigned; indexes ensured.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate single-institute data to the multi-tenant layout.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing anything")
    args = parser.parse_args()
    asyncio.run(migrate(args.dry_run))
