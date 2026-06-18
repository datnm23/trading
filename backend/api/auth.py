"""API key authentication for production endpoints."""

import os

from fastapi import Header, HTTPException
from fastapi.security import APIKeyHeader
from loguru import logger

_READ_KEY = os.environ.get("API_KEY", "")
_ADMIN_KEY = os.environ.get("ADMIN_KEY", "")

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def _check_keys_loaded():
    """Warn if keys not configured."""
    if not _READ_KEY:
        logger.warning("API_KEY not set — all read endpoints are UNPROTECTED")
    if not _ADMIN_KEY:
        logger.warning("ADMIN_KEY not set — admin endpoints are UNPROTECTED")


def verify_read_key(api_key: str | None = Header(None, alias="X-API-Key")):
    """Verify read-level API key."""
    if not _READ_KEY:
        return True  # Auth disabled if not configured
    if api_key != _READ_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return True


def verify_admin_key(
    api_key: str | None = Header(None, alias="X-API-Key"),
    admin_key: str | None = Header(None, alias="X-Admin-Key"),
):
    """Verify both read key AND admin key for sensitive operations."""
    verify_read_key(api_key)
    if not _ADMIN_KEY:
        return True
    if admin_key != _ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing admin key")
    return True


# Run check on import
_check_keys_loaded()
