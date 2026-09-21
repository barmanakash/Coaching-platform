"""Small reusable input validators."""

import re

INSTITUTE_CODE_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$")


def validate_safe_url(value: str) -> str:
    """Only allow http(s) links or our own /media/ upload paths — blocks
    javascript:, data:, and other schemes that could be used for XSS."""
    if not (value.startswith("http://") or value.startswith("https://") or value.startswith("/media/")):
        raise ValueError("URL must start with http://, https://, or be an uploaded /media/ file")
    return value


def validate_institute_code(value: str) -> str:
    """Lowercase letters, digits and hyphens; 3-40 chars; no leading/trailing hyphen."""
    value = value.strip().lower()
    if not INSTITUTE_CODE_PATTERN.match(value):
        raise ValueError(
            "Institute code must be 3-40 characters: lowercase letters, numbers and hyphens only"
        )
    return value
