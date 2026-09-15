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
