from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import DuplicateKeyError

from app.core.database import users_collection, institutes_collection, invitations_collection
from app.core.security import hash_password, verify_password, create_access_token, SUPER_ADMIN_ROLE
from app.core.rate_limit import limiter
from app.core.logging_config import logger
from app.services.audit import log_action
from app.services.invitations import hash_invite_token, invitation_status
from app.services.notifications import create_notification

router = APIRouter(prefix="/api/auth", tags=["auth"])

INVALID_INVITE_MESSAGE = "This invitation link is invalid or has already been used"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: str
    name: str
    institute_id: Optional[str] = None
    institute_name: Optional[str] = None


class InvitationPreview(BaseModel):
    name: str
    email: EmailStr
    role: str
    institute_name: str


class AcceptInviteRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: str = Field(min_length=8, max_length=72)
    # The admin's spelling of the name is the default; the invitee may correct it.
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)


async def _institute_name(institute_id: Optional[str]) -> Optional[str]:
    if not institute_id:
        return None
    institute = await institutes_collection.find_one({"_id": ObjectId(institute_id)}, {"name": 1})
    return institute["name"] if institute else None


def _token_response(user: dict, institute_name: Optional[str]) -> TokenResponse:
    institute_id = user.get("institute_id")
    token = create_access_token({
        "sub": str(user["_id"]),
        "role": user["role"],
        "institute_id": institute_id,
    })
    return TokenResponse(
        access_token=token,
        role=user["role"],
        user_id=str(user["_id"]),
        name=user.get("name", ""),
        institute_id=institute_id,
        institute_name=institute_name,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, payload: LoginRequest):
    user = await users_collection.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["password_hash"]):
        logger.warning(f"Failed login attempt for email={payload.email} from {request.client.host}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    account_status = user.get("status", "active")
    if account_status == "pending":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is pending admin approval. You'll be able to log in once an admin verifies you.",
        )
    if account_status == "inactive":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    if user["role"] != SUPER_ADMIN_ROLE and not user.get("institute_id"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not linked to an institute. Please contact your administrator.",
        )

    return _token_response(user, await _institute_name(user.get("institute_id")))


# ---------- Invitations (admin-invite-only onboarding) ----------
# There is no public signup. Accounts are created only by accepting an
# invitation issued by an Institute Admin (teachers/students) or by the
# platform Super Admin (an institute's first admin). See routers/invitations.py.

async def _load_pending_invitation(token: str) -> dict:
    invitation = await invitations_collection.find_one({"token_hash": hash_invite_token(token)})
    # Unknown, already-used and revoked links all look identical on purpose.
    if not invitation or invitation.get("status") != "pending":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVALID_INVITE_MESSAGE)
    if invitation_status(invitation) == "expired":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This invitation has expired. Ask your institute admin to send a new one.",
        )
    return invitation


@router.get("/invitations/{token}", response_model=InvitationPreview)
@limiter.limit("30/minute")
async def preview_invitation(request: Request, token: str):
    """Lets the accept-invite page greet the invitee and show which institute they're joining."""
    invitation = await _load_pending_invitation(token)
    return InvitationPreview(
        name=invitation["name"],
        email=invitation["email"],
        role=invitation["role"],
        institute_name=await _institute_name(invitation["institute_id"]) or "your institute",
    )


@router.post("/accept-invite", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def accept_invite(request: Request, payload: AcceptInviteRequest):
    invitation = await _load_pending_invitation(payload.token)

    if await users_collection.find_one({"email": invitation["email"]}, {"_id": 1}):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")

    # Claim the invitation atomically so one link can never create two accounts.
    now = datetime.now(timezone.utc)
    claimed = await invitations_collection.find_one_and_update(
        {"_id": invitation["_id"], "status": "pending"},
        {"$set": {"status": "accepted", "accepted_at": now}},
    )
    if not claimed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=INVALID_INVITE_MESSAGE)

    institute_id = invitation["institute_id"]
    new_user = {
        "institute_id": institute_id,
        "name": payload.name or invitation["name"],
        "email": invitation["email"],
        "password_hash": hash_password(payload.password),
        "role": invitation["role"],
        "phone": payload.phone,
        # Invited accounts are trusted (an admin vouched for them), so they
        # are active immediately — no separate approval step.
        "status": "active",
        "invited_by": invitation.get("invited_by"),
        "created_at": now,
    }
    try:
        result = await users_collection.insert_one(new_user)
    except DuplicateKeyError:
        # Lost a race on the unique email index: give the invitation back.
        await invitations_collection.update_one(
            {"_id": invitation["_id"]}, {"$set": {"status": "pending"}, "$unset": {"accepted_at": ""}},
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists")
    new_user["_id"] = result.inserted_id

    await log_action(
        institute_id=institute_id,
        actor_id=str(result.inserted_id),
        action="invitation.accepted",
        entity_type="invitation",
        entity_id=str(invitation["_id"]),
        details={"email": invitation["email"], "role": invitation["role"]},
    )

    if invitation["role"] != "admin":
        admins = await users_collection.find({"role": "admin", "institute_id": institute_id}).to_list(length=100)
        for admin in admins:
            await create_notification(
                user_id=str(admin["_id"]),
                type="invite_accepted",
                title="Invitation accepted",
                message=f"{new_user['name']} joined as a {invitation['role']}",
                link="/admin/invitations",
                institute_id=institute_id,
            )

    return _token_response(new_user, await _institute_name(institute_id))
