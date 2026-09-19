"""
Shared rate limiter instance (PRD section 27/32: prevent brute-force abuse).
Lives in its own module so both main.py (registers it) and individual
routers (apply @limiter.limit(...) to specific endpoints) can import it
without a circular import.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
