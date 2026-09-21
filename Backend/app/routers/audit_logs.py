"""Read access to the institute's activity & audit log (PRD section 27). Writes go through services/audit.py."""

from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.database import audit_logs_collection, users_collection
from app.core.security import require_role
from app.core.tenant import scoped

router = APIRouter(prefix="/api/audit-logs", tags=["audit logs"])


class AuditLogOut(BaseModel):
    id: str
    actor_id: str
    actor_name: str
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[str] = None
    details: dict = {}
    created_at: datetime


@router.get("", response_model=list[AuditLogOut])
async def list_audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
    action: Optional[str] = Query(default=None, description="Filter by exact action, e.g. 'invitation.created'"),
    current_user: dict = Depends(require_role("admin")),
):
    query = scoped(current_user, {"action": action} if action else None)
    logs = await audit_logs_collection.find(query).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)

    actor_ids = {log["actor_id"] for log in logs if ObjectId.is_valid(log["actor_id"])}
    names: dict[str, str] = {}
    if actor_ids:
        cursor = users_collection.find({"_id": {"$in": [ObjectId(a) for a in actor_ids]}}, {"name": 1})
        names = {str(u["_id"]): u.get("name", "Unknown") async for u in cursor}

    return [
        AuditLogOut(
            id=str(log["_id"]),
            actor_id=log["actor_id"],
            actor_name=names.get(log["actor_id"], "Unknown"),
            action=log["action"],
            entity_type=log.get("entity_type"),
            entity_id=log.get("entity_id"),
            details=log.get("details", {}),
            created_at=log["created_at"],
        )
        for log in logs
    ]
