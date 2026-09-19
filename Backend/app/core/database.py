from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = AsyncIOMotorClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

# Collection shortcuts (per PRD section 22: MongoDB Collections)
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
    """
    # users: email lookups (login/signup) and role-filtered listings
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("role")
    await users_collection.create_index("status")

    # courses: teacher-scoped listings, publish-status filtering
    await courses_collection.create_index("teacher_ids")
    await courses_collection.create_index("status")

    # modules: fetching a course's modules in order
    await modules_collection.create_index([("course_id", 1), ("order", 1)])

    # resources: fetching a module's resources
    await resources_collection.create_index("module_id")
    await resources_collection.create_index("course_id")

    # enrollments: the most frequently queried collection (course visibility
    # checks happen on nearly every student request) — unique pair, plus
    # each side indexed individually for reverse lookups.
    await enrollments_collection.create_index([("course_id", 1), ("student_id", 1)], unique=True)
    await enrollments_collection.create_index("student_id")

    # classes: role-scoped listings sorted by schedule
    await classes_collection.create_index("course_id")
    await classes_collection.create_index("teacher_id")
    await classes_collection.create_index("status")
    await classes_collection.create_index("scheduled_at")

    # doubts: role-scoped listings sorted by recency
    await doubts_collection.create_index("student_id")
    await doubts_collection.create_index("course_id")
    await doubts_collection.create_index("status")
    await doubts_collection.create_index("updated_at")

    # conversations: "my conversations" lookup
    await conversations_collection.create_index("participant_ids")

    # messages: paginated history for a conversation, oldest-to-newest
    await messages_collection.create_index([("conversation_id", 1), ("created_at", 1)])

    # notifications: "my notifications" sorted newest-first, unread filter
    await notifications_collection.create_index([("user_id", 1), ("created_at", -1)])
    await notifications_collection.create_index([("user_id", 1), ("read", 1)])
