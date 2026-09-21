"""
Activity & audit log (PRD section 27).

Call `log_action` from any router after an important administrative
change. It never raises: a failure to write the audit entry is logged but
must not turn an otherwise successful request into an error.
"""

from datetime import datetime, timezone
from typing import Optional

from app.core.database import audit_logs_collection
from app.core.logging_config import logger


async def log_action(
    *,
    institute_id: Optional[str],
    actor_id: str,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    """`action` is a dotted verb like 'invitation.created' or 'institute.updated'."""
    try:
        await audit_logs_collection.insert_one({
            "institute_id": institute_id,
            "actor_id": actor_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "details": details or {},
            "created_at": datetime.now(timezone.utc),
        })
    except Exception:
        logger.exception(f"Failed to write audit log entry for action={action}")
