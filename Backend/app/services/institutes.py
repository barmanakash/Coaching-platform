from datetime import datetime, timezone

from app.core.database import institutes_collection

DEFAULT_INSTITUTE_CODE = "default"
DEFAULT_INSTITUTE_NAME = "Default Institute"

DEFAULT_GRADING = [
    {"grade": "A+", "min_percent": 90},
    {"grade": "A", "min_percent": 80},
    {"grade": "B", "min_percent": 70},
    {"grade": "C", "min_percent": 60},
    {"grade": "D", "min_percent": 50},
    {"grade": "F", "min_percent": 0},
]


def new_institute_doc(name: str, code: str) -> dict:
    """Shape of a freshly created institute (PRD section 6: profile + academic configuration)."""
    return {
        "name": name,
        "code": code,
        "logo_url": "",
        "address": "",
        "phone": "",
        "email": "",
        "website": "",
        "description": "",
        "academic": {
            "academic_year": "",
            "subjects": [],
            "classes": [],
            "departments": [],
            "grading": [dict(band) for band in DEFAULT_GRADING],
        },
        # Reserved for the Phase 7 subscription system (trial/active/suspended).
        "status": "active",
        "created_at": datetime.now(timezone.utc),
    }


async def get_or_create_default_institute() -> dict:
    """The institute that pre-multi-tenancy (Version 1.0) data is migrated into."""
    existing = await institutes_collection.find_one({"code": DEFAULT_INSTITUTE_CODE})
    if existing:
        return existing
    doc = new_institute_doc(DEFAULT_INSTITUTE_NAME, DEFAULT_INSTITUTE_CODE)
    result = await institutes_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc
