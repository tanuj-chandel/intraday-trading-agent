"""
Angel One SmartAPI — automated daily login (TOTP).

Why this exists:
  Angel One JWTs expire every day. Reading a static ANGELONE_JWT_TOKEN from .env
  means the feed silently dies the next morning. This module logs in fresh at
  session start using CLIENT_CODE + PIN + TOTP_SECRET and returns live tokens.

Read-only credentials use. No order placement anywhere in this module.

Requires: pyotp (pip install pyotp), httpx
"""
import os
import json
import datetime
from dataclasses import dataclass, asdict
from typing import Optional

import httpx
import pytz

from app.core.config import settings
from app.core.logging import logger

try:
    import pyotp
    _PYOTP_AVAILABLE = True
except ImportError:  # pragma: no cover
    _PYOTP_AVAILABLE = False

IST = pytz.timezone("Asia/Kolkata")
LOGIN_URL = "https://apiconnect.angelone.in/rest/auth/angelbroking/user/v1/loginByPassword"
PROFILE_URL = "https://apiconnect.angelone.in/rest/secure/angelbroking/user/v1/getProfile"
TOKEN_CACHE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "angel_tokens.json")


@dataclass
class AngelTokens:
    jwt_token: str
    refresh_token: str
    feed_token: str
    issued_date: str  # YYYY-MM-DD in IST

    def is_for_today(self) -> bool:
        return self.issued_date == datetime.datetime.now(tz=IST).strftime("%Y-%m-%d")


class AngelOneAuthError(RuntimeError):
    pass


class AngelOneAuth:
    """
    Performs a fresh SmartAPI login with TOTP and caches tokens for the day.
    Usage:
        tokens = AngelOneAuth().login()   # raises AngelOneAuthError on failure
    """

    def __init__(self):
        self.api_key = settings.ANGELONE_API_KEY or ""
        self.client_code = settings.ANGELONE_CLIENT_CODE or ""
        self.pin = settings.ANGELONE_PIN or ""
        self.totp_secret = settings.ANGELONE_TOTP_SECRET or ""

    @property
    def has_login_credentials(self) -> bool:
        placeholders = {"", "your_angelone_api_key_here", "your_client_code", "your_pin", "your_totp_secret"}
        return all(v not in placeholders for v in (self.api_key, self.client_code, self.pin, self.totp_secret))

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": self.api_key,
        }

    # ---- token cache -------------------------------------------------------

    def _load_cached(self) -> Optional[AngelTokens]:
        try:
            with open(TOKEN_CACHE_PATH, "r") as f:
                raw = json.load(f)
            # Support both the old file shape ({jwtToken,...}) and the new one.
            if "jwt_token" in raw:
                t = AngelTokens(**raw)
            else:
                t = AngelTokens(
                    jwt_token=raw.get("jwtToken", ""),
                    refresh_token=raw.get("refreshToken", ""),
                    feed_token=raw.get("feedToken", ""),
                    issued_date=raw.get("issued_date", "1970-01-01"),
                )
            return t if t.jwt_token else None
        except Exception:
            return None

    def _save_cached(self, tokens: AngelTokens) -> None:
        try:
            with open(TOKEN_CACHE_PATH, "w") as f:
                json.dump(asdict(tokens), f, indent=2)
        except Exception as exc:
            logger.warning(f"Could not persist Angel One tokens: {exc}")

    # ---- verification ------------------------------------------------------

    def verify(self, jwt_token: str) -> bool:
        """Cheap liveness check: /getProfile must return 200 with status=true."""
        try:
            headers = self._headers()
            headers["Authorization"] = f"Bearer {jwt_token}"
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(PROFILE_URL, headers=headers)
            if resp.status_code != 200:
                return False
            return bool(resp.json().get("status", False))
        except Exception:
            return False

    # ---- login -------------------------------------------------------------

    def login(self, force: bool = False) -> AngelTokens:
        """
        Returns valid tokens for today. Order of preference:
          1. Today's cached tokens, if /getProfile still accepts them.
          2. Fresh TOTP login.
        Raises AngelOneAuthError if neither works. Never falls back to a mock.
        """
        if not force:
            cached = self._load_cached()
            if cached and cached.is_for_today() and self.verify(cached.jwt_token):
                logger.info("Angel One: reusing today's cached session token (verified).")
                return cached

        if not self.has_login_credentials:
            raise AngelOneAuthError(
                "Angel One login credentials incomplete. Need ANGELONE_API_KEY, "
                "ANGELONE_CLIENT_CODE, ANGELONE_PIN, ANGELONE_TOTP_SECRET in .env"
            )
        if not _PYOTP_AVAILABLE:
            raise AngelOneAuthError("pyotp not installed. Run: pip install pyotp")

        totp = pyotp.TOTP(self.totp_secret).now()
        payload = {"clientcode": self.client_code, "password": self.pin, "totp": totp}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(LOGIN_URL, headers=self._headers(), json=payload)
        except Exception as exc:
            raise AngelOneAuthError(f"Angel One login request failed: {exc}") from exc

        if resp.status_code != 200:
            raise AngelOneAuthError(f"Angel One login HTTP {resp.status_code}: {resp.text[:200]}")

        body = resp.json()
        if not body.get("status") or not isinstance(body.get("data"), dict):
            raise AngelOneAuthError(f"Angel One login rejected: {body.get('message', 'unknown error')}")

        d = body["data"]
        tokens = AngelTokens(
            jwt_token=d.get("jwtToken", ""),
            refresh_token=d.get("refreshToken", ""),
            feed_token=d.get("feedToken", ""),
            issued_date=datetime.datetime.now(tz=IST).strftime("%Y-%m-%d"),
        )
        if not tokens.jwt_token:
            raise AngelOneAuthError("Angel One login returned no jwtToken.")

        self._save_cached(tokens)
        logger.info("Angel One: fresh TOTP login successful; tokens cached for today.")
        return tokens
