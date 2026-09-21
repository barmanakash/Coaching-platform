"""
Tenant isolation helpers (PRD section 4).

Every institute-scoped query must include the caller's institute_id, and it
must come from the authenticated user (see security.authenticate_token) —
never from the request body or URL. Wrapping filters in `scoped()` makes
the rule hard to forget and easy to grep for in review.
"""


def scoped(current_user: dict, query: dict | None = None) -> dict:
    """Returns `query` with the caller's institute_id merged in.

    The institute_id is applied last, so a filter that (accidentally or
    maliciously) already contains an institute_id cannot override it.
    """
    return {**(query or {}), "institute_id": current_user["institute_id"]}
