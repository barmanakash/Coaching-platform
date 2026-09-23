from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

# Collection shortcuts (per PRD section 30: MongoDB Collections)

# --- Platform-level (multi-tenant SaaS) ---
institutes_collection = db["institutes"]
invitations_collection = db["invitations"]
audit_logs_collection = db["audit_logs"]

# --- Tenant-scoped: every document below carries an `institute_id` ---
users_collection = db["users"]
courses_collection = db["courses"]
modules_collection = db["modules"]
resources_collection = db["resources"]
enrollments_collection = db["enrollments"]
classes_collection = db["classes"]
doubts_collection = db["doubts"]
conversations_collection = db["conversations"]
messages_collection = db["messages"]
notifications_collection = db["notifications"]
assignments_collection = db["assignments"]
submissions_collection = db["submissions"]
parent_links_collection = db["parent_links"]

# Collections whose documents belong to exactly one institute. Used by the
# migration script and by tests; add new tenant-scoped collections here.
TENANT_COLLECTIONS = {
    "users": users_collection,
    "courses": courses_collection,
    "modules": modules_collection,
    "resources": resources_collection,
    "enrollments": enrollments_collection,
    "classes": classes_collection,
    "doubts": doubts_collection,
    "conversations": conversations_collection,
    "messages": messages_collection,
    "notifications": notifications_collection,
    "assignments": assignments_collection,
    "submissions": submissions_collection,
    "parent_links": parent_links_collection,
}


async def ping_database() -> bool:
    """Simple health check used at startup / by /health endpoint."""
    try:
        await client.admin.command("ping")
        return True
    except Exception:
        return False


async def ensure_indexes() -> None:
    """
    Creates (or confirms) indexes on every hot query path (PRD section 32:
    Database indexes). Safe to run on every startup — create_index is a
    no-op if an equivalent index already exists.

    Tenant-scoped queries always filter on institute_id first, so it leads
    the compound indexes below.
    """
    # institutes: lookup by public code
    await institutes_collection.create_index("code", unique=True)

    # invitations: token lookup on accept, per-institute listings
    await invitations_collection.create_index("token_hash", unique=True)
    await invitations_collection.create_index([("institute_id", 1), ("created_at", -1)])
    await invitations_collection.create_index([("institute_id", 1), ("email", 1), ("status", 1)])

    # audit logs: newest-first per institute
    await audit_logs_collection.create_index([("institute_id", 1), ("created_at", -1)])

    # users: email is globally unique (login has no institute selector);
    # role-filtered listings are per institute
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index([("institute_id", 1), ("role", 1)])
    await users_collection.create_index("status")

    # courses: teacher-scoped listings, publish-status filtering
    await courses_collection.create_index([("institute_id", 1), ("status", 1)])
    await courses_collection.create_index("teacher_ids")

    # modules: fetching a course's modules in order
    await modules_collection.create_index([("course_id", 1), ("order", 1)])
    await modules_collection.create_index("institute_id")

    # resources: fetching a module's resources
    await resources_collection.create_index("module_id")
    await resources_collection.create_index("course_id")
    await resources_collection.create_index("institute_id")

    # enrollments: the most frequently queried collection (course visibility
    # checks happen on nearly every student request) — unique pair, plus
    # each side indexed individually for reverse lookups.
    await enrollments_collection.create_index([("course_id", 1), ("student_id", 1)], unique=True)
    await enrollments_collection.create_index("student_id")
    await enrollments_collection.create_index("institute_id")

    # classes: role-scoped listings sorted by schedule
    await classes_collection.create_index([("institute_id", 1), ("scheduled_at", 1)])
    await classes_collection.create_index("course_id")
    await classes_collection.create_index("teacher_id")
    await classes_collection.create_index("status")

    # doubts: role-scoped listings sorted by recency
    await doubts_collection.create_index([("institute_id", 1), ("updated_at", -1)])
    await doubts_collection.create_index("student_id")
    await doubts_collection.create_index("course_id")
    await doubts_collection.create_index("status")

    # conversations: "my conversations" lookup
    await conversations_collection.create_index("participant_ids")
    await conversations_collection.create_index("institute_id")

    # messages: paginated history for a conversation, oldest-to-newest
    await messages_collection.create_index([("conversation_id", 1), ("created_at", 1)])

    # notifications: "my notifications" sorted newest-first, unread filter
    await notifications_collection.create_index([("user_id", 1), ("created_at", -1)])
    await notifications_collection.create_index([("user_id", 1), ("read", 1)])

    # parent_links: a parent's list of children, and reverse lookup (which
    # parents a student has) — each pair may exist only once.
    await parent_links_collection.create_index([("parent_id", 1), ("student_id", 1)], unique=True)
    await parent_links_collection.create_index("student_id")
    await parent_links_collection.create_index("institute_id")
