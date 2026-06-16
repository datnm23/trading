"""DNSE OpenAPI v2 signed-request client (HMAC-SHA256 API Key signature).

Advisory market data (historical OHLCV) uses the PUBLIC chart-api and needs NO
key — see data/vn/dnse_source.py. This client is for AUTHENTICATED OpenAPI v2
endpoints (account info, authenticated/real-time market data) that DNSE protects
with the API Key + Signature scheme documented at:
    https://developers.dnse.com.vn/docs/guide/intro/authentication

Auth scheme (Layer 1):
  Headers per request: x-api-key, X-Signature, Date (RFC1123 GMT, ±1 min of
  server time), version. Signature = base64(HMAC-SHA256(signing_string, secret))
  then URL-encode + / = . Each request needs a fresh Date + nonce (uuid4 hex).

NOTE: Order placement (Layer 2) additionally requires an OTP-derived trading-token
— OUT of advisory scope, intentionally not implemented (YAGNI).

Credentials are read from env: DNSE_API_KEY / DNSE_API_SECRET (load via .env).

FINDINGS (2026-06-16, probing openapi.dnse.com.vn with the user's key):
- Host openapi.dnse.com.vn accepts `x-api-key` (401 "X-API-Key header required"
  when missing) and expects the signature in the `Authorization` header
  (400 "Authorization field missing, malformed or invalid"). Gateway = Kong (OA-* codes).
- The EXACT Authorization signature string was not matched after ~8 variants
  (Signature/hmac scheme, keyId/username, 2-vs-3 components, url-enc vs raw b64).
  → Needs DNSE's literal example from the developers.dnse.com.vn dashboard.
- ALTERNATIVE — V1 JWT (services.entrade.com.vn, what the community SDK uses):
  POST /dnse-user-service/api/auth {username, password} → token;
  then `Authorization: Bearer <token>`. Needs DNSE login (custody/phone + password),
  NOT the api-key. Endpoints: /dnse-order-service/accounts, /dnse-deal-service/deals, ...
- NOTE: advisory features need NEITHER — historical OHLCV is public (dnse_source.py).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import uuid
from email.utils import formatdate
from typing import Optional

import requests
from loguru import logger

# OpenAPI v2 REST base (confirmed: host accepts x-api-key + Authorization signature,
# returns OA-* errors / Kong gateway). Authenticated endpoints e.g. GET /accounts.
_BASE_URL = "https://openapi.dnse.com.vn"
_API_VERSION = "2026-05-07"


class DnseSignedClient:
    """Signed GET client for DNSE OpenAPI v2 authenticated endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = _BASE_URL,
        version: str = _API_VERSION,
        timeout: int = 15,
    ):
        self.api_key = api_key or os.environ.get("DNSE_API_KEY", "")
        self.api_secret = api_secret or os.environ.get("DNSE_API_SECRET", "")
        self.base_url = base_url.rstrip("/")
        self.version = version
        self.timeout = timeout

    # ------------------------------------------------------------------
    def _signature_headers(self, method: str, path: str) -> dict:
        """Build x-api-key / X-Signature / Date / version headers for one request."""
        date = formatdate(timeval=None, usegmt=True)  # RFC1123 GMT, e.g. 'Fri, 15 May 2026 07:11:30 GMT'
        nonce = uuid.uuid4().hex  # 32-char hex, no hyphens
        # Signing string: each line '\n'-joined, lowercase method/field names.
        signing_string = (
            f"(request-target): {method.lower()} {path}\n"
            f"date: {date}\n"
            f"nonce: {nonce}"
        )
        digest = hmac.new(
            self.api_secret.encode("utf-8"),
            signing_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        sig = base64.b64encode(digest).decode("ascii")
        sig = sig.replace("+", "%2B").replace("/", "%2F").replace("=", "%3D")
        x_signature = (
            f'Signature keyId="{self.api_key}",algorithm="hmac-sha256",'
            f'headers="(request-target) date nonce",signature="{sig}",nonce="{nonce}"'
        )
        return {
            "x-api-key": self.api_key,
            "X-Signature": x_signature,
            "Date": date,
            "version": self.version,
        }

    # ------------------------------------------------------------------
    def get(self, path: str, params: Optional[dict] = None) -> dict:
        """Signed GET against an OpenAPI v2 path (e.g. '/openapi/accounts')."""
        if not self.api_key or not self.api_secret:
            raise RuntimeError(
                "DNSE credentials missing — set DNSE_API_KEY and DNSE_API_SECRET in .env"
            )
        headers = self._signature_headers("GET", path)
        resp = requests.get(
            self.base_url + path, headers=headers, params=params, timeout=self.timeout
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    def verify_credentials(self, probe_path: str = "/openapi/accounts") -> bool:
        """Return True if a signed request succeeds (key + signature accepted)."""
        try:
            self.get(probe_path)
            logger.info("DNSE credentials OK (signed request accepted)")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error(f"DNSE credential check FAILED: {exc}")
            return False


if __name__ == "__main__":
    # Quick manual check once .env has DNSE_API_KEY / DNSE_API_SECRET.
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except Exception:
        pass
    client = DnseSignedClient()
    print("Credentials valid:" , client.verify_credentials())
